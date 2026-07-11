import re, hashlib
from datetime import datetime
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

# UFCStats now serves a JavaScript proof-of-work gate to block bots: an
# interstitial that asks the client to brute-force a nonce whose SHA-256 starts
# with N zero hex chars, POST it to /__c to receive an access cookie, then
# reload. A plain requests.get just sees the challenge page (no event data), so
# we replicate the PoW here and reuse one session/cookie across all requests.
_session = requests.Session()
_NONCE_RE = re.compile(r'nonce="([0-9a-fA-F]+)"')
_DIFFICULTY_RE = re.compile(r'new Array\((\d+)\+1\)')

def _solve_challenge(html: str) -> bool:
    m_nonce = _NONCE_RE.search(html)
    m_diff = _DIFFICULTY_RE.search(html)
    if not (m_nonce and m_diff):
        return False
    nonce, difficulty = m_nonce.group(1), int(m_diff.group(1))
    target = "0" * difficulty
    n = 0
    while hashlib.sha256(f"{nonce}:{n}".encode()).hexdigest()[:difficulty] != target:
        n += 1
    _session.post("http://www.ufcstats.com/__c",
                  data={"nonce": nonce, "n": n}, headers=HEADERS, timeout=15)
    return True

def fetch(url: str, **kwargs) -> requests.Response:
    """GET through a shared session, solving the UFCStats bot gate once if served."""
    kwargs.setdefault("headers", HEADERS)
    kwargs.setdefault("timeout", 30)
    res = _session.get(url, **kwargs)
    if "/__c" in res.text and "nonce=" in res.text and _solve_challenge(res.text):
        res = _session.get(url, **kwargs)
    return res

def _parse_event_rows(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
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

def get_events():
    """Scrape UFCStats events for the dropdown.

    UFCStats moves a card from 'upcoming' to 'completed' once it starts, so a
    card that is live right now is absent from the upcoming page. To keep it
    selectable mid-event, also check the top of the completed page and include
    any event dated today or yesterday (yesterday covers cards running past
    midnight) ahead of the upcoming list.
    """
    res = fetch("http://www.ufcstats.com/statistics/events/upcoming")
    upcoming = _parse_event_rows(res.text)

    live = []
    try:
        res = fetch("http://www.ufcstats.com/statistics/events/completed")
        completed = _parse_event_rows(res.text)
        seen = {e["url"] for e in upcoming}
        today = datetime.now().date()
        for e in completed[:3]:
            try:
                event_date = datetime.strptime(e["date"], "%B %d, %Y").date()
            except ValueError:
                continue
            if 0 <= (today - event_date).days <= 1 and e["url"] not in seen:
                live.append({**e, "name": e["name"] + " (live)"})
    except Exception as e:
        print(f"[events] completed-page check failed: {e}")

    return live + upcoming

def next_card():
    evts = get_events()
    if not evts:
        return {"name": "Unknown", "url": ""}
    return evts[0]
