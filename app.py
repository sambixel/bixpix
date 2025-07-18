from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import get_fight_links, get_fight_stats


app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "🏠 BixPix Flask API is running!"

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

    # link = "http://www.ufcstats.com/fight-details/74099d470e8d2765"
    # return jsonify({"status": "True", "stats": get_fight_stats(link)})

if __name__ == "__main__":
    app.run(debug=True)
