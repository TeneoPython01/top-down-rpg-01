# top-down-rpg-01

<<<<<<< HEAD
A top-down RPG game built with Python and [Pygame](https://www.pygame.org/).

## Features
<<<<<<< HEAD
- Tile-based maps loaded from CSV files
- Player movement with arrow keys or WASD
- Camera that follows the player and clamps to map edges
- Tile collision detection (walls, water)
- HUD showing player coordinates

## Requirements
- Python 3.8+
- Pygame 2.5+

## Setup
```bash
pip install -r requirements.txt
=======
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
=======
A top-down RPG game built with Python and [pygame](https://www.pygame.org/).

## Features
- Tile-based map loaded from a text file
- Player movement (WASD / arrow keys) with wall collision
- Camera that keeps the player centered on screen
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df

## Requirements
- Python 3.10+
- pygame 2.5+

<<<<<<< HEAD
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
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
python main.py
```

## Controls
| Key | Action |
|-----|--------|
<<<<<<< HEAD
<<<<<<< HEAD
| Arrow Keys / WASD | Move player |
| ESC | Quit |

## Project Structure
```
top-down-rpg-01/
├── main.py              # Entry point
├── requirements.txt
├── game/
│   ├── settings.py      # Constants (screen size, tile IDs, colors, …)
│   ├── player.py        # Player sprite with movement & collision
│   ├── tile.py          # Individual tile sprite
│   ├── tilemap.py       # Map loader (CSV → Tile objects)
│   ├── camera.py        # Camera that follows the player
│   └── game.py          # Main game loop
├── data/
│   └── maps/
│       └── map01.csv    # Starter map
└── assets/
    └── images/          # Sprite/tile images (placeholder)
```

## Map Format
Maps are CSV files in `data/maps/`. Each cell is an integer tile ID:
| ID | Tile | Walkable |
|----|------|----------|
| -1 | Empty | Yes |
| 0  | Grass | Yes |
| 1  | Wall | No |
| 2  | Water | No |
| 3  | Path | Yes |
=======
=======
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
| W / ↑ | Move up |
| S / ↓ | Move down |
| A / ← | Move left |
| D / → | Move right |
| Esc | Quit |

<<<<<<< HEAD
## Map Format
Maps are stored as plain-text files in `game/maps/`. Each character represents one tile:

| Character | Tile |
|-----------|------|
| `.` | Grass (walkable) |
| `#` | Wall (blocks movement) |
| `~` | Water (walkable, cosmetic) |

## License
MIT
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
## Project Structure
```
top-down-rpg-01/
├── main.py               # Entry point
├── requirements.txt      # Python dependencies
├── game/
│   ├── __init__.py
│   ├── settings.py       # Constants and configuration
│   ├── game.py           # Main Game class and loop
│   ├── player.py         # Player class
│   ├── tile.py           # Tile class
│   ├── tilemap.py        # TileMap loader
│   ├── camera.py         # Camera class
│   └── maps/
│       └── map_01.txt    # Sample map
└── .github/
    └── copilot-instructions.md
```

## Map Format
Map files are plain text files stored in `game/maps/`. Each character represents one tile:

| Character | Tile type |
|-----------|-----------|
| `W` | Wall |
| `.` | Floor |
| `P` | Player spawn (treated as floor) |

>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
