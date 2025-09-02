import json
import logging
from typing import Dict, Optional
from database import database
from server.protocol import GameState, GameStateResponse, to_dict

class Game:
    """Represents a single, isolated Tic-Tac-Toe game session."""
    def __init__(self, game_id, on_empty):
        self.game_id = game_id
        self.clients = set() # This will now store ClientConnection objects
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_over = False
        self.winner = None
        self.player_names: Dict[str, Optional[str]] = {"X": None, "O": None}
        self._on_empty = on_empty

    async def add_client(self, client_conn, name):
        if len(self.clients) >= 2:
            return None

        player_symbol = "X" if not self.clients else "O"
        client_conn.player_symbol = player_symbol
        client_conn.player_name = name
        client_conn.game_id = self.game_id
        self.clients.add(client_conn)
        
        self.player_names[player_symbol] = name
        logging.info(f"[Game {self.game_id}] Player {name} ({player_symbol}) joined.")
        return player_symbol

    async def reconnect_client(self, new_client_conn, player_symbol, name):
        """Replaces a disconnected client with a new connection."""
        # Find the old, disconnected client object to remove it
        old_client = None
        for client in self.clients:
            if client.player_symbol == player_symbol:
                old_client = client
                break
        
        if old_client:
            self.clients.remove(old_client)

        # Add the new client connection
        new_client_conn.player_symbol = player_symbol
        new_client_conn.player_name = name
        new_client_conn.game_id = self.game_id
        self.clients.add(new_client_conn)
        
        self.player_names[player_symbol] = name
        logging.info(f"[Game {self.game_id}] Player {name} ({player_symbol}) reconnected.")

    async def remove_client(self, client_conn):
        self.clients.remove(client_conn)
        logging.info(f"Client {client_conn.player_name} disconnected from Game {self.game_id}")
        if not self.clients:
            self._on_empty(self.game_id)
        else:
            # Don't end the game immediately, allow for reconnection
            pass

    def _check_win(self):
        b = self.board
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] and b[i][0] is not None: self.winner = b[i][0]
            if b[0][i] == b[1][i] == b[2][i] and b[0][i] is not None: self.winner = b[0][i]
        if b[0][0] == b[1][1] == b[2][2] and b[0][0] is not None: self.winner = b[0][0]
        if b[0][2] == b[1][1] == b[2][0] and b[0][2] is not None: self.winner = b[0][2]
        if self.winner:
            self.game_over = True
            self._record_game_result()

    def _check_draw(self):
        if not any(None in row for row in self.board) and not self.winner:
            self.game_over = True
            self._record_game_result()

    def _record_game_result(self):
        winner_name, loser_name, outcome = None, None, "draw"
        if self.winner:
            outcome = "win"
            winner_name = self.player_names[self.winner]
            loser_symbol = "O" if self.winner == "X" else "X"
            loser_name = self.player_names[loser_symbol]
        else:
            winner_name, loser_name = self.player_names['X'], self.player_names['O']
        database.record_game_result(winner_name, loser_name, outcome)

    async def handle_move(self, client_conn, move_data):
        if self.game_over or client_conn.player_symbol != self.current_player:
            return
        
        row, col = move_data['row'], move_data['col']
        if self.board[row][col] is None:
            self.board[row][col] = client_conn.player_symbol # Correctly use the wrapper
            self._check_win()
            if not self.game_over: self._check_draw()
            if not self.game_over: self.current_player = "O" if self.current_player == "X" else "X"
            await self.broadcast_state()

    async def restart_game(self):
        self.board = [[None for _ in range(3)] for _ in range(3)]
        self.current_player = "X"
        self.game_over = False
        self.winner = None
        logging.info(f"[Game {self.game_id}] Restarted.")
        await self.broadcast_state()

    async def broadcast_state(self):
        game_state = GameState(
            board=self.board,
            current_player=self.current_player,
            game_over=self.game_over,
            winner=self.winner,
            player_names=self.player_names
        )
        response = GameStateResponse(state=game_state)
        
        for client_conn in self.clients:
            try:
                await client_conn.send(to_dict(response))
            except Exception:
                # The disconnection will be handled by the main server loop
                pass