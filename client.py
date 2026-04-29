import pygame
import socket
import threading
import pickle
import sys

from ui import *


# ---------------- GAME STATE ----------------
class GameState:
    def __init__(self):
        self.board = [[0 for _ in range(7)] for _ in range(6)]
        self.turn = 1
        self.game_over = False
        self.winner = None
        self.ready = False


# ---------------- NETWORK ----------------
class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '172.16.141.39'
        self.port = 5555

        self.player_id = None
        self.game_state = None
        self.rooms = {}
        self.app_state = "LOBBY"

    def connect(self):
        try:
            self.client.connect((self.host, self.port))
            threading.Thread(target=self.receive, daemon=True).start()
            self.send({"type": "LIST"})
            return True
        except:
            return False

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
        except:
            pass

    def receive(self):
        while True:
            try:
                data = self.client.recv(4096)
                if not data:
                    break

                msg = pickle.loads(data)

                if msg["type"] == "LIST":
                    self.rooms = msg["rooms"]

                elif msg["type"] == "WAITING":
                    self.player_id = msg["player_id"]
                    self.app_state = "WAITING"

                elif msg["type"] == "GAME_START":
                    self.player_id = msg["player_id"]
                    self.app_state = "GAME"

                elif msg["type"] == "STATE":
                    self.game_state = msg["state"]

                    if self.game_state.ready:
                        self.app_state = "GAME"

            except:
                break

        # 🔥 ADDED: SERVER DISCONNECTED HANDLING
        self.app_state = "QUIT"
        try:
            self.client.close()
        except:
            pass


# ---------------- LOBBY ----------------
def lobby_screen(screen, net, font, title_font):
    input_text = ""
    active = False

    input_rect = pygame.Rect(WIDTH//2 - 150, 150, 300, 50)

    create_btn = UI.create_room_button(font)
    refresh_btn = UI.refresh_button(font)

    while net.app_state == "LOBBY":
        screen.fill(Theme.BG)
        mouse = pygame.mouse.get_pos()

        screen.blit(title_font.render("MULTIPLAYER", True, Theme.TEXT),
                    (WIDTH//2 - 180, 50))

        pygame.draw.rect(screen,
                         Theme.BTN_HOVER if active else Theme.BTN,
                         input_rect, border_radius=10)

        screen.blit(font.render(input_text, True, Theme.TEXT),
                    (input_rect.x + 10, input_rect.y + 10))

        create_btn.draw(screen, mouse)
        refresh_btn.draw(screen, mouse)

        y = 300
        for name, count in net.rooms.items():
            r = pygame.Rect(WIDTH//2 - 200, y, 400, 45)

            pygame.draw.rect(screen,
                             Theme.BTN_HOVER if r.collidepoint(mouse) else Theme.BTN,
                             r, border_radius=5)

            screen.blit(font.render(f"{name} ({count}/2)", True, Theme.TEXT),
                        (r.x + 10, r.y + 10))

            y += 55

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.MOUSEBUTTONDOWN:
                active = input_rect.collidepoint(event.pos)

                if create_btn.clicked(event, mouse) and input_text:
                    net.send({"type": "CREATE", "name": input_text})

                if refresh_btn.clicked(event, mouse):
                    net.send({"type": "LIST"})

                y = 300
                for name in net.rooms:
                    if pygame.Rect(WIDTH//2 - 200, y, 400, 45).collidepoint(event.pos):
                        net.send({"type": "JOIN", "name": name})
                    y += 55

            if event.type == pygame.KEYDOWN and active:
                if event.key == pygame.K_BACKSPACE:
                    input_text = input_text[:-1]
                elif len(input_text) < 12:
                    input_text += event.unicode

        pygame.display.update()

    return net.app_state


# ---------------- GAME ----------------
def play_game(screen, net, font, title_font):
    last_board = [[0]*7 for _ in range(6)]

    leave_btn = UI.leave_button(font)
    play_again_btn = UI.play_again_button(font)
    quit_btn = UI.quit_button(font)

    local_game_over = False

    while net.app_state == "GAME":
        mouse = pygame.mouse.get_pos()
        screen.fill(Theme.BG)

        if net.game_state:

            for r in range(6):
                for c in range(7):
                    if net.game_state.board[r][c] != last_board[r][c]:
                        animate_drop(screen, last_board, c, r,
                                     net.game_state.board[r][c])
                        last_board[r][c] = net.game_state.board[r][c]

            pygame.draw.rect(screen, (35, 37, 54), (0, 0, WIDTH, 60))
            leave_btn.draw(screen, mouse)

            if net.game_state.game_over:
                local_game_over = True

            msg = "YOUR TURN" if net.game_state.turn == net.player_id else "OPPONENT TURN"
            color = Theme.P1 if net.game_state.turn == 1 else Theme.P2

            screen.blit(font.render(msg, True, color),
                        (WIDTH//2 - 80, 20))

            draw_board(screen, net.game_state.board)

            if not net.game_state.game_over and net.game_state.turn == net.player_id:
                col = mouse[0] // CELL_SIZE
                draw_token(screen, net.player_id,
                           int(col * CELL_SIZE + CELL_SIZE / 2),
                           TOP_MARGIN - 50)

        # ---------------- OVERLAY ----------------
        if local_game_over and net.game_state:
            draw_overlay(
                screen,
                "DRAW!" if net.game_state.winner == 0 else f"PLAYER {net.game_state.winner} WINS!",
                title_font,
                Theme.TEXT if net.game_state.winner == 0 else (Theme.P1 if net.game_state.winner == 1 else Theme.P2)
            )

            play_again_btn.draw(screen, mouse)
            quit_btn.draw(screen, mouse)

        # ---------------- EVENTS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if leave_btn.clicked(event, mouse):
                net.send({"type": "LEAVE"})
                net.app_state = "LOBBY"
                return "LOBBY"

            if event.type == pygame.MOUSEBUTTONDOWN and not local_game_over:
                if net.game_state and not net.game_state.game_over:
                    if net.game_state.turn == net.player_id:
                        net.send({"type": "MOVE",
                                  "col": event.pos[0] // CELL_SIZE})

            if local_game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_btn.clicked(event, mouse):
                    net.send({"type": "RESET"})
                    local_game_over = False
                    last_board = [[0]*7 for _ in range(6)]

                if quit_btn.clicked(event, mouse):
                    net.send({"type": "LEAVE"})
                    net.app_state = "LOBBY"
                    return "LOBBY"

        pygame.display.update()

    return net.app_state


# ---------------- MAIN ----------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    font = Fonts.small()
    title_font = Fonts.title()

    net = Network()
    if not net.connect():
        return

    state = "LOBBY"

    while state != "QUIT":

        # 🔥 ADDED: server crash detection
        if net.app_state == "QUIT":
            state = "QUIT"
            break

        if state == "LOBBY":
            state = lobby_screen(screen, net, font, title_font)

        elif state == "WAITING":
            screen.fill(Theme.BG)
            screen.blit(font.render("Waiting...", True, Theme.TEXT),
                        (WIDTH//2 - 60, HEIGHT//2))
            pygame.display.update()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    state = "QUIT"

            if net.app_state == "GAME":
                state = "GAME"

        elif state == "GAME":
            state = play_game(screen, net, font, title_font)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()