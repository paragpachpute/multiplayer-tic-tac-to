from flask import Flask, jsonify
from flask_cors import CORS
from database import database
from server import config

app = Flask(__name__)
CORS(app)

@app.route('/leaderboard', methods=['GET'])
def get_leaderboard_endpoint():
    """API endpoint to get the leaderboard data."""
    leaderboard_data = database.get_leaderboard()
    return jsonify(leaderboard_data)

