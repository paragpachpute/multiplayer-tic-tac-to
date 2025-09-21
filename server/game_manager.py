import logging
import uuid
from server.game_room import Game
from server.ultimate_game_room import UltimateGame
from server.ai_game_room import AIGameRoom
from server.ultimate_ai_game_room import UltimateAIGameRoom

active_games = {}

def create_game(game_mode='standard'):
    """Creates a new multiplayer game room and returns it."""
    game_id = str(uuid.uuid4())[:4].upper()
    
    if game_mode == 'ultimate':
        active_games[game_id] = UltimateGame(game_id, on_empty=remove_game)
        logging.info(f"New Ultimate game created with ID: {game_id}")
    else:
        active_games[game_id] = Game(game_id, on_empty=remove_game)
        logging.info(f"New standard game created with ID: {game_id}")
        
    return active_games[game_id]

def create_ai_game(executor, game_mode='standard'):
    """Creates a new single-player AI game room and returns it."""
    game_id = str(uuid.uuid4())[:4].upper()
    
    if game_mode == 'ultimate':
        game = UltimateAIGameRoom(game_id, on_empty=remove_game, executor=executor)
        logging.info(f"New Ultimate AI game created with ID: {game_id}")
    else:
        game = AIGameRoom(game_id, on_empty=remove_game, executor=executor)
        logging.info(f"New standard AI game created with ID: {game_id}")
        
    active_games[game_id] = game
    return game

def get_game(game_id):
    """Finds and returns a game room by its ID."""
    return active_games.get(game_id)

def remove_game(game_id):
    """Removes a game room from the active list."""
    if game_id in active_games:
        del active_games[game_id]
        logging.info(f"Game {game_id} is empty and has been removed.")
