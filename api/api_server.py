from flask import Flask, jsonify, request
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

@app.route('/game_stats', methods=['GET'])
def get_game_stats_endpoint():
    """
    API endpoint to get game statistics.
    Accepts a 'range' query parameter: 'week', 'month', or 'year'.
    Defaults to 'week'.
    """
    time_range = request.args.get('range', 'week').lower()
    
    if time_range == 'month':
        days_limit = 30
    elif time_range == 'year':
        days_limit = 365
    else: # Default to week
        days_limit = 7
        
    stats_data = database.get_games_played_per_day(days_limit)
    return jsonify(stats_data)

