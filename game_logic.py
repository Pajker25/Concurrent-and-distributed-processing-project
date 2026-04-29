# game_logic.py

class GameLogic:
    ROWS = 6
    COLS = 7
    WIN_CONDITION = 4

    @staticmethod
    def create_board():
        return [[0 for _ in range(GameLogic.COLS)] for _ in range(GameLogic.ROWS)]

    @staticmethod
    def is_valid_location(board, col):
        return 0 <= col < GameLogic.COLS and board[0][col] == 0

    @staticmethod
    def get_next_open_row(board, col):
        for r in range(GameLogic.ROWS - 1, -1, -1):
            if board[r][col] == 0:
                return r
        return None

    @staticmethod
    def drop_piece(board, row, col, piece):
        board[row][col] = piece

    @staticmethod
    def check_win(board, piece):
        w = GameLogic.WIN_CONDITION
        rows, cols = GameLogic.ROWS, GameLogic.COLS

        # horizontal
        for r in range(rows):
            for c in range(cols - w + 1):
                if all(board[r][c+i] == piece for i in range(w)):
                    return True

        # vertical
        for c in range(cols):
            for r in range(rows - w + 1):
                if all(board[r+i][c] == piece for i in range(w)):
                    return True

        # diagonal \
        for r in range(rows - w + 1):
            for c in range(cols - w + 1):
                if all(board[r+i][c+i] == piece for i in range(w)):
                    return True

        # diagonal /
        for r in range(w - 1, rows):
            for c in range(cols - w + 1):
                if all(board[r-i][c+i] == piece for i in range(w)):
                    return True

        return False

    @staticmethod
    def is_draw(board):
        return all(board[0][c] != 0 for c in range(GameLogic.COLS))