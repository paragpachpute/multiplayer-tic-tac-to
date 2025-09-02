# Proposed Testing Plan for Tic-Tac-Toe Platform

This document outlines a comprehensive, multi-layered testing strategy for the `tic-tac-toe-server` and `tic-tac-toe-web` applications. The plan follows the "Testing Pyramid" concept, emphasizing a strong base of unit tests, followed by integration tests, and capped with end-to-end (E2E) system tests.

---

### 1. `tic-tac-toe-server` (Backend Testing)

**Framework:** `pytest`
**Location:** A new `tests/` directory inside `tic-tac-toe-server`.

#### A. Unit Tests (Testing in Isolation)

**Method:** Use `pytest` to test pure logic. Mock external dependencies like database connections and network sockets.

**Test Cases:**

*   **`tests/test_database.py`:**
    *   **Leaderboard Calculation:**
        *   Use an in-memory SQLite database.
        *   Seed it with mock game results (wins, draws).
        *   Call `get_leaderboard()` and assert that scores (win=3, draw=1) and player ranks are calculated correctly.
    *   **Result Recording:**
        *   Assert that `record_game_result()` correctly inserts data into the test database.

*   **`tests/test_game_room.py`:**
    *   **Player Management:**
        *   Assert `add_client` assigns 'X' to the first player and 'O' to the second.
        *   Assert a third player is rejected.
    *   **Game Logic:**
        *   Test that `handle_move()` correctly updates the board and switches the current player.
        *   Test that invalid moves (on an occupied cell, out of turn) are ignored.
    *   **Win/Draw Conditions:**
        *   Write tests for all 8 win conditions (rows, columns, diagonals).
        *   Write a test for a full-board draw scenario.
    *   **Game Restart:**
        *   Assert `restart_game()` resets the board, `current_player`, and `game_over` status.

#### B. Integration Tests (Testing Modules Together)

**Method:** Use `pytest` with fewer mocks to test the interaction between internal modules and the communication protocol.

**Test Cases:**

*   **API Server (`/leaderboard`):**
    *   Start a test instance of the Flask `app`.
    *   Populate a test database programmatically.
    *   Use a test client (e.g., `app.test_client()`) to make a real HTTP GET request to `/leaderboard`.
    *   Assert the HTTP response is `200 OK` and the JSON body is correct.

*   **`tests/integration/test_full_game_flow.py`:**
    *   Simulate a full game by calling the `handle_message` function directly with JSON payloads.
    *   **Scenario:**
        1.  Send `create_game` message; assert correct response.
        2.  Send `join_game` message; assert success.
        3.  Send a sequence of `move` messages to complete a game.
        4.  After each move, check the broadcasted `gameState` for accuracy.
        5.  After the winning move, assert `game_over` is true and the winner is correct.

---

### 2. `tic-tac-toe-web` (Frontend Testing)

**Frameworks:** **Vitest** or **Jest** with **Testing Library**.
**Location:** A new `tests/` directory inside `tic-tac-toe-web`.

**Test Cases:**

*   **UI Rendering:**
    *   Assert the lobby is rendered correctly on initial load.
    *   Assert the game board is rendered correctly based on a mock `gameState` message.
*   **User Interaction (with mocked WebSockets):**
    *   Simulate a user typing a name and clicking "Create Game"; verify the correct WebSocket message is constructed.
    *   Simulate a click on a board cell; verify the correct `move` message is sent.
    *   Simulate receiving a `gameState` where it's not the player's turn; verify cells are disabled.
*   **Leaderboard Modal:**
    *   Simulate a click on the "Leaderboard" button.
    *   Mock the `fetch` API call and provide sample data.
    *   Assert the modal appears and displays the data in a table.

---

### 3. End-to-End (E2E) System Testing

**Framework:** **Cypress** or **Playwright**.
**Location:** A new top-level `e2e-tests/` directory.

**Method:** Automate a real user journey across the entire live system. The test script will manage starting/stopping all servers and controlling browser windows.

**Test Scenario: `full_game.spec.js`**

1.  **Setup:**
    *   Start the backend API and Game servers.
    *   Start the frontend web server.
    *   Ensure the database is in a clean state.
2.  **Execution:**
    *   **Player 1 (Alice):**
        *   Open a browser to the web client.
        *   Enter "Alice" and click "Create New Game".
        *   Extract and save the Game ID.
    *   **Player 2 (Bob):**
        *   Open a **second browser window**.
        *   Enter "Bob", paste the Game ID, and click "Join Game".
    *   **Gameplay:**
        *   Automate a series of clicks back and forth between the two browser windows until one player wins.
        *   After each move, assert that the board and status text have updated correctly in *both* windows.
    *   **Verification:**
        *   Assert the final "wins!" message is displayed.
        *   Click the "Leaderboard" button and assert that the winner's score has been updated correctly.
3.  **Teardown:**
    *   Shut down all servers.
