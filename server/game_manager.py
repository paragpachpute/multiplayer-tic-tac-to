import logging
import uuid
from server.game_room import Game

active_games = {}

def create_game():
    """Creates a new game room and returns its ID."""
    game_id = str(uuid.uuid4())[:4].upper()
    active_games[game_id] = Game(game_id, on_empty=remove_game)
    logging.info(f"New game created with ID: {game_id}")
    return active_games[game_id]

def get_game(game_id):
    """Finds and returns a game room by its ID."""
    return active_games.get(game_id)

def remove_game(game_id):
    """Removes a game room from the active list."""
    if game_id in active_games:
        del active_games[game_id]
        logging.info(f"Game {game_id} is empty and has been removed.")
