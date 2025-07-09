# scraper.py
import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}

def get_fight_links_from_event(event_url):
    res = requests.get(event_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    fight_links = []
    rows = soup.select("tr.b-fight-details__table-row")
    for row in rows:
        link = row.get("data-link")
        if link:
            fight_links.append(link)
    return fight_links

def parse_fight_stats(fight_url):
    res = requests.get(fight_url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    try:
        names = soup.select('h3.b-fight-details__person-name span')
        fighter_A = names[0].text.strip()
        fighter_B = names[1].text.strip()

        winner_boxes = soup.select("div.b-fight-details__person")
        winner = None
        if 'Win' in winner_boxes[0].text:
            winner = 'A'
        elif 'Win' in winner_boxes[1].text:
            winner = 'B'

        stat_row = soup.select_one('tr.b-fight-details__table-row')
        cols = stat_row.find_all('td')
        A_sig_strikes = int(cols[0].text.split()[0])
        B_sig_strikes = int(cols[1].text.split()[0])
        A_td = int(cols[4].text.split()[0])
        B_td = int(cols[5].text.split()[0])

        return {
            'fighter_A': fighter_A,
            'fighter_B': fighter_B,
            'A_sig_strikes': A_sig_strikes,
            'B_sig_strikes': B_sig_strikes,
            'A_takedowns': A_td,
            'B_takedowns': B_td,
            'winner': winner,
            'fight_url': fight_url
        }

    except Exception as e:
        print(f"Error parsing {fight_url}: {e}")
        return None

def scrape_event(event_url):
    links = get_fight_links_from_event(event_url)
    return [fight for link in links if (fight := parse_fight_stats(link))]
