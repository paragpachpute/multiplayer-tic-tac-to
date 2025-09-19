import asyncio
import logging
from typing import Dict, Optional
from database import database
from server.protocol import GameState, GameStateResponse, to_dict
from server.ai_logic import find_best_move
from server.game_room import Game

class AIGameRoom(Game):
    """
    Represents a Tic-Tac-Toe game against a computer opponent.
    Inherits from the base Game class but overrides move handling.
    """
    def __init__(self, game_id, on_empty, executor):
        super().__init__(game_id, on_empty)
        self.executor = executor
        self.player_names: Dict[str, Optional[str]] = {"X": None, "O": "Computer"}

    async def add_client(self, client_conn, name):
        """Only allows one human player ('X') to join."""
        if self.clients: # Game is already full with one player
            return None
        
        player_symbol = "X"
        client_conn.player_symbol = player_symbol
        client_conn.player_name = name
        client_conn.game_id = self.game_id
        self.clients.add(client_conn)
        
        self.player_names[player_symbol] = name
        logging.info(f"[AI Game {self.game_id}] Player {name} ({player_symbol}) joined.")
        return player_symbol

    async def start_game(self):
        """Starts the game by broadcasting the initial state."""
        logging.info(f"[AI Game {self.game_id}] Starting game.")
        await self.broadcast_state()

    async def handle_move(self, client_conn, move_data):
        """Handles a move from the human player and triggers the AI's response."""
        if self.game_over or client_conn.player_symbol != self.current_player:
            return
        
        # 1. Process the human's move
        row, col = move_data['row'], move_data['col']
        if self.board[row][col] is None:
            self.board[row][col] = client_conn.player_symbol
            self._check_win()
            if not self.game_over: self._check_draw()
            
            # If the game isn't over, switch to AI's turn
            if not self.game_over:
                self.current_player = "O"
                await self.broadcast_state() # Show the human's move immediately
                await self._make_ai_move()
            else:
                await self.broadcast_state()

    async def _make_ai_move(self):
        """Calculates and performs the AI's move."""
        if self.game_over:
            return

        logging.info(f"[AI Game {self.game_id}] AI is thinking...")
        
        # Run the blocking AI calculation in the process pool
        loop = asyncio.get_running_loop()
        # The AI logic needs a copy of the board to prevent race conditions
        board_copy = [row[:] for row in self.board]
        ai_move = await loop.run_in_executor(
            self.executor, find_best_move, board_copy
        )
        
        row, col = ai_move
        logging.info(f"[AI Game {self.game_id}] AI chose move: ({row}, {col})")

        if self.board[row][col] is None:
            self.board[row][col] = 'O'
            self._check_win()
            if not self.game_over: self._check_draw()
        
        # Switch back to the human's turn
        if not self.game_over:
            self.current_player = "X"
            
        await self.broadcast_state()
