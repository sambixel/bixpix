import requests
from bs4 import BeautifulSoup

url = "https://www.espn.com/mma/fightcenter/_/id/600053168/league/ufc"

# Spoof headers to avoid 403
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

res = requests.get("http://www.ufcstats.com/statistics/events/upcoming", headers=headers)
soup = BeautifulSoup(res.text, "html.parser")

dropdown_options = []

# Find all event rows
rows = soup.select('tr.b-statistics__table-row')
for row in rows:
    link_tag = row.find('a', class_='b-link')
    if link_tag:
        event_name = link_tag.text.strip()
        event_url = link_tag['href']
        date_span = row.find('span', class_='b-statistics__date')
        event_date = date_span.text.strip() if date_span else 'Unknown'
        dropdown_options.append({
            'name': f"{event_name}",
            'url': event_url,
            'date': event_date
        })

def next_card():
    next = dropdown_options[0]
    next_card_url = next["url"]
    next_card_name = next["name"]
    return {
        "name": next_card_name,
        "url": next_card_url
    }

html = '<select id="ufcEventSelect">\n'
# html += '<option disabled selected>Select an upcoming UFC event</option>\n'

for option in dropdown_options:
    html += f'  <option value="{option["url"]}">{option["name"]}</option>\n'

html += '</select>'


with open("index_template.html", "r") as file:
    html_template = file.read()
# Replace the insertion point with espn's exact dropdown html She my rider for a reason
html_output = html_template.replace("<!--DropDown Insert-->", html)
# Write over the original index.html with index template, except the insertion has been replaced with the dropdown.
with open("index.html", "w") as file:
    file.write(html_output)

# Do the same process for events page.
with open("event_template.html", "r") as file:
    event_template = file.read()
event_output = event_template.replace("<!--DropDown Insert-->", html)
with open("event.html", "w") as file:
    file.write(event_output)