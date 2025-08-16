import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

def get_events():
    """Scrape UFCStats upcoming events for dropdown."""
    res = requests.get("http://www.ufcstats.com/statistics/events/upcoming", headers=HEADERS, timeout=30)
    soup = BeautifulSoup(res.text, "html.parser")
    events = []
    rows = soup.select("tr.b-statistics__table-row")
    for row in rows:
        link_tag = row.find("a", class_="b-link")
        if not link_tag:
            continue
        name = link_tag.get_text(strip=True)
        url = link_tag.get("href")
        date_span = row.find("span", class_="b-statistics__date")
        date = date_span.get_text(strip=True) if date_span else "Unknown"
        events.append({"name": name, "url": url, "date": date})
    return events

def next_card():
    evts = get_events()
    if not evts:
        return {"name": "Unknown", "url": ""}
    return evts[0]
