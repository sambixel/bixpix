# scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
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

    dob_str = "Dec 04, 1991"
    dob = datetime.strptime(dob_str, "%b %d, %Y")  # Parse the string

    today = datetime.today()
    age = (today - dob).days // 365

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
    fighter1["avgFightTime"] = float(f1avgTime.split(':')[0]) * 60 + float(f1avgTime.split(':')[1])
    fighter2["avgFightTime"] = float(f2avgTime.split(':')[0]) * 60 + float(f2avgTime.split(':')[1])

    f1height = fight_data[7].get_text(strip=True)
    f2height = fight_data[8].get_text(strip=True)
    fighter1["height"] = float(f1height[0]) * 12 + float(f1height[3:f2height.find('\"')])
    fighter2["height"] = float(f2height[0]) * 12 + float(f2height[3:f2height.find('\"')])

    fighter1["weight"] = int(fight_data[10].get_text(strip=True)[:3])
    fighter2["weight"] = int(fight_data[11].get_text(strip=True)[:3])

    fighter1["reach"] = float(fight_data[13].get_text(strip=True).replace('"', ''))
    fighter1["reach"] = float(fight_data[14].get_text(strip=True).replace('"', ''))

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

    # 5 Most recent fight outcomes

    try:
        fighter1["1"] = fight_data[45].get_text(strip=True)
        fighter1["2"] = fight_data[47].get_text(strip=True)
        fighter1["3"] = fight_data[49].get_text(strip=True)
        fighter1["4"] = fight_data[51].get_text(strip=True)
        fighter1["5"] = fight_data[53].get_text(strip=True)
        fighter1["retrieveFights"] = "Success"
    except:
        fighter1["retrieveFights"] = "Fail"

    try:
        fighter2["1"] = fight_data[46].get_text(strip=True)
        fighter2["2"] = fight_data[48].get_text(strip=True)
        fighter2["3"] = fight_data[50].get_text(strip=True)
        fighter2["4"] = fight_data[52].get_text(strip=True)
        fighter2["5"] = fight_data[54].get_text(strip=True)
        fighter2["retrieveFights"] = "Success"
    except:
        fighter2["retrieveFights"] = "Fail"
    
    return fighter1, fighter2


