from flask import Flask, request, jsonify

app = Flask(__name__)  # Make sure this is global

# ✅ Simple test route
@app.route("/")
def home():
    return "🏠 BixPix Flask API is running!"

# ✅ List all routes (for debugging)
@app.route("/routes")
def list_routes():
    import urllib
    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.parse.unquote(f"{rule.endpoint:25s} {methods:20s} {rule}")
        output.append(line)
    return "<br>".join(sorted(output))

# ✅ Test POST route
@app.route("/api/getFighter", methods=["POST"])
def get_fighters():
    data = request.get_json()
    return jsonify({"status": "success", "received": data})

# ✅ Must be included to run via `python app.py`
if __name__ == "__main__":
    app.run(debug=True)
