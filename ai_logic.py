# AI opponent implementation and board evaluation

import random
import math
from game_logic import GameLogic


class Connect4AI:
    PLAYER_PIECE = 1
    AI_PIECE = 2
    WINDOW_LENGTH = 4
    EMPTY = 0

    @staticmethod
    def get_random_move(board):
        valid_locations = [
            c for c in range(GameLogic.COLS) if GameLogic.is_valid_location(board, c)
        ]
        return random.choice(valid_locations) if valid_locations else None

    @staticmethod
    def evaluate_window(window, piece):
        score = 0
        opp_piece = 1 if piece == 2 else 2

        if window.count(piece) == 4:
            score += 100
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += 5
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += 2

        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= 4

        return score

    @staticmethod
    def score_position(board, piece):
        score = 0

        center_array = [board[r][GameLogic.COLS // 2] for r in range(GameLogic.ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 3

        for r in range(GameLogic.ROWS):
            row_array = board[r]
            for c in range(GameLogic.COLS - 3):
                window = row_array[c : c + 4]
                score += Connect4AI.evaluate_window(window, piece)

        for c in range(GameLogic.COLS):
            col_array = [board[r][c] for r in range(GameLogic.ROWS)]
            for r in range(GameLogic.ROWS - 3):
                window = col_array[r : r + 4]
                score += Connect4AI.evaluate_window(window, piece)

        for r in range(GameLogic.ROWS - 3):
            for c in range(GameLogic.COLS - 3):
                window = [board[r + i][c + i] for i in range(4)]
                score += Connect4AI.evaluate_window(window, piece)

        for r in range(3, GameLogic.ROWS):
            for c in range(GameLogic.COLS - 3):
                window = [board[r - i][c + i] for i in range(4)]
                score += Connect4AI.evaluate_window(window, piece)

        return score

    @staticmethod
    def minimax(board, depth, alpha, beta, maximizingPlayer):
        valid_locations = [
            c for c in range(GameLogic.COLS) if GameLogic.is_valid_location(board, c)
        ]
        is_terminal = (
            GameLogic.check_win(board, 1)
            or GameLogic.check_win(board, 2)
            or len(valid_locations) == 0
        )

        if depth == 0 or is_terminal:
            if is_terminal:
                if GameLogic.check_win(board, 2):
                    return (None, 10000000000000)
                elif GameLogic.check_win(board, 1):
                    return (None, -10000000000000)
                else:
                    return (None, 0)
            else:
                return (None, Connect4AI.score_position(board, 2))

        if maximizingPlayer:
            value = -math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = GameLogic.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                GameLogic.drop_piece(b_copy, row, col, 2)
                new_score = Connect4AI.minimax(b_copy, depth - 1, alpha, beta, False)[1]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return column, value

        else:
            value = math.inf
            column = random.choice(valid_locations)
            for col in valid_locations:
                row = GameLogic.get_next_open_row(board, col)
                b_copy = [r[:] for r in board]
                GameLogic.drop_piece(b_copy, row, col, 1)
                new_score = Connect4AI.minimax(b_copy, depth - 1, alpha, beta, True)[1]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return column, value
