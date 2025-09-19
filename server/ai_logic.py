"""
This module contains the AI logic for the Tic-Tac-Toe game.
It uses the Minimax algorithm to determine the best possible move.
"""

import math

def find_best_move(board):
    """
    Finds the best possible move for the AI player ('O').
    The board is a 3x3 list of lists. 'X' is the human, 'O' is the AI.
    Returns a tuple of (row, col).
    """
    best_val = -math.inf
    best_move = (-1, -1)

    for i in range(3):
        for j in range(3):
            if board[i][j] is None:
                board[i][j] = 'O'
                move_val = minimax(board, 0, False)
                board[i][j] = None  # Undo the move

                if move_val > best_val:
                    best_move = (i, j)
                    best_val = move_val
    
    return best_move

def minimax(board, depth, is_maximizer):
    """
    The core Minimax algorithm.
    """
    score = evaluate(board)

    if score == 10:
        return score - depth
    if score == -10:
        return score + depth
    if not any(None in row for row in board):
        return 0

    if is_maximizer:
        best = -math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    board[i][j] = 'O'
                    best = max(best, minimax(board, depth + 1, not is_maximizer))
                    board[i][j] = None
        return best
    else: # Minimizer
        best = math.inf
        for i in range(3):
            for j in range(3):
                if board[i][j] is None:
                    board[i][j] = 'X'
                    best = min(best, minimax(board, depth + 1, not is_maximizer))
                    board[i][j] = None
        return best

def evaluate(b):
    """
    Evaluates the board state from the perspective of the AI ('O').
    Returns +10 for an AI win, -10 for a human win, and 0 otherwise.
    """
    # Check rows for a win
    for i in range(3):
        if b[i][0] == b[i][1] == b[i][2]:
            if b[i][0] == 'O': return 10
            if b[i][0] == 'X': return -10
    
    # Check columns for a win
    for i in range(3):
        if b[0][i] == b[1][i] == b[2][i]:
            if b[0][i] == 'O': return 10
            if b[0][i] == 'X': return -10

    # Check diagonals for a win
    if b[0][0] == b[1][1] == b[2][2]:
        if b[0][0] == 'O': return 10
        if b[0][0] == 'X': return -10
    
    if b[0][2] == b[1][1] == b[2][0]:
        if b[0][2] == 'O': return 10
        if b[0][2] == 'X': return -10

    return 0
