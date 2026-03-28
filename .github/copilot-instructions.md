# Copilot Instructions for top-down-rpg-01

## Project Overview
<<<<<<< HEAD
<<<<<<< HEAD
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
=======
This is a top-down RPG game built with Python and Pygame. The game features tile-based maps, a player character, camera system, and basic movement mechanics.

## Architecture
- `main.py` — Entry point; instantiates and runs the Game class.
- `game/settings.py` — All game constants (screen size, FPS, tile size, colors, speeds).
- `game/game.py` — Main `Game` class with the game loop (events, update, draw).
- `game/player.py` — `Player` class; handles sprite, position, and input-based movement.
- `game/tile.py` — `Tile` class representing a single map tile.
- `game/tilemap.py` — `TileMap` class; loads a map from a text file and renders tiles.
- `game/camera.py` — `Camera` class; offsets rendering so the player stays centred.
- `game/maps/` — Text files defining tile layouts (`.` = grass, `#` = wall).

## Coding Conventions
- Python 3.10+, PEP 8 style.
- Use `pygame.sprite.Sprite` for drawable entities.
- Keep all magic numbers in `game/settings.py`.
- Prefer composition over inheritance beyond the base `Sprite`.

## Running the Game
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
This is a top-down RPG game built with Python and pygame.

## Project Structure
- `main.py` - Entry point; initializes and runs the game
- `game/` - Main game package
  - `settings.py` - Game constants and configuration (screen size, FPS, tile size, colors)
  - `player.py` - Player class with movement and animation
  - `tile.py` - Tile class representing individual map tiles
  - `tilemap.py` - TileMap class for loading and rendering the map
  - `camera.py` - Camera class that follows the player
  - `game.py` - Main Game class containing the game loop
  - `maps/` - Map data files (`.txt` format)

## Coding Conventions
- Use Python 3.10+
- Follow PEP 8 style guidelines
- Keep game logic in the `game/` package; `main.py` should only bootstrap the game
- Use `pygame.Vector2` for positions and velocities
- All game constants belong in `game/settings.py`
- Map files use single-character codes: `W` = wall, `.` = floor, `P` = player spawn

## Dependencies
- pygame (see `requirements.txt`)

## Running the Game
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
```bash
pip install -r requirements.txt
python main.py
```
<<<<<<< HEAD
<<<<<<< HEAD

## Controls
- **Arrow Keys / WASD**: Move the player
- **ESC**: Quit the game

## Expanding the Game
When adding new features:
1. Create new modules in the `game/` directory
2. Add any new constants to `game/settings.py`
3. Register new objects in the `Game` class
4. Keep game logic separate from rendering logic where possible
=======
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
