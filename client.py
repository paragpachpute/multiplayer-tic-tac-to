import pygame
import sys
import socket
import json
import threading

# --- Constants ---
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
LINE_COLOR = (0, 0, 0)
WIDTH, HEIGHT = 600, 600
ROWS, COLS = 3, 3
SQUARE_SIZE = WIDTH // COLS

# --- Game State Variables ---
board = [[None for _ in range(COLS)] for _ in range(ROWS)]
current_player = "X"
game_over = False
winner = None
player_symbol = None
player_names = {"X": None, "O": None}
game_id = None
status_message = "Connecting..."

# --- Pygame Setup ---
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Tic Tac Toe")

def draw_grid():
    for i in range(1, ROWS):
        pygame.draw.line(screen, LINE_COLOR, (0, i * SQUARE_SIZE), (WIDTH, i * SQUARE_SIZE), 3)
        pygame.draw.line(screen, LINE_COLOR, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, HEIGHT), 3)

def draw_symbols():
    for row in range(ROWS):
        for col in range(COLS):
            if board[row][col] == "X":
                x_pos, y_pos = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
                pygame.draw.line(screen, BLACK, (x_pos - 40, y_pos - 40), (x_pos + 40, y_pos + 40), 4)
                pygame.draw.line(screen, BLACK, (x_pos + 40, y_pos - 40), (x_pos - 40, y_pos + 40), 4)
            elif board[row][col] == "O":
                x_pos, y_pos = col * SQUARE_SIZE + SQUARE_SIZE // 2, row * SQUARE_SIZE + SQUARE_SIZE // 2
                pygame.draw.circle(screen, BLACK, (x_pos, y_pos), 40, 4)

def update_status_message():
    global status_message
    if game_over:
        winner_name = player_names.get(winner)
        status_message = f"{winner_name} wins!" if winner else "It's a draw!"
    else:
        current_name = player_names.get(current_player)
        if not current_name:
             status_message = "Waiting for opponent..."
        else:
            status_message = "Your turn" if player_symbol == current_player else f"{current_name}'s turn"

def update_state(state):
    global board, current_player, game_over, winner, player_names
    board = state['board']
    current_player = state['current_player']
    game_over = state['game_over']
    winner = state['winner']
    player_names = state.get('player_names', {})
    update_status_message()

def receive_messages(socket_file):
    global game_id, player_symbol, status_message
    while True:
        try:
            data = socket_file.readline()
            if not data: break
            
            message = json.loads(data)
            msg_type = message.get('type')

            if msg_type == 'game_created':
                game_id = message['game_id']
                player_symbol = message['player_symbol']
                print(f"Game created! Your ID is: {game_id}")
                status_message = f"Game ID: {game_id}. Waiting for opponent..."
                pygame.display.set_caption(f"Tic Tac Toe - Game {game_id} - Player {player_symbol}")
            elif msg_type == 'game_joined':
                game_id = message['game_id']
                player_symbol = message['player_symbol']
                print(f"Successfully joined game {game_id} as Player {player_symbol}")
                pygame.display.set_caption(f"Tic Tac Toe - Game {game_id} - Player {player_symbol}")
            elif msg_type == 'gameState':
                update_state(message['state'])
            elif msg_type == 'error':
                status_message = f"Error: {message['message']}"
                print(status_message)

        except (IOError, json.JSONDecodeError):
            print("Connection to server lost.")
            status_message = "Connection lost."
            break

def main():
    # --- Lobby ---
    name = input("Enter your name: ")
    choice = ""
    while choice not in ["1", "2"]:
        choice = input("1. Create New Game\n2. Join Game\nEnter choice (1 or 2): ")

    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('127.0.0.1', 5556))
        socket_file = client_socket.makefile('rw')

        if choice == "1":
            message = {"type": "create_game", "name": name}
        else:
            join_id = input("Enter Game ID to join: ").upper()
            message = {"type": "join_game", "name": name, "game_id": join_id}
        
        socket_file.write(json.dumps(message) + '\n')
        socket_file.flush()

    except Exception as e:
        print(f"Failed to connect to server: {e}")
        sys.exit()

    # --- Start Game ---
    pygame.init()
    receive_thread = threading.Thread(target=receive_messages, args=(socket_file,), daemon=True)
    receive_thread.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if not game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if player_symbol == current_player:
                    row, col = event.pos[1] // SQUARE_SIZE, event.pos[0] // SQUARE_SIZE
                    move = {"type": "move", "game_id": game_id, "row": row, "col": col}
                    socket_file.write(json.dumps(move) + '\n')
                    socket_file.flush()

            if game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                restart = {"type": "restart", "game_id": game_id}
                socket_file.write(json.dumps(restart) + '\n')
                socket_file.flush()

        # --- Drawing ---
        screen.fill(WHITE)
        draw_grid()
        draw_symbols()

        font = pygame.font.Font(None, 48)
        status_text = font.render(status_message, True, BLACK)
        status_rect = status_text.get_rect(center=(WIDTH/2, 25))
        screen.blit(status_text, status_rect)

        if game_over:
            font = pygame.font.Font(None, 48)
            restart_text = font.render("Press 'R' to restart", True, BLUE)
            restart_rect = restart_text.get_rect(center=(WIDTH/2, HEIGHT - 50))
            screen.blit(restart_text, restart_rect)

        pygame.display.update()

if __name__ == "__main__":
    main()
