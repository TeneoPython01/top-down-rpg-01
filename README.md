# top-down-rpg-01

A top-down RPG game built with Python and [Pygame](https://www.pygame.org/).

## Features
- Tile-based map loaded from a plain-text file
- Player character with smooth 4-directional movement (WASD / arrow keys)
- Wall collision detection
- Camera that follows the player and clamps to map bounds
- Easily extensible architecture

## Project Structure
```
top-down-rpg-01/
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── game/
│   ├── __init__.py
│   ├── settings.py      # Constants and configuration
│   ├── game.py          # Game class and main loop
│   ├── player.py        # Player class
│   ├── tile.py          # Tile class
│   ├── tilemap.py       # TileMap class
│   ├── camera.py        # Camera class
│   └── maps/
│       └── map_01.txt   # Sample map
└── README.md
```

## Requirements
- Python 3.10+
- pygame 2.5+

## Setup & Running
```bash
# 1. Clone the repo
git clone https://github.com/TeneoPython01/top-down-rpg-01.git
cd top-down-rpg-01

# 2. (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the game
python main.py
```

## Controls
| Key | Action |
|-----|--------|
| W / ↑ | Move up |
| S / ↓ | Move down |
| A / ← | Move left |
| D / → | Move right |
| Esc | Quit |

## Map Format
Maps are stored as plain-text files in `game/maps/`. Each character represents one tile:

| Character | Tile |
|-----------|------|
| `.` | Grass (walkable) |
| `#` | Wall (blocks movement) |
| `~` | Water (walkable, cosmetic) |

## License
MIT
