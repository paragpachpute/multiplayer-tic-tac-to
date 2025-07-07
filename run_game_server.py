import asyncio
import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from server.main import main_async

if __name__ == "__main__":
    try:
        print("Starting the Tic-Tac-Toe Game Server...")
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("Game Server shutting down.")
