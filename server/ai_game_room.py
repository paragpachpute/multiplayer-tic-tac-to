import asyncio
import logging
import time
import os
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
        # AI game is always standard, so timer is 1 minute
        self.player_x_time_bank = float(os.getenv('PLAYER_TIMER_SECONDS_STANDARD', '60'))
        self.player_o_time_bank = float(os.getenv('PLAYER_TIMER_SECONDS_STANDARD', '60')) # AI's timer is not really used, but we keep it for consistency

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
        """Starts the game by broadcasting the initial state and starting the timer."""
        logging.info(f"[AI Game {self.game_id}] Starting game.")
        self.current_turn_start_time = time.time()
        await self.broadcast_state()

    async def handle_move(self, client_conn, move_data):
        """Handles a move from the human player and triggers the AI's response."""
        if self.game_over or client_conn.player_symbol != self.current_player:
            return
        
        # --- Timer Logic for Human Player ---
        time_spent = time.time() - self.current_turn_start_time
        self.player_x_time_bank -= time_spent
        if self.player_x_time_bank <= 0:
            self.winner = "O" # Computer wins if human runs out of time
            self.game_over = True
            self._record_game_result()
            await self.broadcast_state()
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
        
        # Switch back to the human's turn and reset the timer
        if not self.game_over:
            self.current_player = "X"
            self.current_turn_start_time = time.time()
            
        await self.broadcast_state()

    async def restart_game(self):
        """Resets the game to its initial state."""
        await super().restart_game() # Call the parent restart logic
        # Reset AI-specific state
        self.player_names = {"X": list(self.clients)[0].player_name if self.clients else None, "O": "Computer"}
        self.current_turn_start_time = time.time()
        await self.broadcast_state()