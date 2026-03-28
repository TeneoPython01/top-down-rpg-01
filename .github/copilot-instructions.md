# Copilot Instructions for top-down-rpg-01

## Project Overview
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
```bash
pip install -r requirements.txt
python main.py
```
