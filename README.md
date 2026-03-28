# top-down-rpg-01

A top-down RPG game built with Python and [Pygame](https://www.pygame.org/).

## Features
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
python main.py
```

## Controls
| Key | Action |
|-----|--------|
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
