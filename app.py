from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

CURATIONS = []


@app.route('/curate', methods=['POST'])
def submit_curation():
    CURATIONS.append(dict(request.json))
    return jsonify({'status': 'good'}) 


@app.route('/curations', methods=['GET'])
def get_curations():
    return jsonify(CURATIONS)


if __name__ == '__main__':
    app.run()

