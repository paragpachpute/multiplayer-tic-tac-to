import asyncio
import json
import logging
import websockets
import sys
import os
from threading import Thread
from concurrent.futures import ProcessPoolExecutor

# --- Setup ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from server import game_manager, config
from database import database
from server.protocol import GameCreatedResponse, GameJoinedResponse, ErrorResponse, MessageType, to_dict
from server.connection import ClientConnection

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s')

# --- Global Process Pool ---
# This executor will be used to run CPU-bound AI calculations in a separate process.
process_pool_executor = ProcessPoolExecutor()

# --- Core Message Routing ---
async def handle_message(message_str, client_conn):
    """Routes a received message to the appropriate game logic."""
    if not message_str: return # Ignore empty messages
    try:
        message = json.loads(message_str)
        msg_type = message.get("type")

        if msg_type == MessageType.CREATE_GAME:
            game_mode = message.get("game_mode", "standard")
            game = game_manager.create_game(game_mode)
            player_symbol = await game.add_client(client_conn, message.get("name", "Anonymous"))
            response = GameCreatedResponse(game_id=game.game_id, player_symbol=player_symbol)
            await client_conn.send(to_dict(response))

        elif msg_type == MessageType.CREATE_AI_GAME:
            game_mode = message.get("game_mode", "standard")
            game = game_manager.create_ai_game(process_pool_executor, game_mode)
            player_symbol = await game.add_client(client_conn, message.get("name", "Anonymous"))
            response = GameCreatedResponse(game_id=game.game_id, player_symbol=player_symbol)
            await client_conn.send(to_dict(response))
            # The AI game starts immediately
            await game.start_game()

        elif msg_type == MessageType.JOIN_GAME:
            game_id = message.get("game_id")
            game = game_manager.get_game(game_id)
            if game:
                player_symbol = await game.add_client(client_conn, message.get("name", "Anonymous"))
                if player_symbol:
                    response = GameJoinedResponse(game_id=game.game_id, player_symbol=player_symbol)
                    await client_conn.send(to_dict(response))
                    if len(game.clients) == 2:
                        await game.broadcast_state()
                else:
                    await client_conn.send(to_dict(ErrorResponse(message="Game is full.")))
            else:
                await client_conn.send(to_dict(ErrorResponse(message="Game not found.")))

        elif msg_type == MessageType.RECONNECT:
            game_id = message.get("game_id")
            game = game_manager.get_game(game_id)
            if game:
                await game.reconnect_client(
                    client_conn,
                    message.get("player_symbol"),
                    message.get("name")
                )
                await game.broadcast_state()
            else:
                # If the game doesn't exist, the client's state is stale.
                # We can just ignore this, and the client will show the lobby.
                pass

        elif client_conn.game_id:
            game = game_manager.get_game(client_conn.game_id)
            if game:
                if msg_type == MessageType.MOVE:
                    await game.handle_move(client_conn, message)
                elif msg_type == MessageType.RESTART:
                    await game.restart_game()
    except json.JSONDecodeError:
        logging.warning(f"Received invalid JSON: {message_str}")
    except Exception as e:
        logging.error(f"Error handling message: {e}", exc_info=True)

# --- Unified Connection Handler ---
async def connection_handler(client_conn):
    """Handles the entire lifecycle of a single client connection."""
    logging.info(f"New connection from {client_conn.get_remote_address()}")
    try:
        while True:
            try:
                # Wait for a message from the client with a 15-minute timeout.
                message = await asyncio.wait_for(client_conn.read(), timeout=900.0)
                
                # If the message is empty, it means the client has disconnected.
                if not message:
                    logging.info(f"Client {client_conn.get_remote_address()} sent an empty message, closing connection.")
                    break
                
                await handle_message(message, client_conn)
            except asyncio.TimeoutError:
                logging.info(f"Connection from {client_conn.get_remote_address()} timed out after 15 minutes. Closing.")
                break
    except (websockets.exceptions.ConnectionClosedError, ConnectionResetError, asyncio.IncompleteReadError):
        logging.info(f"Connection closed by client {client_conn.get_remote_address()}")
    except Exception as e:
        logging.error(f"Unexpected error in connection handler: {e}", exc_info=True)
    finally:
        logging.info(f"Cleaning up connection for {client_conn.get_remote_address()}")
        if client_conn.game_id:
            game = game_manager.get_game(client_conn.game_id)
            if game:
                await game.remove_client(client_conn)

# --- Main Entrypoint ---
async def main_async():
    """Initializes database and starts all servers."""
    # Check if running in test mode
    if os.getenv('TEST_MODE') == 'true':
        database.reset_database()
    else:
        database.initialize_database()
    
    async def ws_handler(websocket):
        await connection_handler(ClientConnection(websocket))

    async def tcp_handler(reader, writer):
        await connection_handler(ClientConnection(reader, writer))

    tcp_server = await asyncio.start_server(tcp_handler, config.HOST, config.TCP_PORT)
    ws_server = await websockets.serve(ws_handler, config.HOST, config.WS_PORT)
    
    logging.info(f"Unified Server listening on TCP:{config.TCP_PORT} and WS:{config.WS_PORT}")
    await asyncio.gather(tcp_server.serve_forever(), ws_server.wait_closed())