import sys
import os

# Add the project root to the Python path to allow for absolute imports
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from api.api_server import app
from server.config import HOST, API_PORT

if __name__ == "__main__":
    print(f"Starting the Tic-Tac-Toe API Server on http://{HOST}:{API_PORT}")
    # The database is initialized by the main game server,
    # but for standalone testing, you might add database.initialize_database() here.
    app.run(host=HOST, port=API_PORT)
