# scraper.py
import requests
from bs4 import BeautifulSoup

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

    fighter1 = {}
    fighter2 = {}

    # "." In front of the class so soup knows to search for a class, not an HTML tag.
    fighterNames = soup.select(".b-fight-details__table-header-link")
    
    fighter1["name"] = fighterNames[0].get_text(strip=True)
    fighter2["name"] = fighterNames[1].get_text(strip=True)

    fight_data = soup.select(".b-fight-details__table-text")
    
    fighter1["WinLoss"] = fight_data[1].get_text(strip=True)
    fighter2["WinLoss"] = fight_data[2].get_text(strip=True)

    fighter1["avgFightTime"] = fight_data[4].get_text(strip=True)
    fighter2["avgFightTime"] = fight_data[5].get_text(strip=True)

    fighter1["height"] = fight_data[7].get_text(strip=True)
    fighter2["height"] = fight_data[8].get_text(strip=True)

    fighter1["weight"] = fight_data[10].get_text(strip=True)
    fighter2["weight"] = fight_data[11].get_text(strip=True)

    fighter1["reach"] = fight_data[13].get_text(strip=True)
    fighter2["reach"] = fight_data[14].get_text(strip=True)

    fighter1["stance"] = fight_data[16].get_text(strip=True)
    fighter2["stance"] = fight_data[17].get_text(strip=True)

    fighter1["DOB"] = fight_data[19].get_text(strip=True)
    fighter2["DOB"] = fight_data[20].get_text(strip=True)

    fighter1["SLpM"] = fight_data[22].get_text(strip=True)
    fighter2["SLpM"] = fight_data[23].get_text(strip=True)

    fighter1["strikeAccuracy"] = fight_data[25].get_text(strip=True)
    fighter2["strikeAccuracy"] = fight_data[26].get_text(strip=True)

    fighter1["SApM"] = fight_data[28].get_text(strip=True)
    fighter2["SApM"] = fight_data[29].get_text(strip=True)

    fighter1["defense"] = fight_data[31].get_text(strip=True)
    fighter2["defense"] = fight_data[32].get_text(strip=True)


    fighter1["TDavg"] = fight_data[34].get_text(strip=True)
    fighter2["TDavg"] = fight_data[35].get_text(strip=True)

    fighter1["TDacc"] = fight_data[37].get_text(strip=True)
    fighter2["TDacc"] = fight_data[38].get_text(strip=True)

    fighter1["TDdef"] = fight_data[40].get_text(strip=True)
    fighter2["TDdef"] = fight_data[41].get_text(strip=True)

    fighter1["SubAvg"] = fight_data[43].get_text(strip=True)
    fighter2["SubAvg"] = fight_data[44].get_text(strip=True)

    # 5 Most recent fight outcomes

    try:
        fighter1["1"] = fight_data[45].get_text(strip=True)
        fighter1["2"] = fight_data[47].get_text(strip=True)
        fighter1["3"] = fight_data[49].get_text(strip=True)
        fighter1["4"] = fight_data[51].get_text(strip=True)
        fighter1["5"] = fight_data[53].get_text(strip=True)
    except:
        fighter1["5fights"] = "Fail"

    try:
        fighter2["1"] = fight_data[46].get_text(strip=True)
        fighter2["2"] = fight_data[48].get_text(strip=True)
        fighter2["3"] = fight_data[50].get_text(strip=True)
        fighter2["4"] = fight_data[52].get_text(strip=True)
        fighter2["5"] = fight_data[54].get_text(strip=True)
    except:
        fighter2["5fights"] = "Fail"
    
    return fighter1, fighter2


