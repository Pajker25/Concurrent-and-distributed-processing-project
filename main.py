# Main entry point handling game loops, states, and local gameplay

import pygame
import sys
from ai_logic import Connect4AI
from game_logic import GameLogic
from ui import Theme, Assets, Fonts, UI, Button, draw_board, draw_token, animate_drop, draw_overlay, WIDTH, HEIGHT, CELL_SIZE, TOP_MARGIN
from network import Network, lobby_screen, waiting_screen, play_online_game


def difficulty_menu_screen(screen, font, title_font):
    easy_btn = Button(WIDTH//2 - 150, 200, 300, 50, "Easy (Random)", font)
    medium_btn = Button(WIDTH//2 - 150, 270, 300, 50, "Medium", font)
    hard_btn = Button(WIDTH//2 - 150, 340, 300, 50, "Hard", font)
    back_btn = Button(10, 10, 100, 40, "Back", font)

    while True:
        screen.fill(Theme.BG)
        mouse = pygame.mouse.get_pos()
        screen.blit(title_font.render("CHOOSE DIFFICULTY", True, Theme.TEXT), (WIDTH//2 - 220, 100))

        easy_btn.draw(screen, mouse)
        medium_btn.draw(screen, mouse)
        hard_btn.draw(screen, mouse)
        back_btn.draw(screen, mouse)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
            if event.type == pygame.QUIT:
                return "QUIT", None
            if event.type == pygame.MOUSEBUTTONDOWN:
                if easy_btn.clicked(event, mouse):
                    return "LOCAL_AI", 1
                if medium_btn.clicked(event, mouse):
                    return "LOCAL_AI", 3
                if hard_btn.clicked(event, mouse):
                    return "LOCAL_AI", 5
                if back_btn.clicked(event, mouse):
                    return "MAIN_MENU", None
        pygame.display.update()


def main_menu_screen(screen, font, title_font):
    local_btn = Button(WIDTH//2 - 150, 180, 300, 50, "PvP", font)
    ai_btn = Button(WIDTH//2 - 150, 250, 300, 50, "AI", font)
    multi_btn = Button(WIDTH//2 - 150, 320, 300, 50, "Multiplayer", font)
    quit_btn = Button(WIDTH//2 - 150, 390, 300, 50, "Quit", font)

    while True:
        screen.fill(Theme.BG)
        mouse = pygame.mouse.get_pos()
        if Assets.LOGO:
            logo_rect = Assets.LOGO.get_rect(center=(WIDTH // 2, 100))
            screen.blit(Assets.LOGO, logo_rect)

        local_btn.draw(screen, mouse)
        ai_btn.draw(screen, mouse)
        multi_btn.draw(screen, mouse)
        quit_btn.draw(screen, mouse)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if local_btn.clicked(event, mouse):
                    return "LOCAL_HUMAN"
                if ai_btn.clicked(event, mouse):
                    return "DIFFICULTY_SELECT"
                if multi_btn.clicked(event, mouse):
                    return "INIT_NETWORK"
                if quit_btn.clicked(event, mouse):
                    return "QUIT"
        pygame.display.update()


def play_local_game(screen, font, title_font, is_ai=False, ai_depth=3):
    board = GameLogic.create_board()
    turn = 1
    game_over = False
    winner = None

    play_again_btn = UI.play_again_button(font)
    leave_btn = UI.leave_button(font)
    quit_btn = UI.quit_button(font)

    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill(Theme.BG)
        pygame.draw.rect(screen, (35, 37, 54), (0, 0, WIDTH, 60))
        draw_board(screen, board)

        if not game_over and is_ai and turn == 2:
            col, _ = Connect4AI.minimax(board, ai_depth, -float('inf'), float('inf'), True)
            
            if col is not None and GameLogic.is_valid_location(board, col):
                row = GameLogic.get_next_open_row(board, col)
                board_before = [r[:] for r in board]
                GameLogic.drop_piece(board, row, col, 2)
                animate_drop(screen, board_before, col, row, 2)

                if GameLogic.check_win(board, 2):
                    game_over, winner = True, 2
                elif GameLogic.is_draw(board):
                    game_over, winner = True, 0
                else:
                    turn = 1
            continue

        if not game_over:
            color = Theme.P1 if turn == 1 else Theme.P2
            UI.draw_text_with_outline(screen, f"PLAYER {turn}'S TURN", font, color, (WIDTH//2, 30))

            col = mouse[0] // CELL_SIZE
            draw_token(screen, turn, int(col * CELL_SIZE + CELL_SIZE / 2), TOP_MARGIN - 50)
            leave_btn.draw(screen, mouse)
        else:
            draw_overlay(screen, "DRAW!" if winner == 0 else f"PLAYER {winner} WINS!", title_font, Theme.TEXT if winner == 0 else (Theme.P1 if winner == 1 else Theme.P2), board=board, winner=winner)
            play_again_btn.draw(screen, mouse)
            quit_btn.draw(screen, mouse)

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
            if event.type == pygame.QUIT:
                return "QUIT"
            if event.type == pygame.MOUSEBUTTONDOWN:
                if not game_over:
                    if leave_btn.clicked(event, mouse):
                        return "MAIN_MENU"
                    
                    col = mouse[0] // CELL_SIZE
                    if GameLogic.is_valid_location(board, col):
                        row = GameLogic.get_next_open_row(board, col)
                        board_before = [r[:] for r in board]
                        GameLogic.drop_piece(board, row, col, turn)
                        animate_drop(screen, board_before, col, row, turn)

                        if GameLogic.check_win(board, turn):
                            game_over, winner = True, turn
                        elif GameLogic.is_draw(board):
                            game_over, winner = True, 0
                        else:
                            turn = 2 if turn == 1 else 1
                else:
                    if play_again_btn.clicked(event, mouse):
                        board = GameLogic.create_board()
                        turn, game_over, winner = 1, False, None
                    if quit_btn.clicked(event, mouse):
                        return "MAIN_MENU"

        pygame.display.update()


def main():
    pygame.init()
    flags = pygame.RESIZABLE | pygame.SCALED
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    Assets.load()

    font = Fonts.small()
    title_font = Fonts.title()
    net = None
    state = "MAIN_MENU"
    ai_depth = 3
    leave_btn = UI.leave_button(font)

    while state != "QUIT":
        if net and net.app_state == "QUIT":
            state = "QUIT"
            break

        if state == "MAIN_MENU":
            if net:
                try:
                    net.client.close()
                except Exception:
                    pass
                net = None 
            state = main_menu_screen(screen, font, title_font)
            
        elif state == "LOCAL_HUMAN":
            state = play_local_game(screen, font, title_font, is_ai=False)

        elif state == "DIFFICULTY_SELECT":
            state, ai_depth = difficulty_menu_screen(screen, font, title_font)

        elif state == "LOCAL_AI":
            state = play_local_game(screen, font, title_font, is_ai=True, ai_depth=ai_depth)

        elif state == "INIT_NETWORK":
            net = Network()
            if not net.connect():
                state = "MAIN_MENU"
            else:
                state = "LOBBY"

        elif state == "LOBBY":
            state = lobby_screen(screen, net, font, title_font)
            
        elif state == "WAITING":
            state = waiting_screen(screen, net, font, leave_btn)
                
        elif state == "GAME":
            state = play_online_game(screen, net, font, title_font)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()