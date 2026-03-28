# Copilot Instructions for top-down-rpg-01

## Project Overview
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
```bash
pip install -r requirements.txt
python main.py
```
