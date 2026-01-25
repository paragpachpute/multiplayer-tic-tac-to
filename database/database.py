import sqlite3
import logging
import os
from datetime import datetime

DB_FILE = os.getenv('DATABASE_FILE', 'database/game_results.db')

def initialize_database():
    """Creates or updates the game_results table."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            winner_name TEXT,
            loser_name TEXT,
            outcome TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            game_mode TEXT DEFAULT 'standard'
        )
    ''')
    
    # Add game_mode column if it doesn't exist (for backward compatibility)
    try:
        cursor.execute("ALTER TABLE game_results ADD COLUMN game_mode TEXT DEFAULT 'standard'")
        logging.info("Added 'game_mode' column to the database.")
    except sqlite3.OperationalError:
        # Column already exists, which is fine
        pass
        
    conn.commit()
    conn.close()
    logging.info("Database initialized.")

def reset_database():
    """Deletes existing database file and creates a fresh one. Used for test mode."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        logging.info(f"Deleted existing database: {DB_FILE}")
    initialize_database()
    logging.info(f"Fresh database created: {DB_FILE}")

def record_game_result(winner_name, loser_name, outcome, game_mode='standard'):
    """Records the result of a single game to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO game_results (winner_name, loser_name, outcome, timestamp, game_mode) VALUES (?, ?, ?, ?, ?)",
        (winner_name, loser_name, outcome, timestamp, game_mode)
    )
    conn.commit()
    conn.close()
    logging.info(f"Game result recorded: Winner={winner_name}, Loser={loser_name}, Outcome={outcome}, Mode={game_mode}")

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

        # Calculate losses
        cursor.execute("SELECT COUNT(*) FROM game_results WHERE loser_name = ? AND outcome = 'win'", (name,))
        losses = cursor.fetchone()[0]

        # Calculate draws
        cursor.execute("SELECT COUNT(*) FROM game_results WHERE outcome = 'draw' AND (winner_name = ? OR loser_name = ?)", (name, name))
        draws = cursor.fetchone()[0]

        # Calculate total games and win percentage
        total_games = wins + losses + draws
        if total_games > 0:
            win_percentage = round((wins / total_games) * 100, 2)
        else:
            win_percentage = 0.0

        # Get last game played date
        cursor.execute("SELECT MAX(timestamp) FROM game_results WHERE winner_name = ? OR loser_name = ?", (name, name))
        last_timestamp = cursor.fetchone()[0]

        # Format the date
        try:
            if last_timestamp:
                last_game_date = datetime.fromisoformat(last_timestamp).strftime("%Y-%m-%d")
            else:
                last_game_date = "N/A"
        except (ValueError, AttributeError):
            last_game_date = "N/A"

        leaderboard.append({
            "name": name,
            "wins": wins,
            "losses": losses,
            "draws": draws,
            "win_percentage": win_percentage,
            "last_game_date": last_game_date
        })

    conn.close()

    # Sort by wins (descending), then draws (descending), then losses (descending)
    leaderboard.sort(key=lambda x: (-x['wins'], -x['draws'], -x['losses']))

    # Limit to top 10 players
    leaderboard = leaderboard[:10]

    # Add ranks
    for i, player in enumerate(leaderboard):
        player['rank'] = i + 1

    return leaderboard

def get_games_played_per_day(days_limit=7):
    """
    Counts the number of games played per day for the last N days.

    Args:
        days_limit (int): The number of past days to retrieve data for.

    Returns:
        list: A list of dictionaries, e.g., [{"date": "YYYY-MM-DD", "count": N}].
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # The query groups by the date part of the timestamp and counts the entries.
    # It filters for records within the specified date range.
    query = """
        SELECT
            DATE(timestamp) as game_date,
            COUNT(*) as game_count
        FROM
            game_results
        WHERE
            DATE(timestamp) >= DATE('now', '-' || ? || ' days')
        GROUP BY
            game_date
        ORDER BY
            game_date ASC;
    """
    
    cursor.execute(query, (days_limit,))
    
    rows = cursor.fetchall()
    conn.close()
    
    # Format the data for the API response
    games_per_day = [{"date": row[0], "count": row[1]} for row in rows]
    
    return games_per_day
