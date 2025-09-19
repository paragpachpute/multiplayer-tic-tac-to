# Design Document: Game Timer Feature

## 1. Overview

This document outlines the design and implementation plan for adding a per-player game timer to both Standard and Ultimate Tic-Tac-Toe. Each player will have a personal "time bank" that counts down only during their turn. If a player's time bank runs out, they forfeit the game.

The primary architectural goal is to ensure the timer is **server-authoritative** to prevent any client-side manipulation.

## 2. Feature Requirements

*   Each player will have their own timer.
*   The timer will only count down during that player's active turn.
*   The initial time bank will be:
    *   **Standard Game:** 1 minute (60 seconds) per player.
    *   **Ultimate Game:** 10 minutes (600 seconds) per player.
*   If a player's timer reaches zero, they lose the game.
*   The timer state must be managed by the server; the client's display is for visual purposes only.
*   Both players should be able to see both their own and their opponent's remaining time.

## 3. Proposed Architecture

We will implement the timer using a **Timestamp Subtraction Method**. This is a highly efficient, stateless (between moves), and robust approach that ensures the server remains the single source of truth for timekeeping.

### 3.1. Core Logic

1.  **Initialization:** When a game room is created, two new variables will be added to the room's state: `player_x_time_bank` and `player_o_time_bank`, initialized to the appropriate time in seconds based on the game mode.
2.  **Turn Start:** When the game transitions to a player's turn (e.g., Player X), the server will record the current system timestamp in a new variable, `current_turn_start_time`.
3.  **State Broadcast:** The `gameState` message sent to the clients will be augmented to include the current time bank for both players. The client's JavaScript will use this information to run a purely visual countdown timer.
4.  **Move Reception:** When the server receives a `move` message from the active player (Player X), it will:
    a.  Record the move reception time: `move_received_time = now()`.
    b.  Calculate the duration of the turn: `time_spent = move_received_time - current_turn_start_time`.
    c.  Subtract this duration from the player's time bank: `player_x_time_bank -= time_spent`.
    d.  Check for a timeout. If `player_x_time_bank` is now less than or equal to zero, the server will immediately end the game, declaring the other player the winner.
5.  **Turn Transition:** If the game is not over, the server will update the `current_turn_start_time` to the current time for the next player (Player O) and broadcast the new state.

This method ensures that network latency is implicitly accounted for and that the server's timekeeping is authoritative.

## 4. Implementation Tasks

The implementation will be broken down into the following discrete tasks:

### Task 1: Server-Side State Management

*   **Files:** `tic-tac-toe-server/server/game_room.py` and `tic-tac-toe-server/server/ultimate_game_room.py`
    *   In the `__init__` method of both classes, add the `player_x_time_bank` and `player_o_time_bank` variables, initializing them to 60 or 600 based on the game mode.
    *   Add a `current_turn_start_time` variable, initialized to `None`.
    *   When the game starts (i.e., when the second player joins), set `current_turn_start_time` to the current time.
*   **File:** `tic-tac-toe-server/server/protocol.py`
    *   Update the `GameState` dataclass to include two new optional fields: `player_x_time` and `player_o_time`.

### Task 2: Server-Side Timer Logic

*   **Files:** `game_room.py` and `ultimate_game_room.py`
    *   In the `handle_move` method of both classes:
        *   Implement the timestamp subtraction logic as described in section 3.1.
        *   Add the timeout check. If a player's time is depleted, set `self.game_over = True`, set the winner to the opposing player, and broadcast the final state.
        *   After a valid move, update `current_turn_start_time` before broadcasting the new state.
    *   In the `broadcast_state` method, ensure the new time bank values are included in the `GameState` object being sent to the clients.

### Task 3: Client-Side UI (Display)

*   **File:** `tic-tac-toe-web/index.html`
    *   Add two new elements to the game screen to display the timers for Player X and Player O. These should be clearly labeled.
*   **File:** `tic-tac-toe-web/style.css`
    *   Add styling for the new timer display elements to ensure they are well-integrated into the UI.

### Task 4: Client-Side Timer Logic (Visual Countdown)

*   **File:** `tic-tac-toe-web/script.js`
    *   In the `updateBoard` function, use the new time bank data from the `gameState` message to update the text of the timer display elements.
    *   Implement a `setInterval` function that visually counts down the timer for the *current* player. This timer is for display only.
    *   This `setInterval` should be cleared and reset every time a new `gameState` message is received to ensure it stays in sync with the server's authoritative time.
