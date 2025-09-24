import asyncio
import logging
import time
from typing import Dict, Optional
from database import database
from server.protocol import GameState, GameStateResponse, to_dict
from server.ultimate_game_room import UltimateGame
from server.ultimate_ai_logic import find_best_move

class UltimateAIGameRoom(UltimateGame):
    """
    Represents an Ultimate Tic-Tac-Toe game against a computer opponent.
    Inherits from the base UltimateGame class but overrides move handling.
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
        logging.info(f"[Ultimate AI Game {self.game_id}] Player {name} ({player_symbol}) joined.")
        return player_symbol

    async def start_game(self):
        """Starts the game by broadcasting the initial state and starting the timer."""
        logging.info(f"[Ultimate AI Game {self.game_id}] Starting game.")
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

        # 1. Process the human's move by calling the parent's handle_move logic
        # We need to temporarily set the current player to the human's symbol
        # to pass the validation in the parent method.
        original_player = self.current_player
        self.current_player = client_conn.player_symbol
        
        # We will call a modified version of the parent's move logic,
        # as we don't want it to switch players or broadcast yet.
        await self._process_human_move(move_data)
        
        self.current_player = original_player # Restore current player

        # If the game isn't over after the human's move, trigger the AI
        if not self.game_over:
            self.current_player = "O" # Switch to AI's turn
            await self.broadcast_state() # Show the human's move immediately
            await self._make_ai_move()
        else:
            await self.broadcast_state()

    async def _process_human_move(self, move_data):
        """A simplified version of the parent's handle_move, just for applying the move."""
        row, col = move_data['row'], move_data['col']
        macro_row, macro_col = row // 3, col // 3
        micro_row, micro_col = row % 3, col % 3
        micro_board_index = macro_row * 3 + macro_col

        # Basic validation
        if self.active_micro_board_coords and (macro_row, macro_col) != tuple(self.active_micro_board_coords): return
        if self.macro_board[macro_row][macro_col] is not None: return
        if self.micro_boards[micro_board_index][micro_row][micro_col] is not None: return

        # Apply move
        self.micro_boards[micro_board_index][micro_row][micro_col] = self.current_player
        
        # Check for wins
        micro_board_winner = self._check_board_win(self.micro_boards[micro_board_index])
        if micro_board_winner:
            self.macro_board[macro_row][macro_col] = micro_board_winner
            macro_board_winner = self._check_board_win(self.macro_board)
            if macro_board_winner:
                if macro_board_winner != 'draw': self.winner = macro_board_winner
                self.game_over = True
                self._record_game_result()

        # Determine the next active board for the AI
        next_active_coords = [micro_row, micro_col]
        if not self.game_over:
            if self.macro_board[next_active_coords[0]][next_active_coords[1]] is not None:
                self.active_micro_board_coords = None # Free move for AI
            else:
                self.active_micro_board_coords = next_active_coords

    async def _make_ai_move(self):
        """Calculates and performs the AI's move for the ultimate game."""
        if self.game_over:
            return

        logging.info(f"[Ultimate AI Game {self.game_id}] AI is thinking...")

        # Start timing the AI's turn
        ai_turn_start_time = time.time()

        # Prepare the state for the AI function
        current_state = {
            "micro_boards": [row[:] for row in self.micro_boards],
            "macro_board": [row[:] for row in self.macro_board],
            "active_micro_board_coords": self.active_micro_board_coords
        }

        loop = asyncio.get_running_loop()
        ai_move = await loop.run_in_executor(
            self.executor, find_best_move, current_state
        )

        # --- Timer Logic for AI Player ---
        ai_thinking_time = time.time() - ai_turn_start_time
        self.player_o_time_bank -= ai_thinking_time
        if self.player_o_time_bank <= 0:
            self.winner = "X" # Human wins if AI runs out of time
            self.game_over = True
            self._record_game_result()
            await self.broadcast_state()
            return

        if ai_move is None:
            logging.warning(f"[Ultimate AI Game {self.game_id}] AI returned no move. Game might be a draw.")
            self.game_over = True # Or handle as draw
            await self.broadcast_state()
            return

        row, col = ai_move
        logging.info(f"[Ultimate AI Game {self.game_id}] AI chose move: ({row}, {col}) after {ai_thinking_time:.2f}s")

        # Apply the AI's move
        macro_row, macro_col = row // 3, col // 3
        micro_row, micro_col = row % 3, col % 3
        micro_board_index = macro_row * 3 + macro_col
        self.micro_boards[micro_board_index][micro_row][micro_col] = 'O'

        # Check for wins
        micro_board_winner = self._check_board_win(self.micro_boards[micro_board_index])
        if micro_board_winner:
            self.macro_board[macro_row][macro_col] = micro_board_winner
            macro_board_winner = self._check_board_win(self.macro_board)
            if macro_board_winner:
                if macro_board_winner != 'draw': self.winner = macro_board_winner
                self.game_over = True
                self._record_game_result()

        # Determine next active board
        next_active_coords = [micro_row, micro_col]
        if self.macro_board[next_active_coords[0]][next_active_coords[1]] is not None:
            self.active_micro_board_coords = None
        else:
            self.active_micro_board_coords = next_active_coords

        # Switch back to the human's turn and reset the timer
        if not self.game_over:
            self.current_player = "X"
            self.current_turn_start_time = time.time()

        await self.broadcast_state()

    async def restart_game(self):
        """Resets the game to its initial state."""
        await super().restart_game()
        self.player_names = {"X": list(self.clients)[0].player_name if self.clients else None, "O": "Computer"}
        self.current_turn_start_time = time.time()
        await self.broadcast_state()
