# top-down-rpg-01

A top-down RPG game built with Python and [pygame](https://www.pygame.org/).

## Features
- Tile-based map loaded from a text file
- Player movement (WASD / arrow keys) with wall collision
- Camera that keeps the player centered on screen

## Requirements
- Python 3.10+
- pygame 2.5+

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
python main.py
```

## Controls
| Key | Action |
|-----|--------|
| W / arrow up | Move up |
| S / arrow down | Move down |
| A / arrow left | Move left |
| D / arrow right | Move right |
| Esc | Quit |

## Project Structure
```
top-down-rpg-01/
+-- main.py               # Entry point
+-- requirements.txt      # Python dependencies
+-- game/
|   +-- __init__.py
|   +-- settings.py       # Constants and configuration
|   +-- game.py           # Main Game class and loop
|   +-- player.py         # Player class
|   +-- tile.py           # Tile class
|   +-- tilemap.py        # TileMap loader
|   +-- camera.py         # Camera class
|   +-- maps/
|       +-- map_01.txt    # Sample map
+-- .github/
    +-- copilot-instructions.md
```

## Map Format
Map files are plain text files stored in `game/maps/`. Each character represents one tile:

| Character | Tile type |
|-----------|-----------|
| `W` | Wall |
| `.` | Floor |
| `P` | Player spawn (treated as floor) |
