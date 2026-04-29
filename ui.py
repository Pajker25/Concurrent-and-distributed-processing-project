import pygame
from game_logic import GameLogic


# ---------------- CONSTANTS ----------------
ROWS = GameLogic.ROWS
COLS = GameLogic.COLS

CELL_SIZE = 100
PIECE_SIZE = 42
TOP_MARGIN = 150

WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE + TOP_MARGIN


# ---------------- THEME ----------------
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


# ---------------- FONTS ----------------
class Fonts:
    @staticmethod
    def small():
        return pygame.font.SysFont("helvetica", 28, True)

    @staticmethod
    def title():
        return pygame.font.SysFont("helvetica", 50, True)


# ---------------- BUTTON ----------------
class Button:
    def __init__(self, x, y, w, h, text, font):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font

    def draw(self, screen, mouse):
        color = Theme.BTN_HOVER if self.rect.collidepoint(mouse) else Theme.BTN
        pygame.draw.rect(screen, color, self.rect, border_radius=10)

        txt = self.font.render(self.text, True, Theme.TEXT)
        screen.blit(txt, txt.get_rect(center=self.rect.center))

    def clicked(self, event, mouse):
        return event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(mouse)


class UI:

    @staticmethod
    def play_again_button(font):
        play_w = 200
        quit_w = 100
        h = 50
        gap = 20

        total_width = play_w + gap + quit_w
        start_x = WIDTH // 2 - total_width // 2

        return Button(
            start_x,
            250,
            play_w,
            h,
            "Play Again",
            font
        )

    @staticmethod
    def quit_button(font):
        play_w = 200
        quit_w = 100
        h = 50
        gap = 20

        total_width = play_w + gap + quit_w
        start_x = WIDTH // 2 - total_width // 2 + play_w + gap

        return Button(
            start_x,
            250,
            quit_w,
            h,
            "Quit",
            font
        )

    @staticmethod
    def leave_button(font):
        return Button(
            10,
            10,
            100,
            40,
            "Leave",
            font
        )

    # (optional future reuse)
    @staticmethod
    def create_room_button(font):
        return Button(
            WIDTH // 2 - 100,
            220,
            200,
            50,
            "Create Room",
            font
        )

    @staticmethod
    def refresh_button(font):
        return Button(
            WIDTH // 2 - 100,
            HEIGHT - 70,
            200,
            40,
            "Refresh",
            font
        )


# ---------------- DRAWING ----------------
def draw_token(screen, piece, x, y):
    if piece == 0:
        return

    base = Theme.P1 if piece == 1 else Theme.P2
    light = Theme.P1_LIGHT if piece == 1 else Theme.P2_LIGHT

    pygame.draw.circle(screen, base, (x, y), PIECE_SIZE)
    pygame.draw.circle(
        screen,
        light,
        (x, y - int(PIECE_SIZE * 0.15)),
        int(PIECE_SIZE * 0.7)
    )


def draw_board(screen, board):
    pygame.draw.rect(screen, Theme.BOARD_SHADOW,
                     (0, TOP_MARGIN, WIDTH, HEIGHT - TOP_MARGIN))

    pygame.draw.rect(screen, Theme.BOARD,
                     (0, TOP_MARGIN - 10, WIDTH, HEIGHT - TOP_MARGIN + 10),
                     border_radius=15)

    for r in range(ROWS):
        for c in range(COLS):
            cx = int(c * CELL_SIZE + CELL_SIZE / 2)
            cy = int(r * CELL_SIZE + CELL_SIZE / 2 + TOP_MARGIN)

            if board[r][c] == 0:
                pygame.draw.circle(screen, Theme.EMPTY, (cx, cy), PIECE_SIZE)
            else:
                draw_token(screen, board[r][c], cx, cy)


# ---------------- ANIMATION ----------------
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

        screen.fill(Theme.BG)
        draw_board(screen, board_before)
        draw_token(screen, piece, x, int(y))

        pygame.display.update()
        clock.tick(60)


# ---------------- OVERLAY ----------------
def draw_overlay(screen, text, font, color):
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    txt = font.render(text, True, color)
    screen.blit(txt, txt.get_rect(center=(WIDTH // 2, 180)))