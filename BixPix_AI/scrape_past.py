import requests
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import re

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def convert_height(h):
    feet = int(h[0])
    inches = int(h[3:h.find('"')])
    return feet * 12 + inches

def convert_percent(p):
    return float(p.strip('%')) / 100.0

def parse_stats(soup, fight_year):
    stats = {}
    fs = soup.select("li.b-list__box-list-item.b-list__box-list-item_type_block")

    for li in fs:
        label_tag = li.select_one("i.b-list__box-item-title")
        if not label_tag:
            continue

        label = label_tag.text.strip().replace(":", "")
        value = li.get_text(strip=True).replace(label_tag.text.strip(), "").strip()

        try:
            if label == "Height":
                stats["height"] = convert_height(value)
            elif label == "Weight":
                stats["weight"] = int(value.split()[0])
            elif label == "Reach":
                stats["reach"] = int(value.replace('"', ''))
            elif label == "DOB":
                stats["age"] = int(fight_year) - int(value[-4:])
        except Exception as e:
            print(f"Skipping {label} due to parse error: {e}")

    # Career statistics — still assuming they appear in a consistent order
    text_items = soup.select("li.b-list__box-list-item")
    for item in text_items:
        text = item.text.strip()
        try:
            if "SLpM" in text:
                stats["SLpM"] = float(text.split(":")[1].strip())
            elif "Str. Acc." in text:
                stats["Str_Acc"] = convert_percent(text.split(":")[1])
            elif "SApM" in text:
                stats["SApM"] = float(text.split(":")[1].strip())
            elif "Str. Def" in text:
                stats["Str_Def"] = convert_percent(text.split(":")[1])
            elif "TD Avg." in text:
                stats["TD_Avg"] = float(text.split(":")[1].strip())
            elif "TD Acc." in text:
                stats["TD_Acc"] = convert_percent(text.split(":")[1])
            elif "TD Def." in text:
                stats["TD_Def"] = convert_percent(text.split(":")[1])
            elif "Sub. Avg." in text:
                stats["Sub_Avg"] = float(text.split(":")[1].strip())
        except:
            continue

    return stats


# CSV setup (same as before)…
fieldnames = [
    "fight_date",
    *(f"f1_{f}" for f in ["height","weight","reach","age","SLpM","Str_Acc","SApM","Str_Def","TD_Avg","TD_Acc","TD_Def","Sub_Avg"]),
    *(f"f2_{f}" for f in ["height","weight","reach","age","SLpM","Str_Acc","SApM","Str_Def","TD_Avg","TD_Acc","TD_Def","Sub_Avg"]),
    "label"
]

with open("fight_data.csv","w",newline="") as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    max_events = 5000
    events_scraped = 0
    page = 1

    # keep going until we hit max_events or no more pages
    while events_scraped < max_events:
        page_url = f"http://www.ufcstats.com/statistics/events/completed?page={page}"
        res = requests.get(page_url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")

        # get all event links on this page
        event_links = [a["href"] for a in soup.select("a.b-link.b-link_style_black")]

        # if page is empty, break out
        if not event_links:
            break

        for ev in event_links:
            # stop if we've collected enough
            if events_scraped >= max_events:
                break

            ev_soup = BeautifulSoup(requests.get(ev, headers=headers).text, "html.parser")

            raw_date = ev_soup.select_one("li.b-list__box-list-item").get_text(strip=True)
            clean_date = raw_date.replace("Date:", "").strip()
            fight_year = clean_date[-4:]
            fight_date = datetime.strptime(clean_date, "%B %d, %Y").date()


            fighters = [a["href"] for a in ev_soup.select("a.b-link.b-link_style_black")]

            # pair fighters two at a time
            for i in range(0, len(fighters), 2):
                if events_scraped >= max_events:
                    break

                try:
                    # winner
                    f1 = BeautifulSoup(requests.get(fighters[i], headers=headers).text, "html.parser")
                    stats1 = parse_stats(f1, fight_year)
                    # loser
                    f2 = BeautifulSoup(requests.get(fighters[i+1], headers=headers).text, "html.parser")
                    stats2 = parse_stats(f2, fight_year)

                    row = {"fight_date": fight_date}
                    for k, v in stats1.items():
                        row[f"f1_{k}"] = v
                    for k, v in stats2.items():
                        row[f"f2_{k}"] = v
                    row["label"] = 1

                    writer.writerow(row)
                    events_scraped += 1

                except Exception as e:
                    print(f"Skipping a fight due to parse error: {e}")

        page += 1

print(f"Done — scraped {events_scraped} fights across {page-1} pages.")
