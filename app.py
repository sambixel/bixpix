from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

@app.route('/api/getFighter', methods=['POST'])
def getFighter():
    try:
        data = request.get_json(silent=True) or {}
        url = 'https://www.espn.com' + data.get('cardURL')
        # Spoof headers to avoid 403
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers)

        # Makes HTML easily accessible for searching
        soup = BeautifulSoup(res.text, "html.parser")

        tags = soup.select('a.AnchorLink.db.h9.MMAFightCenter__ProfileLink')
        links = [ tag['href'] for tag in tags ]

        return jsonify({'links': links})
    
    except Exception as e:
        # still returns JSON (and CORS header) on errors
        return jsonify(error=str(e)), 500

if __name__ == '__main__':
    app.run(debug=True)
