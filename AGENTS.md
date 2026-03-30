# Agent Instructions for top-down-rpg-01

## Repository Purpose
A top-down RPG game implemented in Python using pygame-ce, set in a post-pandemic fantasy world called the Verdant Plains.

## Key Files and Their Roles
| File | Purpose |
|------|---------|
| `run.py` | Entry point — creates and runs the `Game` object |
| `settings.py` | All constants: screen dimensions, FPS, tile IDs, colours, paths |
| `src/game.py` | `Game` class — main loop, state-machine stack, shared systems |
| `src/states/title.py` | Title screen with starfield |
| `src/states/intro.py` | Scripted intro cutscene (narration panels + character animation) |
| `src/states/overworld.py` | Overworld exploration: movement, encounters, zone/town/dungeon transitions, chests, hidden walls |
| `src/states/battle.py` | Turn-based battle (SPD queue, magic, items, flee, boss AI, animations) |
| `src/states/town.py` | Town exploration (shop/inn tiles, NPC interaction) |
| `src/states/shop.py` | Buy/sell shop UI |
| `src/states/inn.py` | Inn rest screen (restore HP/MP for gold) |
| `src/states/dialog.py` | Dialog overlay (typewriter text box with speaker banner) |
| `src/states/pause_menu.py` | Pause menu (Items, Equipment, Magic, Stats, Quests, Save tabs; secret Cheats tab) |
| `src/states/fade.py` | Fade-to-black overlay used for all cross-map transitions |
| `src/states/game_over.py` | Game over screen |
| `src/entities/player.py` | Player entity: movement, RPG stats, level-up, serialisation |
| `src/entities/enemy.py` | Enemy entity |
| `src/entities/npc.py` | NPC entity (humanoid sprite + name label) |
| `src/systems/audio.py` | `AudioManager` — BGM streaming and SFX playback |
| `src/systems/battle_engine.py` | Damage/hit/crit formulas, turn ordering, status effects |
| `src/systems/encounter.py` | Step-based random encounter system |
| `src/systems/magic.py` | Spell loading, casting logic |
| `src/systems/inventory.py` | Item storage, use, equip/unequip, stat recalculation |
| `src/systems/camera.py` | Camera that follows the player |
| `src/systems/save_load.py` | JSON save/load (multiple slots) |
| `src/systems/quest_flags.py` | Boolean story-progression flags |
| `src/systems/quest_log.py` | Quest log: objectives, state tracking, reward granting |
| `src/ui/text_box.py` | Typewriter dialog box with speaker banner |
| `src/ui/menu.py` | Reusable menu widget (bobbing cursor, SFX) |
| `src/ui/hud.py` | In-game HUD (HP/MP bars, area name) |
| `src/ui/battle_hud.py` | Battle HUD (command menu, HP/MP bars, enemy list) |
| `src/utils/tilemap.py` | Hardcoded 2-D tile maps for all zones and zone registry |
| `src/utils/town_maps.py` | Hardcoded 2-D tile maps for all towns and town registry |
| `src/utils/animation.py` | Frame-based animation controller |
| `src/utils/spritesheet.py` | Spritesheet loader/slicer |
| `data/items.json` | Item definitions (consumables, equipment) |
| `data/spells.json` | Spell definitions (cost, power, element, learn level) |
| `data/enemies.json` | Enemy stats and loot tables |
| `data/encounters.json` | Zone-based random encounter tables |
| `data/levels.json` | Level-up XP thresholds and absolute stat values |
| `data/shops.json` | Shop inventories per town |
| `data/dialog.json` | NPC dialog scripts (keyed by dialog_id) |
| `data/quests.json` | Quest definitions (triggers, objectives, complete flags, rewards) |

## Development Guidelines
- Keep all magic numbers and paths in `settings.py` (root, not inside `src/`).
- All tile IDs are `TILE_*` constants in `settings.py`; when adding a new tile type define its constant and colour there first.
- Overworld zones and town maps are hardcoded 2-D arrays in `src/utils/tilemap.py` and `src/utils/town_maps.py` respectively; register them in the zone/town registry at the bottom of each file.
- Player movement is frame-rate independent (multiply by `dt`); grid-based stepping handled in `player.update()`.
- The camera offset is applied at draw time; never modify sprite positions directly in the draw path.
- When adding a new feature, add its constants to `settings.py` first, then implement the class in the appropriate `src/` subpackage.
- New states must inherit from `src/states/base_state.py:BaseState`; set `is_overlay = True` for transparent overlay states.
- Audio calls should go through `game.audio` (the shared `AudioManager`); the manager fails silently if audio files are absent.
- Save data is serialised through `Player.to_dict()` / `Player.from_dict()`; keep the schema backward-compatible.

## Running the Game
```bash
pip install -r requirements.txt
python run.py
```

## Testing
Run the automated test suite with:
```bash
python -m pytest tests/ -v
```
All 56 tests cover the player entity (stats, level-up, serialisation), battle engine (damage, hit/crit, turn order), and map transitions (town-exit spawn, zone-to-zone transitions).
