```mermaid
graph TD
    subgraph "End Users"
        UserA[Player 1]
        UserB[Player 2]
        UserC[Leaderboard Viewer]
    end

    subgraph "Client Applications"
        direction LR
        Browser[Web Browser]
        Desktop[Python Client]
        Android[Android App]
    end

    subgraph "Cloud Server Infrastructure (VPS)"
        direction TB

        subgraph "Firewall / Network Layer"
            direction LR
            Port80[Port 80: HTTP]
            Port5000[Port 5000: API]
            Port5556[Port 5556: TCP]
            Port8765[Port 8765: WebSocket]
        end
        
        Nginx[Nginx Web Server / Reverse Proxy]

        subgraph "Application Layer"
            direction LR
            GameServer["Multi-Game Server (server.py)"]
            APIServer["Leaderboard API (api_server.py)"]
        end

        Database[(SQLite Database<br>game_results.db)]
        
        subgraph GameServer
            direction TB
            RoomManager["Connection & Room Manager"]
            GameRoom1["Game Room 1"]
            GameRoom2["Game Room 2"]
            GameRoomN["..."]
        end
    end
    
    UserA --> Browser
    UserB --> Desktop
    UserB --> Android

    UserC -- "Views Leaderboard" --> Browser

    %% Data Flows
    Browser -- "HTTP for Web Page" --> Port80 --> Nginx
    Nginx -- "Serves HTML/CSS/JS" --> Browser
    
    Browser -- "HTTP GET /leaderboard" --> Port80 --> Nginx
    APIServer -- "Reads from" --> Database
    APIServer -- "Returns Leaderboard JSON" --> Nginx --> Browser
    Nginx -- "Proxies to" --> Port5000 --> APIServer

    Desktop -- "TCP Socket" --> Port5556 --> RoomManager
    Android -- "TCP Socket" --> Port5556 --> RoomManager
    Browser -- "WebSocket" --> Port8765 --> RoomManager
    
    RoomManager --> GameRoom1
    RoomManager --> GameRoom2
    
    GameRoom1 -- "Writes to" --> Database
    GameRoom2 -- "Writes to" --> Database

    %% Styling
    style Nginx fill:#188,stroke:#333,stroke-width:2px
    style GameServer fill:#388,stroke:#333,stroke-width:2px
    style APIServer fill:#588,stroke:#333,stroke-width:2px
    style Database fill:#788,stroke:#333,stroke-width:2px
```