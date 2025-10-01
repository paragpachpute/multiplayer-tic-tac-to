# Multiplayer Tic-Tac-Toe - Backend Servers

This directory contains the complete backend for the multiplayer Tic-Tac-Toe platform, including the real-time game server and the leaderboard API.

## Project Structure

*   `/api`: Contains the Flask REST API server for the leaderboard.
*   `/database`: Contains the database interaction module and the SQLite database file.
*   `/docs`: Contains architecture and deployment documentation.
*   `/server`: Contains the core real-time `asyncio` game server logic.
*   `run_api_server.py`: The script to start the API server.
*   `run_game_server.py`: The script to start the main game server.

---

## How to Run Locally for Development

To run the backend on your local machine, you will need **two separate terminal windows**.

### Prerequisites

Ensure you have all the Python dependencies installed:
```bash
# (If you have a virtual environment, activate it first: source venv/bin/activate)
pip install -r requirements.txt
```

### Terminal 1: Start the API Server

This server handles requests for the leaderboard.

1.  From this project's root directory (`tic-tac-toe-server`), run the API server script:
    ```bash
    python3 run_api_server.py
    ```
    *This will start the Flask server on `http://localhost:5000`.*

### Terminal 2: Start the Real-Time Game Server

This server handles the actual gameplay for all clients.

1.  From this project's root directory (`tic-tac-toe-server`), run the game server script:
    ```bash
    python3 run_game_server.py
    ```
    *This will start the asyncio server, listening for TCP connections on port `5556` and WebSocket connections on port `8765`.*

Both backend servers are now running and ready to accept connections from any of the game clients.

---

## Game State Management

### Grace Period for Reconnections

The server implements a grace period system to handle temporary disconnections:

- **Grace Period Duration**: 10 minutes (configurable via `GAME_GRACE_PERIOD_SECONDS` environment variable)
- **Automatic Cleanup**: Games with no connected players are kept alive for the grace period to allow reconnections
- **Smart Cancellation**: Grace period is automatically cancelled when players reconnect or new players join
- **Applies to**: Both standard and Ultimate Tic-Tac-Toe multiplayer games

This ensures that temporary disconnections (like app switching on mobile) don't immediately destroy game sessions, providing a better user experience when sharing game IDs with friends.
