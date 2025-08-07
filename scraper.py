# scraper.py
from flask import jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import joblib
import numpy as np


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}
model = joblib.load("bixpix_xgb_model.pkl")

BASE_FEATS = [
    "height", "weight", "reach", "age",
    "SLpM", "strikeAccuracy", "SApM", "defense",
    "TDavg", "TDacc", "TDdef", "SubAvg"
]

def _build_feature_vector(f1: dict, f2: dict) -> list[float]:
    """
    Return the 12-dim vector (f1 – f2) in the exact order the model expects.
    """
    return [f1[feat] - f2[feat] for feat in BASE_FEATS]

def get_predictions(event_url):
    fight_links = get_fight_links(event_url)

    fights = []
    # Scrape every fight on the card
    for link in fight_links:
        try:
            f1, f2 = get_fight_stats(link)
            fights.append((f1, f2))
        except Exception as e:
            print(f"[get_predictions] skipped {link}: {e}")

    # Build feature matrix & run model
    X= np.array([_build_feature_vector(f1, f2) for f1, f2 in fights])
    proba = model.predict_proba(X)[:, 1].tolist()  

    # Assemble results
    results = []
    for (f1, f2), p in zip(fights, proba):
        conf = round(p if p > 0.5 else 1 - p, 3)
        results.append({
            "fighter1":   f1["name"],
            "fighter2":   f2["name"],
            "prediction": f"{f1['name']} wins" if p > 0.5 else f"{f2['name']} wins",
            "confidence": conf
        })

    # Sort by confidence descending
    results.sort(key=lambda r: r["confidence"], reverse=True)

    return {
        "status":      "success",
        "cardURL":     event_url,
        "predictions": results
    }




def get_fight_links(event_url):
    res = requests.get(event_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    fight_links = []
    rows = soup.find_all('tr', class_='b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click')
    for row in rows:
        link = row.get("data-link")
        if link:
            fight_links.append(link)
    return fight_links

def get_fight_stats(fight_url):
    res = requests.get(fight_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    fighter1 = {}
    fighter2 = {}

    # "." In front of the class so soup knows to search for a class, not an HTML tag.
    fighterNames = soup.select(".b-fight-details__table-header-link")
    
    fighter1["name"] = fighterNames[0].get_text(strip=True)
    fighter2["name"] = fighterNames[1].get_text(strip=True)

    fight_data = soup.select(".b-fight-details__table-text")
    
    f1rec = fight_data[1].get_text(strip=True)
    f2rec = fight_data[2].get_text(strip=True)
    if "NC" in f1rec:
        f1rec = f1rec[:-6]
    if "NC" in f2rec:
        f2rec = f2rec[:-6]
    f1w, f1l, f1d = map(int, f1rec.split('-'))
    f2w, f2l, f2d = map(int, f2rec.split('-'))
    fighter1["wins"] = f1w
    fighter1["losses"] = f1l
    fighter1["draws"] = f1d
    fighter2["wins"] = f2w
    fighter2["losses"] = f2l
    fighter2["draws"] = f2d

    f1avgTime = fight_data[4].get_text(strip=True)
    f2avgTime = fight_data[5].get_text(strip=True)
    if f1avgTime != '':
        fighter1["avgFightTime"] = float(f1avgTime.split(':')[0]) * 60 + float(f1avgTime.split(':')[1])    
    else:
        fighter2["avgFightTime"] = 0
    if f2avgTime != '':
        fighter2["avgFightTime"] = float(f2avgTime.split(':')[0]) * 60 + float(f2avgTime.split(':')[1])
    else:
        fighter2["avgFightTime"] = 0

    f1height = fight_data[7].get_text(strip=True)
    f2height = fight_data[8].get_text(strip=True)
    if '-' not in f1height:
        fighter1["height"] = float(f1height[0]) * 12 + float(f1height[3:f1height.find('\"')])    
    if '-' not in f2height:
        fighter2["height"] = float(f2height[0]) * 12 + float(f2height[3:f2height.find('\"')])

    if '--' not in fight_data[10]:
        fighter1["weight"] = int(fight_data[10].get_text(strip=True)[:3])
    if '--' not in fight_data[11]:
        fighter2["weight"] = int(fight_data[11].get_text(strip=True)[:3])

    if '--' not in fight_data[13]:
        fighter1["reach"] = float(fight_data[13].get_text(strip=True).replace('"', ''))
    if '--' not in fight_data[14]:
        fighter2["reach"] = float(fight_data[14].get_text(strip=True).replace('"', ''))

    fighter1["stance"] = fight_data[16].get_text(strip=True)
    fighter2["stance"] = fight_data[17].get_text(strip=True)

    fighter1["DOB"] = fight_data[19].get_text(strip=True)
    fighter2["DOB"] = fight_data[20].get_text(strip=True)
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


