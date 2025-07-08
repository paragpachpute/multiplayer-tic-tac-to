# Deployment Guide: Multiplayer Tic-Tac-Toe Platform

This document outlines the complete architecture and deployment process for the multiplayer Tic-Tac-Toe platform.

## I. Core Technologies & Services

This project is deployed using the following key third-party services:

*   **Virtual Private Server (VPS):** The entire backend application is hosted on a **DigitalOcean Droplet**.
*   **DNS & Proxy:** Domain Name System (DNS) and HTTPS/SSL termination are managed by **Cloudflare**.

## II. System Architecture Overview

The platform operates on a hybrid server model to efficiently handle different types of client communication.

### 1. Core Services

*   **Nginx:** A high-performance web server that acts as the main entry point and reverse proxy. It listens on the public port 80 and routes traffic internally.
*   **Game Server:** A Python `asyncio` application that manages all real-time game logic. It handles persistent connections from game clients.
*   **API Server:** A Python `Flask` application that serves stateless data, specifically the game leaderboard.
*   **SQLite:** A file-based database that stores game results.

### 2. Deployed File Structure

The project code is deployed on the server with the following structure:

*   `/root/multiplayer-tic-tac-to/`: The main project root cloned from Git.
    *   `server/`: The real-time game server modules.
    *   `api/`: The leaderboard API server module.
    *   `database/`: The database interaction module.
    *   `run_game_server.py`: The script to start the game server.
    *   `run_api_server.py`: The script to start the API server.
    *   `venv/`: The Python virtual environment containing all dependencies.
*   `/var/www/tic-tac-toe/`: The root directory for the static web client files (`index.html`, `style.css`, `script.js`).

## II. Connection Protocols and Ports

| Service         | Protocol      | Listens On (Internal) | Accessed Via (Public)                | Purpose                               |
|-----------------|---------------|-----------------------|--------------------------------------|---------------------------------------|
| Nginx           | HTTP / HTTPS  | Port 80               | `http://pparag.dev`                  | Main entry point, serves web client   |
| **Game Server** | **WebSocket** | `127.0.0.1:8765`      | `wss://pparag.dev/ws`                | Web Client Gameplay                   |
| **Game Server** | **TCP**       | `0.0.0.0:5556`        | `your_server_ip:5556`                | Native (Python/Android) Client Gameplay |
| **API Server**  | **HTTP**      | `127.0.0.1:5000`      | `https://pparag.dev/api/leaderboard` | Leaderboard Data                      |

## III. Server Configuration Files

### 1. Nginx Site Configuration

This file configures Nginx to act as a reverse proxy.

*   **Location:** `/etc/nginx/sites-available/tictactoe`
*   **Enabled via symlink:** `/etc/nginx/sites-enabled/tictactoe`

```nginx
server {
  listen 80;
  server_name pparag.dev www.pparag.dev;

  # Location for the static web client files
  location / {
    root /var/www/tic-tac-toe;
    try_files $uri $uri/ /index.html;
  }

  # Location for the API server
  location /api/ {
    proxy_pass http://143.198.107.112:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
  }

  # Location for the WebSocket game server
  # This is the endpoint your web client will connect to
  location /ws {
    proxy_pass http://143.198.107.112:8765;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

### 2. Game Server `systemd` Service

This file ensures the real-time game server runs continuously.

*   **Location:** `/etc/systemd/system/tictactoe-game.service`

```ini
[Unit]
Description=Tic Tac Toe Real-Time Game Server
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/multiplayer-tic-tac-to
ExecStart=/root/multiplayer-tic-tac-to/venv/bin/python run_game_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 3. API Server `systemd` Service

This file ensures the leaderboard API server runs continuously.

*   **Location:** `/etc/systemd/system/tictactoe-api.service`

```ini
[Unit]
Description=Tic Tac Toe Leaderboard API Server
After=network.target

[Service]
User=root
Group=root
WorkingDirectory=/root/multiplayer-tic-tac-to
ExecStart=/root/multiplayer-tic-tac-to/venv/bin/python run_api_server.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## IV. Management Commands

### Starting and Stopping Services

*   **Start all services:**
    ```bash
    sudo systemctl start tictactoe-game.service
    sudo systemctl start tictactoe-api.service
    sudo systemctl start nginx
    ```
*   **Stop all services:**
    ```bash
    sudo systemctl stop tictactoe-game.service
    sudo systemctl stop tictactoe-api.service
    sudo systemctl stop nginx
    ```
*   **Restart a service:**
    ```bash
    sudo systemctl restart tictactoe-game.service
    ```
*   **Apply changes to service files and restart:**
    ```bash
    sudo systemctl daemon-reload
    sudo systemctl restart tictactoe-api.service
    ```
*   **Apply changes to Nginx configuration:**
    ```bash
    sudo nginx -t && sudo systemctl restart nginx
    ```

### Checking Service Status and Logs

*   **Check status:**
    ```bash
    sudo systemctl status tictactoe-game.service
    sudo systemctl status tictactoe-api.service
    ```
*   **View live logs:**
    ```bash
    sudo journalctl -u tictactoe-game.service -f
    sudo journalctl -u tictactoe-api.service -f
    sudo tail -f /var/log/nginx/access.log
    ```