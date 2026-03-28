# Copilot Instructions for top-down-rpg-01

## Project Overview
This is a top-down RPG game built with Python and Pygame. The game features tile-based maps, a player character with movement, a camera that follows the player, and collision detection.

## Tech Stack
- **Language**: Python 3.8+
- **Game Library**: Pygame
- **Structure**: Object-oriented, modular design

## Project Structure
```
top-down-rpg-01/
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── game/
│   ├── __init__.py
│   ├── settings.py      # Game constants and configuration
│   ├── player.py        # Player class
│   ├── tile.py          # Tile class
│   ├── tilemap.py       # TileMap class (map loading/management)
│   ├── camera.py        # Camera class (follows player)
│   └── game.py          # Main Game class (game loop)
├── assets/
│   └── images/          # Sprite and tile images
└── data/
    └── maps/            # Map data files (CSV)
```

## Coding Guidelines
- Use Python type hints where practical
- Keep classes focused on a single responsibility
- Use constants from `settings.py` rather than magic numbers
- All game dimensions use pixels; tile sizes are defined in `settings.py`
- Follow PEP 8 style conventions
- Write docstrings for all public classes and methods

## Game Architecture
- `Game` class in `game/game.py` owns the main game loop
- `Camera` offsets drawing positions so the player stays centered
- `TileMap` loads CSV map data and stores `Tile` objects in a 2D list
- `Player` handles input, movement, and collision against the tile map

## How to Run
```bash
pip install -r requirements.txt
python main.py
```

## Controls
- **Arrow Keys / WASD**: Move the player
- **ESC**: Quit the game

## Expanding the Game
When adding new features:
1. Create new modules in the `game/` directory
2. Add any new constants to `game/settings.py`
3. Register new objects in the `Game` class
4. Keep game logic separate from rendering logic where possible
