from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from enum import Enum

class MessageType(str, Enum):
    """Defines the valid types for server-client communication."""
    GAME_STATE = "gameState"
    GAME_CREATED = "game_created"
    GAME_JOINED = "game_joined"
    ERROR = "error"
    CREATE_GAME = "create_game"
    JOIN_GAME = "join_game"
    MOVE = "move"
    RESTART = "restart"

# --- Data Structures for Game State ---
@dataclass
class GameState:
    board: List[List[Optional[str]]]
    current_player: str
    game_over: bool
    winner: Optional[str]
    player_names: Dict[str, Optional[str]]

# --- Specific, Standalone Response Types ---
# No base class is used to avoid the default argument inheritance issue.
@dataclass
class GameStateResponse:
    state: GameState
    type: str = MessageType.GAME_STATE

@dataclass
class GameCreatedResponse:
    game_id: str
    player_symbol: str
    type: str = MessageType.GAME_CREATED

@dataclass
class GameJoinedResponse:
    game_id: str
    player_symbol: str
    type: str = MessageType.GAME_JOINED

@dataclass
class ErrorResponse:
    message: str
    type: str = MessageType.ERROR

def to_dict(response) -> Dict:
    """Converts any of the response dataclasses to a dictionary."""
    return asdict(response)