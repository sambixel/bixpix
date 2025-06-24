from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Allow only frontend on 5500
CORS(app, origins=["http://127.0.0.1:5500"])

@app.route('/api/hello', methods=['POST'])
def hello():
    data = request.get_json(silent=True) or {}
    name = data.get('name', 'World')
    return jsonify({ "message": f"Hello, {name}!" })

if __name__ == '__main__':
    app.run(debug=True)
