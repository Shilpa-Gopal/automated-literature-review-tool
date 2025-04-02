from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({"message": "API is working!"})

@app.route('/test')
def test():
    return jsonify({"message": "Test endpoint is working!"})
