import pygame
import sys
from ui import *
from game_logic import GameLogic


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    font = Fonts.small()
    title_font = Fonts.title()

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

        # ---------------- GAME ACTIVE ----------------
        if not game_over:
            color = Theme.P1 if turn == 1 else Theme.P2

            txt = font.render(f"PLAYER {turn}'S TURN", True, color)
            screen.blit(txt, txt.get_rect(center=(WIDTH//2, 30)))

            col = mouse[0] // CELL_SIZE
            draw_token(screen, turn,
                       int(col * CELL_SIZE + CELL_SIZE / 2),
                       TOP_MARGIN - 50)
            
            leave_btn.draw(screen, mouse)

        # ---------------- GAME OVER ----------------
        else:
            draw_overlay(
                screen,
                "DRAW!" if winner == 0 else f"PLAYER {winner} WINS!",
                title_font,
                Theme.TEXT if winner == 0 else (Theme.P1 if winner == 1 else Theme.P2)
            )

            play_again_btn.draw(screen, mouse)
            quit_btn.draw(screen, mouse)            

        # ---------------- EVENTS ----------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:

                if not game_over:
                    col = mouse[0] // CELL_SIZE

                    if leave_btn.clicked(event, mouse):
                            pygame.quit()
                            sys.exit()

                    if GameLogic.is_valid_location(board, col):
                        row = GameLogic.get_next_open_row(board, col)

                        board_before = [r[:] for r in board]
                        GameLogic.drop_piece(board, row, col, turn)

                        animate_drop(screen, board_before, col, row, turn)

                        if GameLogic.check_win(board, turn):
                            game_over = True
                            winner = turn

                        elif GameLogic.is_draw(board):
                            game_over = True
                            winner = 0

                        
                        else:
                            turn = 2 if turn == 1 else 1

                else:
                    if play_again_btn.clicked(event, mouse):
                        board = GameLogic.create_board()
                        turn = 1
                        game_over = False
                        winner = None

                    if quit_btn.clicked(event, mouse):
                        pygame.quit()
                        sys.exit()

        pygame.display.update()


if __name__ == "__main__":
    main()