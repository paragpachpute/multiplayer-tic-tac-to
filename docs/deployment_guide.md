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

*   `/root/multiplayer-tic-tac-to/`: The main project root for the backend servers, cloned from Git.
    *   `server/`: The real-time game server modules.
    *   `api/`: The leaderboard API server module.
    *   `database/`: The database interaction module.
    *   `run_game_server.py`: The script to start the game server.
    *   `run_api_server.py`: The script to start the API server.
    *   `venv/`: The Python virtual environment containing all dependencies.
*   `/var/www/html/`: The root directory for the main portfolio landing page.
*   `/var/www/ttt/`: The root directory for the Tic-Tac-Toe web client, cloned from its own Git repository.

## II. Connection Protocols and Ports

| Service         | Protocol      | Listens On (Internal) | Accessed Via (Public)                  | Purpose                               |
|-----------------|---------------|-----------------------|----------------------------------------|---------------------------------------|
| Nginx           | HTTP / HTTPS  | Port 80               | `http://pparag.dev`                    | Main entry point, serves landing page |
| **Game Server** | **WebSocket** | `127.0.0.1:8765`      | `wss://pparag.dev/ttt/ws`              | Web Client Gameplay                   |
| **Game Server** | **TCP**       | `0.0.0.0:5556`        | `your_server_ip:5556`                  | Native (Python/Android) Client Gameplay |
| **API Server**  | **HTTP**      | `127.0.0.1:5000`      | `https://pparag.dev/ttt/api/leaderboard` | Leaderboard Data                      |

## III. Server Configuration Files

### 1. Nginx Site Configuration

This file configures Nginx to act as a reverse proxy.

*   **Location:** `/etc/nginx/sites-available/tictactoe`
*   **Enabled via symlink:** `/etc/nginx/sites-enabled/tictactoe`

```nginx
server {
  listen 80;
  server_name pparag.dev www.pparag.dev;

  # Change 1: The root location now points to the new landing page directory.
  location / {
    root /var/www/html;
    try_files $uri $uri/ /index.html;
  }

  # Change 2: A new location block is added for the Tic-Tac-Toe app.
  # It uses 'alias' to serve files from a different directory.
  location /ttt/ {
    alias /var/www/ttt/;
    try_files $uri $uri/ /index.html;
  }

  # Change 3: The API location is updated to match the new path.
  # The proxy_pass URL is unchanged and will work correctly.
  location /ttt/api/ {
    proxy_pass http://143.198.107.112:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_redirect off;
  }

  # Change 4: The WebSocket location is updated to match the new path.
  location /ttt/ws {
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