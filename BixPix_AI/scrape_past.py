# scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36"
}
events_scraped = 0
url = "http://www.ufcstats.com/statistics/events/completed"

while events_scraped < 100:
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    event_links = soup.select("a.b-link.b-link_style_black")
    for event in event_links:
        fighters = soup.select("a.b-link.b-link_style_black")
        for fighter in fighters:
            stats = soup.select("li.b-list__box-list-item.b-list__box-list-item_type_block")
            
