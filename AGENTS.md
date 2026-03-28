<<<<<<< HEAD
# AGENTS.md — AI Agent Instructions for top-down-rpg-01

This file provides guidance for AI coding agents (GitHub Copilot, Codex, etc.) working on this repository.

## Repository Purpose
A top-down RPG game written in Python using Pygame. The goal is a playable game with tile-based maps, a moveable player, camera tracking, and collision detection.

## Getting Started
1. Install dependencies: `pip install -r requirements.txt`
2. Run the game: `python main.py`
3. There are no automated tests yet; verify changes by running the game.

## Key Conventions
- **Settings first**: All magic numbers (screen size, tile size, FPS, colors) live in `game/settings.py`.
- **One class per file**: Each module in `game/` contains exactly one primary class.
- **Camera-aware rendering**: Every sprite/tile must apply the camera offset when drawing. Use `camera.apply(rect)` to get the screen-space rectangle.
- **CSV maps**: Map data lives in `data/maps/` as CSV files. Each cell is an integer tile ID. `-1` means no tile (empty/passable). Tile IDs ≥ 0 are rendered and treated as solid by default unless marked walkable in `TileMap`.

## Do's
- Add new game entities as new classes in `game/`
- Use `pygame.sprite.Group` for batches of similar objects
- Prefer surface blitting over drawing primitives for sprites
- Keep the game loop in `game/game.py` — do not add game logic to `main.py`

## Don'ts
- Do not hardcode pixel values outside of `game/settings.py`
- Do not import from `main.py` in any game module
- Do not modify `LICENSE`

## Running and Testing
There is no automated test suite. To validate changes:
1. Run `python main.py` and verify the game window opens
2. Walk the player character around to test movement and collision
3. Confirm the camera follows the player correctly

## Commit Style
Use short imperative messages, e.g. `Add enemy class`, `Fix collision detection`, `Update tile rendering`.
=======
# AGENTS.md — AI Agent Instructions

## Repository: top-down-rpg-01

### Purpose
This repository contains a top-down RPG game in Python/Pygame. When contributing code, follow the conventions below.

### File Structure
```
top-down-rpg-01/
├── main.py              # Entry point
├── requirements.txt     # Python dependencies
├── game/
│   ├── __init__.py
│   ├── settings.py      # Constants and configuration
│   ├── game.py          # Game loop
│   ├── player.py        # Player class
│   ├── tile.py          # Tile class
│   ├── tilemap.py       # TileMap class
│   ├── camera.py        # Camera class
│   └── maps/
│       └── map_01.txt   # Sample map
└── README.md
```

### Coding Guidelines
1. All constants belong in `game/settings.py`.
2. New game entities should extend `pygame.sprite.Sprite`.
3. Map files use plain text: `.` = walkable tile, `#` = wall tile, each row on its own line.
4. Keep the game loop logic in `game/game.py`; avoid mixing rendering with logic.
5. Follow PEP 8. Run `flake8` before committing.

### Testing
- Currently no automated test suite. Manual playtesting via `python main.py`.
- When adding features, verify the game still runs without errors.

### Dependencies
- Python 3.10+
- pygame (see `requirements.txt`)
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
