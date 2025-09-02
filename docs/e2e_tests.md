# End-to-End (E2E) Testing

This document outlines the end-to-end (E2E) testing setup for the Tic-Tac-Toe platform. The E2E tests are located in a separate, top-level directory named `tic-tac-toe-e2e-tests`.

## I. Framework and Tools

*   **Framework:** [Playwright](https://playwright.dev/)
*   **Language:** JavaScript (with Node.js)
*   **Test Runner:** Playwright Test

## II. Test Scenario

The primary test scenario, located in `tests/full_game.spec.js`, automates a complete user journey for a two-player game.

**Scenario Steps:**

1.  **Setup:** Two separate browser windows (contexts) are opened to simulate two different players, "Alice" and "Bob".
2.  **Player 1 (Alice) Creates Game:**
    *   Navigates to the web client.
    *   Enters her name.
    *   Clicks "Create New Game".
    *   The test extracts the unique Game ID from the UI.
3.  **Player 2 (Bob) Joins Game:**
    *   Navigates to the web client in the second browser window.
    *   Enters his name.
    *   Pastes the Game ID from Alice's session.
    *   Clicks "Join Game".
4.  **Gameplay:**
    *   The test waits for the game board to be visible and for the status to indicate it's Alice's turn.
    *   It then automates a series of clicks, alternating between Alice's and Bob's browser windows, to complete a game.
    *   The test waits for the "Your turn" status message before each move to ensure the application is ready.
5.  **Verification:**
    *   After the winning move is made, the test asserts that the status message in both browser windows correctly displays "Alice wins!".

## III. How to Run the Tests

### 1. Start the Servers

Before running the tests, all the backend and frontend servers must be running. A convenience script is provided to handle this.

From the `tic-tac-toe-e2e-tests` directory, run:

```bash
./start_servers.sh
```

This script will:
*   Install the Python dependencies for the server.
*   Start the API server in the background.
*   Start the real-time game server in the background.
*   Start the web client server in the background.

### 2. Execute the Tests

Once the servers are running, you can execute the Playwright test suite.

From the `tic-tac-toe-e2e-tests` directory, run:

```bash
npm test
```

This command will run all the tests in headless mode by default. The test results will be displayed in the terminal.

### 3. Stop the Servers

After testing is complete, you can stop all the background servers using the `kill` command provided in the output of the `start_servers.sh` script.
