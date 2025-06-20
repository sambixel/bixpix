import requests
from bs4 import BeautifulSoup

url = "https://www.espn.com/mma/fightcenter/_/id/600053168/league/ufc"

# Spoof headers to avoid 403
headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

res = requests.get(url, headers=headers)

# Makes HTML easily accessible for searching
soup = BeautifulSoup(res.text, "html.parser")

# Get the Dropdown from ESPN
dropdowns = soup.find_all("select", class_="dropdown__select")
correct_dropdown = next(
    (dropdown for dropdown in dropdowns if any(len(option.get("value", "")) == 9 for option in dropdown.find_all("option"))),
    None  # fallback if no match is found
)

# Make ESPN's dropdown a string
dropdown_html = str(correct_dropdown)
with open("index_template.html", "r") as file:
    html_template = file.read()
# Replace the insertion point with espn's exact dropdown html
html_output = html_template.replace("<!--DropDown Insert-->", dropdown_html)
# Write over the original index.html with index template, except the insertion has been replaced with the dropdown.
with open("index.html", "w") as file:
    file.write(html_output)

# Do the same process for events page.
with open("event_template.html", "r") as file:
    event_template = file.read()
event_output = event_template.replace("<!--DropDown Insert-->", dropdown_html)
with open("event.html", "w") as file:
    file.write(event_output)





# Get all fights.
# fightCard = soup.select("div.mb6")
# for fight in fightCard:
#     names = fight.select("span.truncate.tc.db").text.strip()

#     # If the bout is not complete, continue.
#     if(len(names) < 2):
#         continue
    
#     print(names[0] + " vs " + names[1])
    