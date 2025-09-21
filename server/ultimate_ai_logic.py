"""
This module contains the AI logic for playing Ultimate Tic-Tac-Toe.
It uses a Minimax algorithm with a limited search depth and a heuristic
evaluation function to determine the best move.
"""
import math
import copy

# --- Constants ---
AI_PLAYER = 'O'
HUMAN_PLAYER = 'X'
SEARCH_DEPTH = 3 # How many moves ahead the AI will look. Higher is smarter but slower.

def find_best_move(state):
    """
    The main entry point for the AI. It finds the best possible move for the AI
    player given the current game state.

    Args:
        state (dict): The current game state dictionary containing micro_boards,
                      macro_board, and active_micro_board_coords.

    Returns:
        tuple: The best move as (row, col), or None if no moves are possible.
    """
    best_val = -math.inf
    best_move = None
    legal_moves = _get_legal_moves(state)

    # On the very first move of the game, just pick the center for speed.
    if len(legal_moves) == 81:
        return (4, 4)

    for move in legal_moves:
        temp_state = _apply_move(state, move, AI_PLAYER)
        move_val = _minimax(temp_state, SEARCH_DEPTH, -math.inf, math.inf, False) # Start with minimizing player (human)
        
        if move_val > best_val:
            best_val = move_val
            best_move = move

    return best_move

def _minimax(state, depth, alpha, beta, is_maximizing_player):
    """
    The core Minimax algorithm with Alpha-Beta pruning.
    """
    # Check for terminal state (win/loss/draw) or max depth
    winner = _check_board_win(state['macro_board'])
    if winner:
        return 10000 if winner == AI_PLAYER else -10000
    if depth == 0:
        return _evaluate_board_heuristic(state)

    legal_moves = _get_legal_moves(state)
    if not legal_moves: # Game is a draw
        return 0

    if is_maximizing_player:
        max_eval = -math.inf
        for move in legal_moves:
            child_state = _apply_move(state, move, AI_PLAYER)
            evaluation = _minimax(child_state, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break # Prune
        return max_eval
    else: # Minimizing player
        min_eval = math.inf
        for move in legal_moves:
            child_state = _apply_move(state, move, HUMAN_PLAYER)
            evaluation = _minimax(child_state, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break # Prune
        return min_eval

def _evaluate_board_heuristic(state):
    """
    Calculates a heuristic score for the current board state.
    Positive score is good for AI, negative is good for Human.
    """
    ai_score = _calculate_score_for_player(state, AI_PLAYER)
    human_score = _calculate_score_for_player(state, HUMAN_PLAYER)
    return ai_score - human_score

def _calculate_score_for_player(state, player):
    """
    Calculates the score based on board control for a single player.
    """
    score = 0
    # 1. Macro-board score
    score += _score_3x3_board(state['macro_board'], player) * 200

    # 2. Micro-board scores
    for i in range(9):
        if state['macro_board'][i // 3][i % 3] is None:
            score += _score_3x3_board(state['micro_boards'][i], player)
    
    return score

def _score_3x3_board(board, player):
    """
    Scores a single 3x3 grid based on how many lines of 1, 2, or 3 are controlled.
    """
    score = 0
    opponent = HUMAN_PLAYER if player == AI_PLAYER else AI_PLAYER

    lines = [
        board[0], board[1], board[2], # Rows
        [board[0][0], board[1][0], board[2][0]], # Cols
        [board[0][1], board[1][1], board[2][1]],
        [board[0][2], board[1][2], board[2][2]],
        [board[0][0], board[1][1], board[2][2]], # Diagonals
        [board[0][2], board[1][1], board[2][0]]
    ]

    for line in lines:
        player_count = line.count(player)
        opponent_count = line.count(opponent)

        if player_count == 3:
            score += 100
        elif player_count == 2 and opponent_count == 0:
            score += 10
        elif player_count == 1 and opponent_count == 0:
            score += 1
    
    return score

# --- Helper Functions for State Management ---

def _get_legal_moves(state):
    """
    Generates a list of all valid moves (row, col) from the current state.
    """
    moves = []
    active_coords = state.get('active_micro_board_coords')

    if active_coords:
        macro_row, macro_col = active_coords
        if state['macro_board'][macro_row][macro_col] is None:
            # Play is restricted to one micro-board
            micro_board_index = macro_row * 3 + macro_col
            micro_board = state['micro_boards'][micro_board_index]
            for r in range(3):
                for c in range(3):
                    if micro_board[r][c] is None:
                        moves.append((macro_row * 3 + r, macro_col * 3 + c))
            return moves

    # If no active board or the active board is already won, any open cell is legal
    for macro_r in range(3):
        for macro_c in range(3):
            if state['macro_board'][macro_r][macro_c] is None:
                micro_board_index = macro_r * 3 + macro_c
                micro_board = state['micro_boards'][micro_board_index]
                for micro_r in range(3):
                    for micro_c in range(3):
                        if micro_board[micro_r][micro_c] is None:
                            moves.append((macro_r * 3 + micro_r, macro_c * 3 + micro_c))
    return moves

def _apply_move(original_state, move, player):
    """
    Creates a new state object with the move applied. Does not modify the original.
    """
    state = copy.deepcopy(original_state)
    row, col = move
    macro_row, macro_col = row // 3, col // 3
    micro_row, micro_col = row % 3, col % 3
    micro_board_index = macro_row * 3 + macro_col

    state['micro_boards'][micro_board_index][micro_row][micro_col] = player

    # Check if the micro-board was won
    micro_winner = _check_board_win(state['micro_boards'][micro_board_index])
    if micro_winner:
        state['macro_board'][macro_row][macro_col] = micro_winner

    # Determine the next active board
    next_macro_row, next_macro_col = micro_row, micro_col
    if state['macro_board'][next_macro_row][next_macro_col] is not None:
        state['active_micro_board_coords'] = None # Free move
    else:
        state['active_micro_board_coords'] = [next_macro_row, next_macro_col]
        
    return state

def _check_board_win(board):
    """
    Checks a 3x3 board for a win or draw. Returns 'X', 'O', 'draw', or None.
    """
    for i in range(3):
        if board[i][0] == board[i][1] == board[i][2] and board[i][0] not in [None, 'draw']:
            return board[i][0]
        if board[0][i] == board[1][i] == board[2][i] and board[0][i] not in [None, 'draw']:
            return board[0][i]
    if board[0][0] == board[1][1] == board[2][2] and board[0][0] not in [None, 'draw']:
        return board[0][0]
    if board[0][2] == board[1][1] == board[2][0] and board[0][2] not in [None, 'draw']:
        return board[0][2]
    if all(cell is not None for row in board for cell in row):
        return 'draw'
    return None
