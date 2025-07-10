from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import get_fight_links, get_fight_stats


app = Flask(__name__)
CORS(app)

# ✅ Simple test route
@app.route("/")
def home():
    return "🏠 BixPix Flask API is running!"

@app.route("/api/getFighter", methods=["POST"])
def get_fighters():
    data = request.get_json()

    url = data['cardURL']
    links = get_fight_links(url)

    all_fight_data = []
    # for link in links:
    #     fight_data = get_fight_stats(link)
    #     if fight_data:
    #         all_fight_data.append(fight_data)
    # return jsonify({"status": "success", "received": links})
    link = "http://www.ufcstats.com/fight-details/12cedec11b37ddc0"
    return jsonify({"status": "True", "stats": get_fight_stats(link)})


if __name__ == "__main__":
    app.run(debug=True)
