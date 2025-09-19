from dataclasses import dataclass, asdict
from typing import Optional, Dict, List
from enum import Enum

class MessageType(str, Enum):
    """Defines the valid types for server-client communication."""
    # Server-to-client
    GAME_STATE = "gameState"
    GAME_CREATED = "game_created"
    GAME_JOINED = "game_joined"
    ERROR = "error"
    
    # Client-to-server
    CREATE_GAME = "create_game"
    CREATE_AI_GAME = "create_ai_game"
    JOIN_GAME = "join_game"
    MOVE = "move"
    RESTART = "restart"
    RECONNECT = "reconnect" # New


# --- Data Structures for Game State ---
@dataclass
class GameState:
    board: Optional[List[List[Optional[str]]]]
    current_player: str
    game_over: bool
    winner: Optional[str]
    player_names: Dict[str, Optional[str]]
    # Fields for Ultimate Tic-Tac-Toe
    micro_boards: Optional[List[List[List[Optional[str]]]]] = None
    macro_board: Optional[List[List[Optional[str]]]] = None
    active_micro_board_coords: Optional[List[int]] = None

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