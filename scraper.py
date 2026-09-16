# scraper.py
import os, re, unicodedata
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import joblib
import numpy as np
from bixpix_core import fetch

# -----------------------
# Config 
# -----------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

ODDS_API_BASE = "https://api.the-odds-api.com/v4"
SPORT_KEY = "mma_mixed_martial_arts"                 
BOOKS = ["draftkings", "fanduel", "betmgm"]

# Your trained model
model = joblib.load("bixpix_xgb_model.pkl")

BASE_FEATS = [
    "height", "weight", "reach", "age",
    "SLpM", "strikeAccuracy", "SApM", "defense",
    "TDavg", "TDacc", "TDdef", "SubAvg"
]

# -----------------------
# Helpers
# -----------------------
_name_cleaner = re.compile(r"[^a-z0-9 ]+")

def normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    s = s.lower().strip()
    s = _name_cleaner.sub("", s)
    # Drop spaces entirely: books and UFCStats disagree on spacing
    # (e.g. "Saint Denis" vs "Saintdenis"), which broke odds joins.
    s = re.sub(r"\s+", "", s)
    return s

def pair_key(n1: str, n2: str) -> tuple[str, str]:
    a, b = sorted([normalize_name(n1), normalize_name(n2)])
    return (a, b)

def american_to_implied(odds: int | float | None) -> float | None:
    if odds is None:
        return None
    a = float(odds)
    return 100.0 / (a + 100.0) if a > 0 else (-a) / ((-a) + 100.0)

def profit_per_dollar(odds: int | float | None) -> float | None:
    if odds is None:
        return None
    a = float(odds)
    return (a / 100.0) if a > 0 else (100.0 / (-a))

def expected_value(prob: float, odds: int | float | None) -> float | None:
    """EV per $1 staked: win prob * profit_per_dollar - lose prob. >0 means +EV."""
    b = profit_per_dollar(odds)
    if b is None:
        return None
    return prob * b - (1.0 - prob)

def _build_feature_vector(f1: dict, f2: dict) -> list[float]:
    return [float(f1[feat]) - float(f2[feat]) for feat in BASE_FEATS]

# -----------------------
# Scraper
# -----------------------
def get_fight_links(event_url: str) -> list[str]:
    res = fetch(event_url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")
    fight_links = []
    rows = soup.find_all('tr', class_='b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click')
    for row in rows:
        link = row.get("data-link")
        if link:
            fight_links.append(link)
    return fight_links

def get_fight_stats(fight_url: str):
    res = fetch(fight_url)
    res.raise_for_status()
    soup = BeautifulSoup(res.text, "html.parser")

    fighter1 = {}
    fighter2 = {}

    fighterNames = soup.select(".b-fight-details__table-header-link")
    fighter1["name"] = fighterNames[0].get_text(strip=True)
    fighter2["name"] = fighterNames[1].get_text(strip=True)

    fight_data = soup.select(".b-fight-details__table-text")

    f1rec = fight_data[1].get_text(strip=True)
    f2rec = fight_data[2].get_text(strip=True)
    if "NC" in f1rec: f1rec = f1rec[:-6]
    if "NC" in f2rec: f2rec = f2rec[:-6]
    f1w, f1l, f1d = map(int, f1rec.split('-'))
    f2w, f2l, f2d = map(int, f2rec.split('-'))
    fighter1["wins"], fighter1["losses"], fighter1["draws"] = f1w, f1l, f1d
    fighter2["wins"], fighter2["losses"], fighter2["draws"] = f2w, f2l, f2d

    f1avgTime = fight_data[4].get_text(strip=True)
    f2avgTime = fight_data[5].get_text(strip=True)
    fighter1["avgFightTime"] = float(f1avgTime.split(':')[0]) * 60 + float(f1avgTime.split(':')[1]) if f1avgTime else 0.0
    fighter2["avgFightTime"] = float(f2avgTime.split(':')[0]) * 60 + float(f2avgTime.split(':')[1]) if f2avgTime else 0.0

    f1height = fight_data[7].get_text(strip=True)
    f2height = fight_data[8].get_text(strip=True)
    if '-' not in f1height:
        fighter1["height"] = float(f1height[0]) * 12 + float(f1height[3:f1height.find('\"')])
    if '-' not in f2height:
        fighter2["height"] = float(f2height[0]) * 12 + float(f2height[3:f2height.find('\"')])

    w1 = fight_data[10].get_text(strip=True)
    w2 = fight_data[11].get_text(strip=True)
    if '--' not in w1: fighter1["weight"] = int(w1[:3])
    if '--' not in w2: fighter2["weight"] = int(w2[:3])

    r1 = fight_data[13].get_text(strip=True)
    r2 = fight_data[14].get_text(strip=True)
    if '--' not in r1: fighter1["reach"] = float(r1.replace('"', ''))
    if '--' not in r2: fighter2["reach"] = float(r2.replace('"', ''))

    fighter1["stance"] = fight_data[16].get_text(strip=True)
    fighter2["stance"] = fight_data[17].get_text(strip=True)

    dob = datetime.strptime(fight_data[19].get_text(strip=True), "%b %d, %Y")
    today = datetime.today()
    fighter1["age"] = (today - dob).days // 365
    dob = datetime.strptime(fight_data[20].get_text(strip=True), "%b %d, %Y")
    fighter2["age"] = (today - dob).days // 365

    fighter1["SLpM"] = float(fight_data[22].get_text(strip=True))
    fighter2["SLpM"] = float(fight_data[23].get_text(strip=True))
    fighter1["strikeAccuracy"] = float(fight_data[25].get_text(strip=True).strip('%')) / 100.0
    fighter2["strikeAccuracy"] = float(fight_data[26].get_text(strip=True).strip('%')) / 100.0
    fighter1["SApM"] = float(fight_data[28].get_text(strip=True))
    fighter2["SApM"] = float(fight_data[29].get_text(strip=True))
    fighter1["defense"] = float(fight_data[31].get_text(strip=True).strip('%')) / 100.0
    fighter2["defense"] = float(fight_data[32].get_text(strip=True).strip('%')) / 100.0
    fighter1["TDavg"] = float(fight_data[34].get_text(strip=True))
    fighter2["TDavg"] = float(fight_data[35].get_text(strip=True))
    fighter1["TDacc"] = float(fight_data[37].get_text(strip=True).strip('%')) / 100.0
    fighter2["TDacc"] = float(fight_data[38].get_text(strip=True).strip('%')) / 100.0
    fighter1["TDdef"] = float(fight_data[40].get_text(strip=True).strip('%')) / 100.0
    fighter2["TDdef"] = float(fight_data[41].get_text(strip=True).strip('%')) / 100.0
    fighter1["SubAvg"] = float(fight_data[43].get_text(strip=True))
    fighter2["SubAvg"] = float(fight_data[44].get_text(strip=True))

    return fighter1, fighter2

# -----------------------
# Odds fetch
# -----------------------
def fetch_odds_index() -> dict:
    """
    Returns:
      {
        (normA, normB): {
           normA: {"best_odds": +150, "book": "DraftKings", "implied": 0.4},
           normB: {"best_odds": -170, "book": "FanDuel",    "implied": 0.6296}
        },
        ...
      }
    """
    # Read lazily so it works regardless of when load_dotenv() runs.
    api_key = os.getenv("THE_ODDS_API_KEY", "")
    if not api_key:
        print("[odds] THE_ODDS_API_KEY not set — no odds/EV, picks fall back to confidence order")
        return {}

    try:
        url = f"{ODDS_API_BASE}/sports/{SPORT_KEY}/odds"
        params = {
            "apiKey": api_key,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "american",
            "bookmakers": ",".join(BOOKS),
            "dateFormat": "iso",
        }
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"[odds] fetch failed: {e}")
        return {}

    wanted = set(BOOKS)
    idx: dict[tuple[str, str], dict] = {}

    for ev in data:
        for bm in ev.get("bookmakers", []):
            bm_key = (bm.get("key") or "").lower()
            if bm_key not in wanted:
                continue
            book_title = bm.get("title") or bm_key

            for mkt in bm.get("markets", []):
                if mkt.get("key") != "h2h":
                    continue
                outcomes = [o for o in mkt.get("outcomes", []) if (o.get("name") or "").lower() not in {"draw", "tie"}]
                if len(outcomes) < 2:
                    continue

                a, b = outcomes[0], outcomes[1]
                n1 = normalize_name(a.get("name", ""))
                n2 = normalize_name(b.get("name", ""))
                if not n1 or not n2:
                    continue

                try:
                    p1 = int(a.get("price"))
                    p2 = int(b.get("price"))
                except Exception:
                    continue

                k = pair_key(n1, n2)
                entry = idx.setdefault(k, {})

                ppd1 = profit_per_dollar(p1)
                if (n1 not in entry) or (profit_per_dollar(entry[n1]["best_odds"]) < ppd1):
                    entry[n1] = {"best_odds": p1, "book": book_title, "implied": american_to_implied(p1)}

                ppd2 = profit_per_dollar(p2)
                if (n2 not in entry) or (profit_per_dollar(entry[n2]["best_odds"]) < ppd2):
                    entry[n2] = {"best_odds": p2, "book": book_title, "implied": american_to_implied(p2)}

    return idx

# -----------------------
# Predictions + confidence
# -----------------------
def get_predictions(event_url: str):
    fight_links = get_fight_links(event_url)
    fights = []
    # Fights we can't parse are counted, not dropped silently. On a live card
    # this is the normal case: once a fight finishes, UFCStats swaps its
    # matchup-preview page for a results page with a different layout.
    skipped = 0
    for link in fight_links:
        try:
            f1, f2 = get_fight_stats(link)
            if all(k in f1 for k in BASE_FEATS) and all(k in f2 for k in BASE_FEATS):
                fights.append((f1, f2))
            else:
                skipped += 1
        except Exception as e:
            skipped += 1
            print(f"[get_predictions] skipped {link}: {e}")

    if not fights:
        return {"status": "success", "cardURL": event_url,
                "predictions": [], "skipped": skipped}

    X = np.array([_build_feature_vector(f1, f2) for f1, f2 in fights], dtype=float)
    proba = model.predict_proba(X)[:, 1].tolist()  

    odds_idx = fetch_odds_index()

    results = []
    for (f1, f2), p in zip(fights, proba):
        p1 = float(p)            # model prob fighter1 wins
        p2 = 1.0 - p1            # model prob fighter2 wins
        n1 = normalize_name(f1["name"])
        n2 = normalize_name(f2["name"])
        k = pair_key(n1, n2)

        line_info = odds_idx.get(k)
        o1 = line_info.get(n1) if line_info else None
        o2 = line_info.get(n2) if line_info else None

        # Predict the winner from the model alone. Odds only evaluate the
        # price of that pick; they must never switch it to the other fighter.
        fighter, prob, odd = (f1, p1, o1) if p1 >= 0.5 else (f2, p2, o2)
        odds = int(odd["best_odds"]) if odd else None
        implied = american_to_implied(odds)
        ev = expected_value(prob, odds)
        edge = prob - implied if implied is not None else None
        # Use full precision for classification, rather than the rounded EV
        # sent to the UI. An exact model tie is not a winner/value pick.
        is_value = prob > 0.5 and ev is not None and ev > 0.0
        value_status = (
            "no_pick" if prob == 0.5 else
            "unavailable" if ev is None else
            "value" if is_value else "no_value"
        )

        results.append({
            "fighter1": f1["name"],
            "fighter2": f2["name"],
            "pick": fighter["name"] if prob > 0.5 else None,
            "confidence": round(prob, 3),
            "odds": odds if prob > 0.5 else None,
            "book": str(odd["book"]) if odd and prob > 0.5 else None,
            "ev": round(ev, 3) if ev is not None and prob > 0.5 else None,
            "edge": round(edge, 3) if edge is not None and prob > 0.5 else None,
            "isValue": is_value,
            "valueStatus": value_status,
        })

    # Show the strongest winner predictions first, independent of prices.
    results.sort(key=lambda r: r["confidence"], reverse=True)

    return {"status": "success", "cardURL": event_url,
            "predictions": results, "skipped": skipped}
