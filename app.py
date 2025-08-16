from flask import Flask, request, jsonify
from bixpix_core import get_events, next_card
from scraper import get_fight_links, get_fight_stats, get_predictions as get_predictions_ev

app = Flask(__name__, static_folder="web", static_url_path="")

# Static pages
@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/favicon.ico")
def favicon_ico():
    return app.send_static_file("favicon.ico")

@app.route("/event.html")
def event_page():
    return app.send_static_file("event.html")

# APIs
@app.get("/api/events")
def api_events():
    """
    Normalize to what the UI expects: [{cardName, cardURL, date}]
    """
    events = get_events()  # [{name, url, date}]
    out = [
        {"cardName": e["name"], "cardURL": e["url"], "date": e.get("date", "Unknown")}
        for e in events
    ]
    return jsonify({"status": "success", "events": out})

@app.route("/api/getNext", methods=['GET', 'POST'])
def api_get_next():
    nxt = next_card()  # {name, url}
    payload = get_predictions_ev(nxt["url"])
    payload["cardName"] = nxt["name"]      
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
    payload = get_predictions_ev(url)  
    return jsonify(payload)

if __name__ == "__main__":
    app.run(debug=True)
