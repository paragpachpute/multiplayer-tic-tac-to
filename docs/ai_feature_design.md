# Design Document: "Play vs. Computer" Feature

## 1. Overview

This document outlines the design and implementation plan for adding a new feature that allows a user to play Tic-Tac-Toe against a computer-controlled opponent. The goal is to provide a challenging single-player experience while ensuring the main game server remains responsive and scalable.

This plan covers the AI for the standard 3x3 game board and establishes a robust architectural pattern that can be extended to the Ultimate Tic-Tac-Toe mode in the future.

## 2. Feature Requirements

*   A user should be able to start a new game against an AI opponent from the lobby.
*   The AI opponent should play optimally, providing a genuine challenge (i.e., it should be unbeatable).
*   The addition of the AI should not introduce blocking or performance degradation to the existing multiplayer functionality.
*   The user experience should feel responsive, with the AI's moves appearing quickly after the user's move.

## 3. Proposed Architecture

To meet the requirements, we will implement a **server-side AI** that runs its calculations in a **separate process pool**. This approach keeps the AI logic centralized on the server while preventing the CPU-intensive calculations from blocking the main `asyncio` event loop.

### 3.1. Core Technology

*   **AI Algorithm:** The computer will use the **Minimax algorithm** to determine the optimal move. For a standard 3x3 Tic-Tac-Toe board, this algorithm is computationally fast but provides an unbeatable opponent.
*   **Concurrency Model:** We will use Python's `concurrent.futures.ProcessPoolExecutor`. This will create a pool of worker processes dedicated to running the AI calculations. The main `asyncio` server will hand off the Minimax calculation to this pool, allowing the main server thread to remain free to handle network I/O for all other games.

### 3.2. Detailed Flow

1.  **Initiation:** The user clicks a "Play vs. Computer" button in the web client's lobby.
2.  **Request:** The client sends a new `create_ai_game` WebSocket message to the server.
3.  **Game Room Creation:** The server creates a new, specialized `AIGameRoom` that is designed to handle one human player and a "virtual" AI player.
4.  **Human Move:** The user makes a move, which is sent to the server.
5.  **AI Calculation (Non-Blocking):**
    *   The `AIGameRoom` receives the human's move.
    *   It then requests the main `asyncio` event loop to run the blocking `find_best_move` function within the `ProcessPoolExecutor`.
    *   The `AIGameRoom` `await`s the result, yielding control back to the event loop so other server tasks can run.
6.  **AI Move:** Once the worker process returns the calculated best move, the `AIGameRoom` resumes. It updates the board state with the AI's move.
7.  **Response:** The server sends the final, updated `gameState` back to the client, containing both the human's and the AI's moves.

## 4. Implementation Tasks

The implementation will be broken down into the following discrete tasks:

### Task 1: Client-Side UI (Frontend)

*   **File:** `tic-tac-toe-web/index.html`
    *   Add a new "Play vs. Computer" button to the lobby.
*   **File:** `tic-tac-toe-web/script.js`
    *   Add an event listener for the new button.
    *   This listener will trigger the WebSocket connection and send the `create_ai_game` message.

### Task 2: Server-Side Protocol

*   **File:** `tic-tac-toe-server/server/protocol.py`
    *   Add a new `CREATE_AI_GAME` type to the `MessageType` enum to formally define the new message.

### Task 3: AI Logic Implementation

*   **File:** `tic-tac-toe-server/server/ai_logic.py` (New File)
    *   Implement the core Minimax algorithm in a function, e.g., `find_best_move(board)`.
    *   This function will be pure, stateless, and blocking (CPU-bound). It will take a board state and return the `(row, col)` of the best move.

### Task 4: Server Infrastructure for Concurrency

*   **File:** `tic-tac-toe-server/server/main.py`
    *   At server startup, initialize a `ProcessPoolExecutor`.
    *   Make this executor instance available to the game rooms.

### Task 5: AI Game Room

*   **File:** `tic-tac-toe-server/server/ai_game_room.py` (New File)
    *   Create the `AIGameRoom` class.
    *   It will manage the state for a single-player game against the AI.
    *   Its `handle_move` method will contain the core logic: update the board with the human move, call the AI logic using `loop.run_in_executor`, and then update the board with the AI's move.

### Task 6: Integration with Game Manager

*   **File:** `tic-tac-toe-server/server/main.py` (Message Handling)
    *   Update the main message handler to recognize the `create_ai_game` message.
    *   When this message is received, it will instantiate the new `AIGameRoom` instead of a standard `Game` room.

This structured approach ensures that all components are built and integrated correctly, resulting in a robust and performant "Play vs. Computer" feature.
