# Multiplayer server handling game rooms, client connections, and reconnections

import socket
import threading
import pickle
from game_logic import GameLogic, GameState

HOST = "0.0.0.0"
PORT = 5555
server_running = True

rooms: dict = {}
rooms_lock = threading.RLock()


def broadcast_room(room_name):
    with rooms_lock:
        room = rooms.get(room_name)
        if not room:
            return
        state = room["state"]
        conns = [
            p["conn"] for p in room["players"].values() if p["connected"] and p["conn"]
        ]

    for conn in conns:
        try:
            conn.send(pickle.dumps({"type": "STATE", "state": state}))
        except Exception:
            pass


def handle_client(conn, addr):
    current_room = None
    player_id = None

    def handle_intentional_leave(is_surrender=False):
        nonlocal current_room, player_id
        with rooms_lock:
            if current_room and current_room in rooms:
                room = rooms[current_room]

                if is_surrender:
                    if not room["state"].game_over:
                        room["state"].game_over = True
                        room["state"].winner = 3 - player_id
                        broadcast_room(current_room)
                    return

                if player_id in room["players"]:
                    del room["players"][player_id]

                if len(room["players"]) == 0:
                    del rooms[current_room]
                else:
                    room["state"] = GameState()
                    room["state"].ready = False
                    for p in room["players"].values():
                        p["rematch"] = False

                    for p_id, p_data in room["players"].items():
                        if p_data["connected"] and p_data["conn"]:
                            try:
                                p_data["conn"].send(
                                    pickle.dumps({"type": "WAITING", "player_id": p_id})
                                )
                            except Exception:
                                pass

        current_room = None
        player_id = None

    def handle_disconnect():
        nonlocal current_room, player_id
        with rooms_lock:
            if current_room and current_room in rooms:
                room = rooms[current_room]
                if player_id in room["players"]:
                    room["players"][player_id]["connected"] = False
                    room["players"][player_id]["conn"] = None

                    other_id = 3 - player_id
                    if (
                        other_id in room["players"]
                        and room["players"][other_id]["connected"]
                    ):
                        try:
                            room["players"][other_id]["conn"].send(
                                pickle.dumps(
                                    {"type": "OPPONENT_DISCONNECTED", "status": True}
                                )
                            )
                        except Exception:
                            pass

                if all(not p["connected"] for p in room["players"].values()):
                    del rooms[current_room]

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            msg = pickle.loads(data)
            msg_type = msg.get("type")

            if msg_type == "LIST":
                requester_nick = msg.get("nick", "")
                with rooms_lock:
                    available = {}
                    for name, r in rooms.items():
                        if r["state"].game_over:
                            continue

                        total_players = len(r["players"])
                        active_players = sum(
                            1 for p in r["players"].values() if p["connected"]
                        )

                        if total_players == 1:
                            available[name] = active_players
                        elif total_players == 2 and active_players == 1:
                            disconnected_nick = None
                            for p in r["players"].values():
                                if not p["connected"]:
                                    disconnected_nick = p["nick"]
                                    break

                            if disconnected_nick == requester_nick:
                                available[name] = active_players

                conn.send(pickle.dumps({"type": "LIST", "rooms": available}))

            elif msg_type == "CREATE":
                handle_intentional_leave(False)
                name = msg.get("name")
                nick = msg.get("nick", "Player 1")

                with rooms_lock:
                    if name and name not in rooms:
                        rooms[name] = {
                            "state": GameState(),
                            "players": {
                                1: {
                                    "conn": conn,
                                    "nick": nick,
                                    "rematch": False,
                                    "connected": True,
                                }
                            },
                        }
                        current_room = name
                        player_id = 1
                        conn.send(pickle.dumps({"type": "WAITING", "player_id": 1}))

            elif msg_type == "JOIN":
                handle_intentional_leave(False)
                name = msg.get("name")
                nick = msg.get("nick", "Player 2")

                with rooms_lock:
                    if name in rooms:
                        room = rooms[name]
                        rejoined = False

                        for pid, pdata in room["players"].items():
                            if not pdata["connected"] and pdata["nick"] == nick:
                                pdata["conn"] = conn
                                pdata["connected"] = True
                                current_room = name
                                player_id = pid
                                rejoined = True

                                players_info = {
                                    p_id: p["nick"]
                                    for p_id, p in room["players"].items()
                                }
                                conn.send(
                                    pickle.dumps(
                                        {
                                            "type": "GAME_START",
                                            "player_id": pid,
                                            "players": players_info,
                                        }
                                    )
                                )

                                other_id = 3 - pid
                                if (
                                    other_id in room["players"]
                                    and room["players"][other_id]["connected"]
                                ):
                                    try:
                                        room["players"][other_id]["conn"].send(
                                            pickle.dumps(
                                                {
                                                    "type": "OPPONENT_DISCONNECTED",
                                                    "status": False,
                                                }
                                            )
                                        )
                                        room["players"][other_id]["conn"].send(
                                            pickle.dumps(
                                                {
                                                    "type": "GAME_START",
                                                    "player_id": other_id,
                                                    "players": players_info,
                                                }
                                            )
                                        )
                                    except Exception:
                                        pass

                                broadcast_room(current_room)
                                break

                        if (
                            not rejoined
                            and len(room["players"]) < 2
                            and not room["state"].game_over
                        ):
                            pid = 2 if 1 in room["players"] else 1
                            room["players"][pid] = {
                                "conn": conn,
                                "nick": nick,
                                "rematch": False,
                                "connected": True,
                            }
                            current_room = name
                            player_id = pid
                            room["state"].ready = True

                            players_info = {
                                p_id: p["nick"] for p_id, p in room["players"].items()
                            }
                            for p_id, p_data in room["players"].items():
                                if p_data["connected"] and p_data["conn"]:
                                    try:
                                        p_data["conn"].send(
                                            pickle.dumps(
                                                {
                                                    "type": "GAME_START",
                                                    "player_id": p_id,
                                                    "players": players_info,
                                                }
                                            )
                                        )
                                    except Exception:
                                        pass
                            broadcast_room(current_room)

            elif msg_type == "CHAT":
                if current_room:
                    with rooms_lock:
                        room = rooms[current_room]
                        if player_id in room["players"]:
                            nick = room["players"][player_id]["nick"]
                            text = f"{nick}: {msg.get('text')}"
                            chat_packet = pickle.dumps({"type": "CHAT", "msg": text})
                            for p in room["players"].values():
                                if p["connected"] and p["conn"]:
                                    try:
                                        p["conn"].send(chat_packet)
                                    except Exception:
                                        pass

            elif msg_type == "MOVE":
                if current_room:
                    with rooms_lock:
                        room = rooms[current_room]
                        state = room["state"]
                        if (
                            not state.game_over
                            and len(room["players"]) == 2
                            and all(p["connected"] for p in room["players"].values())
                        ):
                            state.play_move(msg.get("col"), player_id)
                    broadcast_room(current_room)

            elif msg_type == "REMATCH":
                if current_room:
                    with rooms_lock:
                        room = rooms[current_room]
                        if player_id in room["players"]:
                            room["players"][player_id]["rematch"] = True

                        if len(room["players"]) == 2 and all(
                            p.get("rematch")
                            for p in room["players"].values()
                            if p["connected"]
                        ):
                            room["state"] = GameState()
                            room["state"].ready = True
                            for p in room["players"].values():
                                p["rematch"] = False

                            players_info = {
                                p_id: p["nick"] for p_id, p in room["players"].items()
                            }
                            for p_id, p_data in room["players"].items():
                                if p_data["connected"] and p_data["conn"]:
                                    try:
                                        p_data["conn"].send(
                                            pickle.dumps(
                                                {
                                                    "type": "GAME_START",
                                                    "player_id": p_id,
                                                    "players": players_info,
                                                }
                                            )
                                        )
                                    except Exception:
                                        pass
                            broadcast_room(current_room)
                        else:
                            try:
                                conn.send(
                                    pickle.dumps(
                                        {"type": "WAITING", "player_id": player_id}
                                    )
                                )
                            except Exception:
                                pass

            elif msg_type == "SURRENDER":
                handle_intentional_leave(True)

            elif msg_type == "LEAVE":
                handle_intentional_leave(False)

        except Exception:
            handle_disconnect()
            break

    handle_disconnect()
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
            threading.Thread(
                target=handle_client, args=(conn, addr), daemon=True
            ).start()
        except socket.timeout:
            continue
        except OSError:
            break

    server.close()


if __name__ == "__main__":
    start_server()
