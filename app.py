from flask import Flask, request, jsonify
from flask_cors import CORS
from scraper import get_fight_links


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

    return jsonify({"status": "success", "received": links})


if __name__ == "__main__":
    app.run(debug=True)
