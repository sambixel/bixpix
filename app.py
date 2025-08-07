from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import get_predictions, get_fight_links, get_fight_stats
from BixPix import next_card

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    card = next_card()
    return card["name"] + " ; " + card["url"]

@app.route("/api/getFighter", methods=["POST"])
def get_fighters():
    data = request.get_json()

    url = data['cardURL']
    links = get_fight_links(url)

    all_fight_data = []
    for link in links:
        fight_data = get_fight_stats(link)
        if fight_data:
            all_fight_data.append(fight_data)
    return jsonify({"status": "success", "received": all_fight_data})

@app.route("/api/getNext", methods=["POST"])
def get_next():
    # links = get_fight_links(next_card)
    nextCard = next_card()
    nextCardURL = nextCard["url"]

    payload = get_predictions(nextCardURL)
    return jsonify(payload)

if __name__ == "__main__":
    app.run(debug=True)
