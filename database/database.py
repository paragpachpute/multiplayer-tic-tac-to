import sqlite3
import logging
from datetime import datetime

DB_FILE = "database/game_results.db"

def initialize_database():
    """Creates the game_results table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner_name TEXT,
            loser_name TEXT,
            outcome TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

def record_game_result(winner_name, loser_name, outcome):
    """Records the result of a single game to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO game_results (winner_name, loser_name, outcome, timestamp) VALUES (?, ?, ?, ?)",
        (winner_name, loser_name, outcome, timestamp)
    )
    conn.commit()
    conn.close()
    logging.info(f"Game result recorded: Winner={winner_name}, Loser={loser_name}, Outcome={outcome}")

def get_leaderboard():
    """Calculates and returns the player leaderboard."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Get all unique player names
    cursor.execute("SELECT winner_name FROM game_results WHERE winner_name IS NOT NULL")
    winners = [row[0] for row in cursor.fetchall()]
    cursor.execute("SELECT loser_name FROM game_results WHERE loser_name IS NOT NULL")
    losers = [row[0] for row in cursor.fetchall()]
    all_names = set(winners + losers)
    
    leaderboard = []
    for name in all_names:
        # Calculate wins
        cursor.execute("SELECT COUNT(*) FROM game_results WHERE winner_name = ? AND outcome = 'win'", (name,))
        wins = cursor.fetchone()[0]
        
        # Calculate draws
        cursor.execute("SELECT COUNT(*) FROM game_results WHERE outcome = 'draw' AND (winner_name = ? OR loser_name = ?)", (name, name))
        draws = cursor.fetchone()[0]
        
        score = (wins * 3) + (draws * 1)
        leaderboard.append({"name": name, "wins": wins, "draws": draws, "score": score})
        
    conn.close()
    
    # Sort by score (descending) and then by name (ascending)
    leaderboard.sort(key=lambda x: (-x['score'], x['name']))
    
    # Add ranks
    for i, player in enumerate(leaderboard):
        player['rank'] = i + 1
        
    return leaderboard
