# Multiplayer server implementation handling game rooms and client connections

import socket
import threading
import pickle
from game_logic import GameLogic, GameState

HOST = '0.0.0.0'
PORT = 5555
server_running = True


rooms = {}
rooms_lock = threading.RLock()

def broadcast_room(room_name):
    with rooms_lock:
        room = rooms.get(room_name)
        if not room:
            return
        state = room["state"]
        clients = list(room["clients"].keys())

    for conn in clients:
        try:
            conn.send(pickle.dumps({
                "type": "STATE",
                "state": state
            }))
        except Exception:
            pass

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
                        except Exception:
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

            elif msg_type == "CREATE":
                leave_room()
                name = msg.get("name")
                nick = msg.get("nick", "Player 1")

                with rooms_lock:
                    if name and name not in rooms:
                        rooms[name] = {
                            "state": GameState(),
                            "clients": {conn: {"id": 1, "nick": nick, "rematch": False}} 
                        }
                        current_room = name
                        player_id = 1
                        conn.send(pickle.dumps({
                            "type": "WAITING",
                            "player_id": 1
                        }))

            elif msg_type == "JOIN":
                leave_room()
                name = msg.get("name")
                nick = msg.get("nick", "Player 2")

                with rooms_lock:
                    if name in rooms and len(rooms[name]["clients"]) < 2:
                        current_room = name
                        player_id = 2
                        rooms[name]["clients"][conn] = {"id": 2, "nick": nick, "rematch": False}
                        rooms[name]["state"].ready = True

                        players_info = {
                            c_info["id"]: c_info["nick"] 
                            for c_info in rooms[name]["clients"].values()
                        }

                        for c in rooms[name]["clients"]:
                            c.send(pickle.dumps({
                                "type": "GAME_START",
                                "player_id": rooms[name]["clients"][c]["id"],
                                "players": players_info
                            }))
                        broadcast_room(current_room)

            elif msg_type == "CHAT":
                if current_room:
                    with rooms_lock:
                        nick = rooms[current_room]["clients"][conn]["nick"]
                        text = f"{nick}: {msg.get('text')}"
                        chat_packet = pickle.dumps({"type": "CHAT", "msg": text})
                        for c in rooms[current_room]["clients"]:
                            try:
                                c.send(chat_packet)
                            except Exception:
                                pass

            elif msg_type == "MOVE":
                if current_room:
                    with rooms_lock:
                        state = rooms[current_room]["state"]
                        state.play_move(msg.get("col"), player_id)
                    broadcast_room(current_room)

            elif msg_type == "REMATCH":
                if current_room:
                    with rooms_lock:
                        rooms[current_room]["clients"][conn]["rematch"] = True
                        clients_list = list(rooms[current_room]["clients"].values())
                        
                        if len(clients_list) == 2 and all(c.get("rematch") for c in clients_list):
                            rooms[current_room]["state"] = GameState()
                            rooms[current_room]["state"].ready = True
                            
                            for c in rooms[current_room]["clients"].values():
                                c["rematch"] = False
                            
                            broadcast_room(current_room)

            elif msg_type == "LEAVE":
                leave_room()

        except Exception:
            break

    leave_room()
    conn.close()

def start_server():
    global server_running
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen()
    server.settimeout(1.0)

    print("Server running...")

    def console_listener():
        global server_running
        while server_running:
            cmd = input().strip().lower()
            if cmd in ["stop", "exit", "shutdown"]:
                server_running = False
                server.close()
                break

    threading.Thread(target=console_listener, daemon=True).start()

    while server_running:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except socket.timeout:
            continue
        except OSError:
            break

    server.close()

if __name__ == "__main__":
    start_server()