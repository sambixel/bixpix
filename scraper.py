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

