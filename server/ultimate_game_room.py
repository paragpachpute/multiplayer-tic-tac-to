import logging
from typing import List, Optional, Dict
from database import database
from server.protocol import GameState, GameStateResponse, to_dict

class UltimateGame:
    """Represents a single, isolated Ultimate Tic-Tac-Toe game session."""
    def __init__(self, game_id, on_empty):
        self.game_id = game_id
        self.clients = set()
        self.player_names: Dict[str, Optional[str]] = {"X": None, "O": None}
        self._on_empty = on_empty

        # --- Ultimate Game State ---
        self.macro_board: List[List[Optional[str]]] = [[None for _ in range(3)] for _ in range(3)]
        self.micro_boards: List[List[List[Optional[str]]]] = [[[None for _ in range(3)] for _ in range(3)] for _ in range(9)]
        self.active_micro_board_coords = None # [row, col]. None means any board is playable.
        
        self.current_player = "X"
        self.game_over = False
        self.winner = None

    # --- Client Management ---
    async def add_client(self, client_conn, name):
        if len(self.clients) >= 2: return None
        player_symbol = "X" if not self.clients else "O"
        client_conn.player_symbol = player_symbol
        client_conn.player_name = name
        client_conn.game_id = self.game_id
        self.clients.add(client_conn)
        self.player_names[player_symbol] = name
        logging.info(f"[Ultimate Game {self.game_id}] Player {name} ({player_symbol}) joined.")
        return player_symbol

    async def reconnect_client(self, new_client_conn, player_symbol, name):
        old_client = next((c for c in self.clients if c.player_symbol == player_symbol), None)
        if old_client: self.clients.remove(old_client)
        new_client_conn.player_symbol = player_symbol
        new_client_conn.player_name = name
        new_client_conn.game_id = self.game_id
        self.clients.add(new_client_conn)
        self.player_names[player_symbol] = name
        logging.info(f"[Ultimate Game {self.game_id}] Player {name} ({player_symbol}) reconnected.")

    async def remove_client(self, client_conn):
        self.clients.remove(client_conn)
        logging.info(f"Client {client_conn.player_name} disconnected from Ultimate Game {self.game_id}")
        if not self.clients: self._on_empty(self.game_id)

    # --- Core Game Logic ---
    async def handle_move(self, client_conn, move_data):
        logging.info(f"[Game {self.game_id}] Received move: {move_data} from {client_conn.player_name}. Active board: {self.active_micro_board_coords}")
        if self.game_over or client_conn.player_symbol != self.current_player: return

        # The client sends absolute row/col from 0-8. We derive the board and cell coords.
        row, col = move_data['row'], move_data['col']
        macro_row, macro_col = row // 3, col // 3
        micro_row, micro_col = row % 3, col % 3
        micro_board_index = macro_row * 3 + macro_col

        # --- Validate Move ---
        # 1. Is the move in the correct active micro board?
        if self.active_micro_board_coords and (macro_row, macro_col) != tuple(self.active_micro_board_coords):
            logging.warning(f"[Game {self.game_id}] Invalid move: not in active micro board.")
            return
        # 2. Is the micro board already won or drawn?
        if self.macro_board[macro_row][macro_col] is not None:
            logging.warning(f"[Game {self.game_id}] Invalid move: micro board is already finished.")
            return
        # 3. Is the cell already taken?
        if self.micro_boards[micro_board_index][micro_row][micro_col] is not None:
            logging.warning(f"[Game {self.game_id}] Invalid move: cell is already taken.")
            return

        # --- Apply Move ---
        self.micro_boards[micro_board_index][micro_row][micro_col] = self.current_player
        
        # --- Check for Wins and Draws ---
        micro_board_winner = self._check_board_win(self.micro_boards[micro_board_index])
        if micro_board_winner:
            self.macro_board[macro_row][macro_col] = micro_board_winner
            
            macro_board_winner = self._check_board_win(self.macro_board)
            if macro_board_winner:
                if macro_board_winner != 'draw':
                    self.winner = macro_board_winner
                self.game_over = True
                self._record_game_result()
                await self.broadcast_state()
                return

        # --- Determine Next Active Board ---
        next_active_coords = [micro_row, micro_col]
        if self.macro_board[next_active_coords[0]][next_active_coords[1]] is not None:
            self.active_micro_board_coords = None # Free move
        else:
            self.active_micro_board_coords = next_active_coords

        # --- Switch Player and Broadcast ---
        self.current_player = "O" if self.current_player == "X" else "X"
        await self.broadcast_state()

    def _check_board_win(self, board):
        """Checks a 3x3 board for a win or draw. Returns 'X', 'O', 'draw', or None."""
        # Check rows and columns for a winner, excluding 'draw' as a winning symbol
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] and board[i][0] not in [None, 'draw']:
                return board[i][0]
            if board[0][i] == board[1][i] == board[2][i] and board[0][i] not in [None, 'draw']:
                return board[0][i]
        # Check diagonals for a winner
        if board[0][0] == board[1][1] == board[2][2] and board[0][0] not in [None, 'draw']:
            return board[0][0]
        if board[0][2] == board[1][1] == board[2][0] and board[0][2] not in [None, 'draw']:
            return board[0][2]
        # Check for a draw (all cells are filled)
        if all(cell is not None for row in board for cell in row):
            return 'draw'
        return None

    def _record_game_result(self):
        winner_name, loser_name, outcome = None, None, "draw"
        if self.winner and self.winner != 'draw':
            outcome = "win"
            winner_name = self.player_names[self.winner]
            loser_symbol = "O" if self.winner == "X" else "X"
            loser_name = self.player_names[loser_symbol]
        else:
            winner_name, loser_name = self.player_names['X'], self.player_names['O']
        database.record_game_result(winner_name, loser_name, outcome, game_mode='ultimate')

    async def broadcast_state(self):
        # For ultimate games, the main 'board' is None. The state is in the other fields.
        game_state = GameState(
            board=None, # Standard board is unused
            micro_boards=self.micro_boards,
            macro_board=self.macro_board,
            active_micro_board_coords=self.active_micro_board_coords,
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
                pass