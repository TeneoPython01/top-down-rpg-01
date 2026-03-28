# Agent Instructions for top-down-rpg-01

## Repository Purpose
A top-down RPG game implemented in Python using pygame.

## Key Files and Their Roles
| File | Purpose |
|------|---------|
| `main.py` | Entry point — creates and runs the `Game` object |
| `game/settings.py` | All constants: screen dimensions, FPS, tile size, colors |
| `game/game.py` | `Game` class — main loop, event handling, update, draw |
| `game/player.py` | `Player` class — input-driven movement, collision |
| `game/tile.py` | `Tile` class — a single map tile (wall or floor) |
| `game/tilemap.py` | `TileMap` class — loads map from `.txt`, stores `Tile` list |
| `game/camera.py` | `Camera` class — offset that keeps player centered |
| `game/maps/map_01.txt` | Sample map data |

## Development Guidelines
- Keep all magic numbers in `game/settings.py`.
- Player movement should be frame-rate independent (multiply by `dt`).
- The camera offset is applied when drawing sprites; do not modify sprite positions directly.
- Map files use the following tile codes:
  - `W` — wall tile
  - `.` — floor tile
  - `P` — player spawn point (treated as floor in the tile map)
- When adding a new feature, add its constants to `settings.py` first, then implement the class.
- Run `python main.py` to test changes interactively.

## Testing
There is no automated test suite yet. Verify changes by running the game with `python main.py`.
