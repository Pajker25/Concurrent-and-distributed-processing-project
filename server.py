import socket
import threading
import pickle
from game_logic import GameLogic

HOST = '0.0.0.0'
PORT = 5555


# ---------------- GLOBAL SHUTDOWN FLAG ----------------
server_running = True


# ---------------- GAME STATE ----------------
class GameState:
    def __init__(self):
        self.board = GameLogic.create_board()
        self.turn = 1
        self.game_over = False
        self.winner = None
        self.ready = False

    def play_move(self, col, player_id):
        if self.game_over or player_id != self.turn:
            return

        if not GameLogic.is_valid_location(self.board, col):
            return

        row = GameLogic.get_next_open_row(self.board, col)
        if row is None:
            return

        GameLogic.drop_piece(self.board, row, col, player_id)

        if GameLogic.check_win(self.board, player_id):
            self.game_over = True
            self.winner = player_id

        elif GameLogic.is_draw(self.board):
            self.game_over = True
            self.winner = 0

        else:
            self.turn = 2 if self.turn == 1 else 1


# ---------------- ROOMS ----------------
rooms = {}
rooms_lock = threading.Lock()


def broadcast_room(room_name):
    room = rooms.get(room_name)
    if not room:
        return

    state = room["state"]

    for conn in list(room["clients"].keys()):
        try:
            conn.send(pickle.dumps({
                "type": "STATE",
                "state": state
            }))
        except:
            pass


# ---------------- CLIENT HANDLER ----------------
def handle_client(conn, addr):
    current_room = None
    player_id = None

    def leave_room():
        nonlocal current_room, player_id

        with rooms_lock:
            if current_room and current_room in rooms:
                room = rooms[current_room]

                if conn in room["clients"]:
                    del room["clients"][conn]

                if len(room["clients"]) == 0:
                    del rooms[current_room]
                else:
                    room["state"] = GameState()

                    for c in room["clients"]:
                        try:
                            c.send(pickle.dumps({
                                "type": "WAITING",
                                "player_id": 1
                            }))
                        except:
                            pass

        current_room = None
        player_id = None


    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            msg = pickle.loads(data)
            msg_type = msg.get("type")

            # ---------------- LIST ROOMS ----------------
            if msg_type == "LIST":
                with rooms_lock:
                    available = {
                        name: len(r["clients"])
                        for name, r in rooms.items()
                        if len(r["clients"]) < 2
                    }

                conn.send(pickle.dumps({
                    "type": "LIST",
                    "rooms": available
                }))

            # ---------------- CREATE ROOM ----------------
            elif msg_type == "CREATE":
                leave_room()
                name = msg.get("name")

                with rooms_lock:
                    if name and name not in rooms:
                        rooms[name] = {
                            "state": GameState(),
                            "clients": {conn: 1}
                        }
                        current_room = name
                        player_id = 1

                        conn.send(pickle.dumps({
                            "type": "WAITING",
                            "player_id": 1
                        }))

            # ---------------- JOIN ROOM ----------------
            elif msg_type == "JOIN":
                leave_room()
                name = msg.get("name")

                with rooms_lock:
                    if name in rooms and len(rooms[name]["clients"]) < 2:
                        current_room = name
                        player_id = 2

                        rooms[name]["clients"][conn] = 2
                        rooms[name]["state"].ready = True

                        conn.send(pickle.dumps({
                            "type": "GAME_START",
                            "player_id": 2
                        }))

                        broadcast_room(current_room)

            # ---------------- MOVE ----------------
            elif msg_type == "MOVE":
                if current_room:
                    with rooms_lock:
                        state = rooms[current_room]["state"]
                        state.play_move(msg.get("col"), player_id)

                    broadcast_room(current_room)

            # ---------------- RESET ----------------
            elif msg_type == "RESET":
                if current_room:
                    with rooms_lock:
                        rooms[current_room]["state"] = GameState()
                        rooms[current_room]["state"].ready = True

                    broadcast_room(current_room)

            # ---------------- LEAVE ----------------
            elif msg_type == "LEAVE":
                leave_room()

        except:
            break

    leave_room()
    conn.close()


# ---------------- SERVER START ----------------
def start_server():
    global server_running

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server.bind((HOST, PORT))
    server.listen()

    # allows loop to check shutdown flag
    server.settimeout(1.0)

    print("Server running...")
    print("Type 'stop', 'exit', or 'shutdown' to stop server.")

    # ---------------- CONSOLE LISTENER ----------------
    def console_listener():
        global server_running
        while server_running:
            cmd = input().strip().lower()
            if cmd in ["stop", "exit", "shutdown"]:
                print("Shutting down server...")
                server_running = False
                try:
                    server.close()
                except:
                    pass
                break

    threading.Thread(target=console_listener, daemon=True).start()

    # ---------------- MAIN LOOP ----------------
    while server_running:
        try:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr),
                daemon=True
            ).start()

        except socket.timeout:
            continue
        except OSError:
            break

    print("Server stopped cleanly.")
    server.close()


if __name__ == "__main__":
    start_server()