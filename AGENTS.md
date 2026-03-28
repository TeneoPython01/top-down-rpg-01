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
