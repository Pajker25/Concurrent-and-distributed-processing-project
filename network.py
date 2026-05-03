# Network client logic, game state synchronization, and online UI screens

import pygame
import socket
import threading
import pickle
from ui import Theme, UI, Button, draw_board, draw_token, animate_drop, draw_overlay, draw_chat_history, WIDTH, HEIGHT, CELL_SIZE, TOP_MARGIN
from game_logic import GameLogic, GameState


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = '127.0.0.1'
        self.port = 5555
        self.player_id = None
        self.game_state = None
        self.rooms = {}
        self.app_state = "LOBBY"
        
        self.nickname = "Player"
        self.messages = []
        self.players = {1: "Player 1", 2: "Player 2"}

    def connect(self):
        try:
            self.client.connect((self.host, self.port))
            threading.Thread(target=self.receive, daemon=True).start()
            self.send({"type": "LIST"})
            return True
        except Exception:
            return False

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
        except Exception:
            pass

    def reset_game_data(self):
        self.game_state = None
        self.messages = []
        self.app_state = "LOBBY"

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
                    self.players = msg.get("players", self.players)
                    self.app_state = "GAME"
                elif msg["type"] == "STATE":
                    self.game_state = msg["state"]
                    if self.game_state.ready:
                        self.app_state = "GAME"
                elif msg["type"] == "CHAT":
                    self.messages.append({
                        "text": msg["msg"], 
                        "time": pygame.time.get_ticks()
                    })
                    if len(self.messages) > 10:
                        self.messages.pop(0)
            except Exception:
                break

        self.app_state = "QUIT"
        try:
            self.client.close()
        except Exception:
            pass

def lobby_screen(screen, net, font, title_font):
    room_text = ""
    nick_text = net.nickname
    active_room = False
    active_nick = False

    room_rect = pygame.Rect(WIDTH//2 - 150, 120, 300, 45)
    nick_rect = pygame.Rect(WIDTH//2 - 150, 180, 300, 45)

    create_btn = Button(WIDTH//2 - 100, 250, 200, 50, "Create Room", font)
    refresh_btn = UI.refresh_button(font)
    back_btn = Button(10, 10, 100, 40, "Back", font)

    while net.app_state == "LOBBY":
        screen.fill(Theme.BG)
        mouse = pygame.mouse.get_pos()
        
        pygame.draw.rect(screen, Theme.BTN_HOVER if active_room else Theme.BTN, room_rect, border_radius=10)
        pygame.draw.rect(screen, Theme.BTN_HOVER if active_nick else Theme.BTN, nick_rect, border_radius=10)
        
        screen.blit(font.render(f"Room: {room_text}", True, Theme.TEXT), (room_rect.x + 10, room_rect.y + 10))
        screen.blit(font.render(f"Nick: {nick_text}", True, Theme.TEXT), (nick_rect.x + 10, nick_rect.y + 10))

        create_btn.draw(screen, mouse)
        refresh_btn.draw(screen, mouse)
        back_btn.draw(screen, mouse)

        y = 330
        for name, count in net.rooms.items():
            r = pygame.Rect(WIDTH//2 - 200, y, 400, 45)
            pygame.draw.rect(screen, Theme.BTN_HOVER if r.collidepoint(mouse) else Theme.BTN, r, border_radius=5)
            screen.blit(font.render(f"{name} ({count}/2)", True, Theme.TEXT), (r.x + 10, r.y + 10))
            y += 55

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.MOUSEBUTTONDOWN:
                active_room = room_rect.collidepoint(event.pos)
                active_nick = nick_rect.collidepoint(event.pos)

                if back_btn.clicked(event, mouse):
                    return "MAIN_MENU"

                if create_btn.clicked(event, mouse) and room_text:
                    net.nickname = nick_text
                    net.send({"type": "CREATE", "name": room_text, "nick": nick_text})

                if refresh_btn.clicked(event, mouse):
                    net.send({"type": "LIST"})

                y = 330
                for name in net.rooms:
                    if pygame.Rect(WIDTH//2 - 200, y, 400, 45).collidepoint(event.pos):
                        net.nickname = nick_text
                        net.send({"type": "JOIN", "name": name, "nick": nick_text})
                    y += 55

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if active_room:
                    if event.key == pygame.K_BACKSPACE: room_text = room_text[:-1]
                    elif len(room_text) < 12: room_text += event.unicode
                if active_nick:
                    if event.key == pygame.K_BACKSPACE: nick_text = nick_text[:-1]
                    elif len(nick_text) < 12: nick_text += event.unicode

        pygame.display.update()
    return net.app_state

def waiting_screen(screen, net, font, leave_btn):
    screen.fill(Theme.BG)
    mouse = pygame.mouse.get_pos()
    screen.blit(font.render("Waiting for opponent...", True, Theme.TEXT), (WIDTH//2 - 130, HEIGHT//2))
    leave_btn.draw(screen, mouse)
    pygame.display.update()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            return "QUIT"
        if e.type == pygame.MOUSEBUTTONDOWN:
            if leave_btn.clicked(e, mouse):
                net.send({"type": "LEAVE"})
                net.reset_game_data()
                return "LOBBY"

    return net.app_state

def draw_chat(screen, net, font):
    current_time = pygame.time.get_ticks()
    active_messages = [m for m in net.messages if current_time - m["time"] < 7000]
    start_y = HEIGHT - 100 - (len(active_messages) * 25)
    
    for m in active_messages:
        age = current_time - m["time"]
        alpha = 255
        
        if age > 5000:
            alpha = max(0, 255 - int(((age - 5000) / 2000.0) * 255))
            
        txt_surface = font.render(m["text"], True, Theme.TEXT)
        txt_surface.set_alpha(alpha)
        
        shadow = font.render(m["text"], True, (0, 0, 0))
        shadow.set_alpha(alpha)
        
        screen.blit(shadow, (16, start_y + 1))
        screen.blit(txt_surface, (15, start_y))
        
        start_y += 25

def play_online_game(screen, net, font, title_font):
    last_board = [[0]*7 for _ in range(6)]
    chat_input = ""
    typing = False

    leave_btn = UI.leave_button(font)
    play_again_btn = UI.play_again_button(font)
    quit_btn = UI.quit_button(font)
    
    local_game_over = False
    waiting_for_rematch = False 

    while net.app_state == "GAME":
        mouse = pygame.mouse.get_pos()
        screen.fill(Theme.BG)

        if net.game_state:
            if not net.game_state.game_over and local_game_over:
                local_game_over = False
                waiting_for_rematch = False 
                last_board = [[0]*7 for _ in range(6)]

            for r in range(6):
                for c in range(7):
                    new_val = net.game_state.board[r][c]
                    if new_val != last_board[r][c]:
                        if new_val != 0:
                            animate_drop(screen, last_board, c, r, new_val)
                        last_board[r][c] = new_val

            draw_board(screen, net.game_state.board)
            pygame.draw.rect(screen, (35, 37, 54), (0, 0, WIDTH, 60))
            leave_btn.draw(screen, mouse)

            if net.game_state.game_over:
                local_game_over = True

            current_turn_nick = net.players.get(net.game_state.turn, "Unknown")
            msg = "YOUR TURN" if net.game_state.turn == net.player_id else f"TURN: {current_turn_nick}"
            color = Theme.P1 if net.game_state.turn == 1 else Theme.P2
            UI.draw_text_with_outline(screen, msg, font, color, (WIDTH//2, 30))

            draw_chat(screen, net, font)

            if typing:
                draw_chat_history(screen, net, font)
                
                box_rect = pygame.Rect(10, HEIGHT - 50, 300, 35)
                box_surf = pygame.Surface((box_rect.w, box_rect.h), pygame.SRCALPHA)
                box_surf.fill((30, 30, 30, 200))
                screen.blit(box_surf, (box_rect.x, box_rect.y))
                pygame.draw.rect(screen, Theme.P2, box_rect, 2, border_radius=5)
                
                cursor = "|" if pygame.time.get_ticks() % 1000 < 500 else ""
                screen.blit(font.render(f"Say: {chat_input}{cursor}", True, Theme.TEXT), (15, HEIGHT - 45))
            else:
                hint_txt = font.render("Chat [ENTER]", True, (200, 200, 200))
                screen.blit(hint_txt, (WIDTH - hint_txt.get_width() - 15, 15))

            if not net.game_state.game_over and net.game_state.turn == net.player_id and not typing:
                col = mouse[0] // CELL_SIZE
                draw_token(screen, net.player_id, int(col * CELL_SIZE + CELL_SIZE / 2), TOP_MARGIN - 50)

        if local_game_over and net.game_state:
            winner_nick = net.players.get(net.game_state.winner, "No one")
            txt = "DRAW!" if net.game_state.winner == 0 else f"{winner_nick} WINS!"
            
            draw_overlay(screen, txt, title_font, Theme.TEXT if net.game_state.winner == 0 else color, board=net.game_state.board, winner=net.game_state.winner)
            
            play_again_btn.draw(screen, mouse)
            quit_btn.draw(screen, mouse)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "QUIT"

            if event.type == pygame.MOUSEBUTTONDOWN:
                if leave_btn.clicked(event, mouse) and not local_game_over:
                    net.send({"type": "LEAVE"})
                    net.reset_game_data()
                    return "LOBBY"
                
                if not typing and not local_game_over and net.game_state:
                    if net.game_state.turn == net.player_id:
                        net.send({"type": "MOVE", "col": event.pos[0] // CELL_SIZE})

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
                if event.key == pygame.K_RETURN:
                    if typing:
                        if chat_input:
                            net.send({"type": "CHAT", "text": chat_input})
                            chat_input = ""
                    else:
                        typing = True
                elif typing:
                    if event.key == pygame.K_ESCAPE:
                        typing = False
                        chat_input = ""
                    elif event.key == pygame.K_BACKSPACE: 
                        chat_input = chat_input[:-1]
                    elif len(chat_input) < 25: 
                        chat_input += event.unicode

            if local_game_over and event.type == pygame.MOUSEBUTTONDOWN:
                if play_again_btn.clicked(event, mouse):
                    net.send({"type": "REMATCH"})
                    net.app_state = "WAITING"
                    return "WAITING"
                    
                if quit_btn.clicked(event, mouse):
                    net.send({"type": "LEAVE"})
                    net.reset_game_data()
                    return "LOBBY"

        pygame.display.update()
    return net.app_state