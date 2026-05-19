# User interface definitions, asset management and rendering

import pygame
import os
import math
from game_logic import GameLogic

ROWS = GameLogic.ROWS
COLS = GameLogic.COLS
CELL_SIZE = 100
PIECE_SIZE = 42
TOP_MARGIN = 150
WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + TOP_MARGIN

class Assets:
    BG = None
    BOARD = None
    TOKEN_P1 = None
    TOKEN_P2 = None

    @staticmethod
    def load():
        token_size = (int(CELL_SIZE * 0.9), int(CELL_SIZE * 0.9))
        
        Assets.TOKEN_P1 = pygame.image.load(os.path.join("assets", "token_p1.png")).convert_alpha()
        Assets.TOKEN_P1 = pygame.transform.smoothscale(Assets.TOKEN_P1, token_size)
        
        Assets.TOKEN_P2 = pygame.image.load(os.path.join("assets", "token_p2.png")).convert_alpha()
        Assets.TOKEN_P2 = pygame.transform.smoothscale(Assets.TOKEN_P2, token_size)
        
        Assets.BOARD = pygame.image.load(os.path.join("assets", "board.png")).convert_alpha()
        Assets.BOARD = pygame.transform.smoothscale(Assets.BOARD, (COLS * CELL_SIZE, ROWS * CELL_SIZE))
        
        Assets.BG = pygame.image.load(os.path.join("assets", "bg.png")).convert()
        Assets.BG = pygame.transform.smoothscale(Assets.BG, (WIDTH, HEIGHT))

        Assets.LOGO = pygame.image.load(os.path.join("assets", "logo.png")).convert_alpha()

class Theme:
    BG = (43, 45, 66)
    BOARD = (30, 136, 229)
    BOARD_SHADOW = (21, 101, 192)
    EMPTY = (43, 45, 66)
    P1 = (229, 57, 53)
    P1_LIGHT = (239, 154, 154)
    P2 = (253, 216, 53)
    P2_LIGHT = (255, 245, 157)
    TEXT = (255, 255, 255)
    BTN = (69, 90, 100)
    BTN_HOVER = (96, 125, 139)
    BTN_SHADOW = (38, 50, 56)
    BTN_HIGHLIGHT = (120, 144, 156)

class Fonts:
    @staticmethod
    def small():
        return pygame.font.SysFont("helvetica", 28, True)

    @staticmethod
    def title():
        return pygame.font.SysFont("helvetica", 50, True)

class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        
        self.base_color = Theme.BTN
        self.hover_color = Theme.BTN_HOVER
        self.shadow_color = Theme.BTN_SHADOW
        self.highlight_color = Theme.BTN_HIGHLIGHT
        
        self.elevation = 6
        self.dynamic_elevation = self.elevation
        self.original_y = y

    def draw(self, screen, mouse):
        top_rect = self.rect.copy()
        bottom_rect = self.rect.copy()
        
        is_hovered = top_rect.collidepoint(mouse)
        is_clicking = pygame.mouse.get_pressed()[0]

        if is_hovered:
            if is_clicking:
                self.dynamic_elevation = 0
            else:
                self.dynamic_elevation = self.elevation + 2
            current_color = self.hover_color
        else:
            self.dynamic_elevation = self.elevation
            current_color = self.base_color

        top_rect.y = self.original_y - self.dynamic_elevation
        bottom_rect.y = self.original_y

        pygame.draw.rect(screen, self.shadow_color, bottom_rect, border_radius=12)
        
        pygame.draw.rect(screen, current_color, top_rect, border_radius=12)
        
        highlight_rect = pygame.Rect(top_rect.x, top_rect.y, top_rect.w, 6)
        pygame.draw.rect(screen, self.highlight_color if is_hovered else self.hover_color, highlight_rect, border_radius=12)

        txt = self.font.render(self.text, True, Theme.TEXT)
        screen.blit(txt, txt.get_rect(center=top_rect.center))

    def clicked(self, event, mouse):
        current_top_rect = self.rect.copy()
        current_top_rect.y = self.original_y - self.dynamic_elevation
        
        return event.type == pygame.MOUSEBUTTONDOWN and current_top_rect.collidepoint(mouse)

class UI:
    @staticmethod
    def play_again_button(font):
        play_w, quit_w, h, gap = 200, 120, 50, 20
        total_width = play_w + gap + quit_w
        start_x = WIDTH // 2 - total_width // 2
        return Button(start_x, 250, play_w, h, "Play Again", font)

    @staticmethod
    def quit_button(font):
        play_w, quit_w, h, gap = 200, 120, 50, 20
        total_width = play_w + gap + quit_w
        start_x = WIDTH // 2 - total_width // 2 + play_w + gap
        return Button(start_x, 250, quit_w, h, "Leave", font)

    @staticmethod
    def leave_button(font):
        return Button(10, 10, 100, 40, "Leave", font)

    @staticmethod
    def create_room_button(font):
        return Button(WIDTH // 2 - 100, 220, 200, 50, "Create Room", font)

    @staticmethod
    def refresh_button(font):
        return Button(WIDTH // 2 - 100, HEIGHT - 70, 200, 40, "Refresh", font)
    @staticmethod
    def draw_text_with_outline(screen, text, font, color, center_pos):
        x, y = center_pos
    
        outline_color = (0, 0, 0)
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (0, -2), (0, 2), (-2, 0), (2, 0)]:
            outline_surf = font.render(text, True, outline_color)
            outline_rect = outline_surf.get_rect(center=(x + dx, y + dy))
            screen.blit(outline_surf, outline_rect)
        
        main_surf = font.render(text, True, color)
        main_rect = main_surf.get_rect(center=(x, y))
        screen.blit(main_surf, main_rect)

def draw_token(screen, piece, x, y):
    if piece == 0:
        return
    img = Assets.TOKEN_P1 if piece == 1 else Assets.TOKEN_P2
    rect = img.get_rect(center=(x, y))
    screen.blit(img, rect)

def draw_board(screen, board):
    screen.blit(Assets.BG, (0, 0))
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != 0:
                cx = int(c * CELL_SIZE + CELL_SIZE / 2)
                cy = int(r * CELL_SIZE + CELL_SIZE / 2 + TOP_MARGIN)
                draw_token(screen, board[r][c], cx, cy)
    screen.blit(Assets.BOARD, (0, TOP_MARGIN))

def get_winning_coords(board, piece):
    w = 4
    rows, cols = ROWS, COLS

    for r in range(rows):
        for c in range(cols - w + 1):
            if all(board[r][c+i] == piece for i in range(w)):
                return [(r, c+i) for i in range(w)]

    for c in range(cols):
        for r in range(rows - w + 1):
            if all(board[r+i][c] == piece for i in range(w)):
                return [(r+i, c) for i in range(w)]

    for r in range(rows - w + 1):
        for c in range(cols - w + 1):
            if all(board[r+i][c+i] == piece for i in range(w)):
                return [(r+i, c+i) for i in range(w)]

    for r in range(w - 1, rows):
        for c in range(cols - w + 1):
            if all(board[r-i][c+i] == piece for i in range(w)):
                return [(r-i, c+i) for i in range(w)]

    return []

def animate_drop(screen, board_before, col, row, piece):
    x = int(col * CELL_SIZE + CELL_SIZE / 2)
    y = TOP_MARGIN // 2
    target = int(row * CELL_SIZE + CELL_SIZE / 2 + TOP_MARGIN)
    clock = pygame.time.Clock()
    vel = 0

    while y < target:
        vel += 1.5
        y += vel
        if y > target:
            y = target

        screen.blit(Assets.BG, (0, 0))
        for r in range(ROWS):
            for c in range(COLS):
                if board_before[r][c] != 0:
                    cx = int(c * CELL_SIZE + CELL_SIZE / 2)
                    cy = int(r * CELL_SIZE + CELL_SIZE / 2 + TOP_MARGIN)
                    draw_token(screen, board_before[r][c], cx, cy)

        draw_token(screen, piece, x, int(y))
        screen.blit(Assets.BOARD, (0, TOP_MARGIN))
        pygame.display.update()
        clock.tick(60)

def draw_overlay(screen, text, font, color, board=None, winner=None):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    if board and winner and winner in [1, 2]:
        winning_coords = get_winning_coords(board, winner)
        time = pygame.time.get_ticks() / 1000.0
        pulse = (math.sin(time * 6) + 1) / 2
        glow_radius = int(PIECE_SIZE * 1.2 + (15 * pulse))
        
        for r, c in winning_coords:
            cx = int(c * CELL_SIZE + CELL_SIZE / 2)
            cy = int(r * CELL_SIZE + CELL_SIZE / 2 + TOP_MARGIN)
            glow_surf = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 215, 0, 150), (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surf, (cx - glow_radius, cy - glow_radius))
            draw_token(screen, winner, cx, cy)

    txt = font.render(text, True, color)
    shadow = font.render(text, True, (0, 0, 0))
    screen.blit(shadow, shadow.get_rect(center=(WIDTH // 2 + 3, 180 + 3)))
    screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 180)))


def draw_chat_history(screen, net, font):
    panel_w = 300
    panel_h = (HEIGHT - 100) // 2
    panel_x = 10
    panel_y = HEIGHT - 50 - panel_h - 10
    
    history_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    history_surf.fill((30, 30, 30, 150))
    screen.blit(history_surf, (panel_x, panel_y))
    
    pygame.draw.rect(screen, Theme.BTN_HOVER, (panel_x, panel_y, panel_w, panel_h), 2, border_radius=5)
    
    max_messages = (panel_h - 20) // 25
    visible_messages = net.messages[-max_messages:] if len(net.messages) > max_messages else net.messages
    
    msg_y = panel_y + 10
    for m in visible_messages:
        shadow = font.render(m["text"], True, (0, 0, 0))
        txt_surface = font.render(m["text"], True, Theme.TEXT)
        
        screen.blit(shadow, (panel_x + 11, msg_y + 1))
        screen.blit(txt_surface, (panel_x + 10, msg_y))
        msg_y += 25