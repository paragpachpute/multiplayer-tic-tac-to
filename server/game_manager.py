import logging
import uuid
from server.game_room import Game
from server.ultimate_game_room import UltimateGame

active_games = {}

def create_game(game_mode='standard'):
    """Creates a new game room and returns its ID."""
    game_id = str(uuid.uuid4())[:4].upper()
    
    if game_mode == 'ultimate':
        active_games[game_id] = UltimateGame(game_id, on_empty=remove_game)
        logging.info(f"New Ultimate game created with ID: {game_id}")
    else:
        active_games[game_id] = Game(game_id, on_empty=remove_game)
        logging.info(f"New standard game created with ID: {game_id}")
        
    return active_games[game_id]

def get_game(game_id):
    """Finds and returns a game room by its ID."""
    return active_games.get(game_id)

def remove_game(game_id):
    """Removes a game room from the active list."""
    if game_id in active_games:
        del active_games[game_id]
        logging.info(f"Game {game_id} is empty and has been removed.")
