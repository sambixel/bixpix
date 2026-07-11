import os
import time
from flask import Flask, request, jsonify
from dotenv import load_dotenv
load_dotenv()  # must run before importing scraper, which reads THE_ODDS_API_KEY

import db
from bixpix_core import get_events
from scraper import get_fight_links, get_fight_stats, get_predictions as get_predictions_ev

app = Flask(__name__, static_folder="web", static_url_path="")

# Scraping a card + model inference + odds API takes ~1 min, so results are
# cached in SQLite and recomputed only when stale. Odds drift and live cards
# lose fights over time, so keep the predictions TTL short-ish.
EVENTS_TTL = int(os.getenv("EVENTS_TTL_SECONDS", "900"))          # 15 min
PREDICTIONS_TTL = int(os.getenv("PREDICTIONS_TTL_SECONDS", "1800"))  # 30 min


def _events_cached(force: bool = False) -> list[dict]:
    out = None if force else db.get("events", EVENTS_TTL)
    if out is None:
        events = get_events()  # [{name, url, date}]
        out = [
            {"cardName": e["name"], "cardURL": e["url"], "date": e.get("date", "Unknown")}
            for e in events
        ]
        db.set("events", out)
    return out


def _predictions_cached(card_url: str, force: bool = False) -> dict:
    key = f"predictions:{card_url}"
    payload = None if force else db.get(key, PREDICTIONS_TTL)
    if payload is None:
        payload = get_predictions_ev(card_url)
        payload["fetchedAt"] = time.time()
        db.set(key, payload)
    return payload


def _want_refresh() -> bool:
    return request.args.get("refresh") == "1"

# Static pages
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/favicon.ico")
def favicon_ico():
    return app.send_static_file("favicon.ico")

# APIs
@app.get("/api/events")
def api_events():
    """
    Normalize to what the UI expects: [{cardName, cardURL, date}]
    """
    out = _events_cached(force=_want_refresh())
    return jsonify({"status": "success", "events": out})

@app.route("/api/getNext", methods=['GET', 'POST'])
def api_get_next():
    events = _events_cached()
    if not events:
        return jsonify({"status": "error", "message": "no upcoming events found"}), 502
    nxt = events[0]
    payload = _predictions_cached(nxt["cardURL"], force=_want_refresh())
    payload["cardName"] = nxt["cardName"]
    return jsonify(payload)

@app.post("/api/getFighter")
def api_get_fighters():
    data = request.get_json(force=True)
    url = data.get("cardURL")
    if not url:
        return jsonify({"status": "error", "message": "cardURL required"}), 400

    links = get_fight_links(url)
    all_fight_data = []
    for link in links:
        try:
            fight_data = get_fight_stats(link)
            if fight_data:
                f1, f2 = fight_data
                all_fight_data.append({"fighter1": f1, "fighter2": f2})
        except Exception as e:
            print(f"[getFighter] skipped {link}: {e}")

    return jsonify({"status": "success", "fights": all_fight_data})

@app.post("/api/predictions")
def api_predictions():
    """
    Accepts either JSON body {cardURL} or query param ?url=
    Returns the EV/odds-aware schema.
    """
    data = request.get_json(force=True) if request.data else {}
    url = data.get("cardURL") or request.args.get("url")
    if not url:
        return jsonify({"status": "error", "message": "cardURL (or ?url=) required"}), 400
    payload = _predictions_cached(url, force=_want_refresh())
    return jsonify(payload)

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)