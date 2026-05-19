# Connect 4 Deluxe

A polished **Connect 4 game built with Python and Pygame** featuring:

- Local Player vs Player
- AI opponent with multiple difficulty levels
- Online multiplayer with lobby system
- In-game chat
- Smooth animations and custom UI
- Reconnect & rematch support

---

# Features

## Local Multiplayer
Play classic Connect 4 against another player on the same computer.

## AI Opponent
Three AI difficulty levels:

| Difficulty | Description |
|---|---|
| Easy | Random moves |
| Medium | Minimax AI (depth 3) |
| Hard | Minimax AI (depth 5) |

The AI uses:
- Minimax algorithm
- Alpha-beta pruning

---

## Online Multiplayer
Host or join rooms online with:
- Real-time synchronized gameplay
- Reconnection support
- Room lobby system
- Live chat
- Rematch functionality

---

## Visual Polish
- Animated token drops
- Highlighted winning combinations
- Custom buttons and overlays
- Smooth hover/click effects
- Fullscreen support (`F11`)

---

# Project Structure

```text
project/
│
├── main.py           # Main game loop and state management
├── game_logic.py     # Core gameplay rules and board logic
├── ai_logic.py       # AI opponent and minimax implementation
├── network.py        # Multiplayer client and online gameplay
├── server.py         # Multiplayer game server
├── ui.py             # Rendering, animations, buttons, assets
│
├── assets/
│   ├── bg.png
│   ├── board.png
│   ├── logo.png
│   ├── token_p1.png
│   └── token_p2.png
│
└── README.md
```

---

# Requirements

- Python 3.10+
- Pygame

Install dependencies:

```bash
pip install pygame
```

---

# Running the Game

## Start the Game

```bash
python main.py
```

---

# Running Multiplayer Server

Start the server separately:

```bash
python server.py
```

The server listens on:

```text
PORT 5555
```

Default host inside `network.py`:

```python
self.host = '26.52.208.28'
```

Replace it with:
- Your local IP
- VPS IP

depending on your setup.

---

# Controls

| Key / Action | Function |
|---|---|
| Mouse Click | Drop token / interact with UI |
| ENTER | Open/send chat |
| ESC | Close chat |
| F11 | Toggle fullscreen |

---

# AI Overview

The AI uses:

## Minimax Algorithm
Recursively explores future moves to maximize winning chances.

## Alpha-Beta Pruning
Optimizes minimax by removing unnecessary branches.

## Board Evaluation
Scores:
- Center control
- Potential connect4 windows
- Blocking opponent threats

---

# Multiplayer Architecture

The multiplayer system is built using:
- Python sockets
- Threads
- Pickle serialization

## Features

- Room creation/joining
- State synchronization
- Disconnect detection
- Reconnection handling
- Rematch support
- Real-time chat

---

# Assets

All textures/images are inside:

```text
assets/
```

Required files that are needed for the project to execute succesfully (you can create your own and replace them if you wish):

```text
bg.png
board.png
logo.png
token_p1.png
token_p2.png
```

---

