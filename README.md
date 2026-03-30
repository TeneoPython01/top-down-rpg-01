# top-down-rpg-01

A top-down RPG built with Python and [pygame](https://www.pygame.org/) — set in a
post-pandemic fantasy world called the Verdant Plains.

## Features

### Exploration
- Tile-based overworld map with wall/water collision
- Player movement (WASD / arrow keys) with camera that follows the player
- **Five overworld zones** connected by zone-exit transitions: Verdant Plains, Silverwood Forest, Stormcrag Mountains, Dark Lands, and Subterra Passage (secret)
- **Four towns** to visit: **Ironhaven**, **Ashenvale**, **Willowmere**, and **Subterra**
- Town exploration: shop and inn event tiles, NPC interaction
- Humanoid NPC sprites with name labels; press **Z** to start a conversation
- Treasure chests scattered across every zone containing items and gold
- Hidden wall in Stormcrag Mountains that opens a secret passage to Subterra Passage
- Dungeon entrances in each zone leading to boss encounters

### Story & Presentation
- **Title screen** with a starfield background
- **Scripted intro cutscene** — two-phase sequence:
  - Phase 1: full-screen narration panels (auto-advance or skip with Z/Enter)
  - Phase 2: animated characters move and speak on the overworld map
  - Press **\\** (Backslash) at any time to skip the entire intro
- Typewriter dialog boxes with speaker banners
- **Corner mini-map** overlay on the overworld (press **M** to toggle); full-screen world map with zone labels and player marker

### Battle System
- Step-based **random encounter** system on grassland tiles
- **Turn-based battle** with a Speed-based turn queue
- Player battle commands: **Attack**, **Magic**, **Item**, **Defend**, **Flee**
- Status effects (e.g. Blind) that affect hit rates
- **Floating damage / healing numbers** animate above targets in battle
- **Battle speed setting** — Normal, Fast, or Instant to reduce animation wait time

### RPG Progression
- Full RPG stats: HP, MP, STR, DEF, MAG, MDF, SPD, LCK, Gold
- Level-up system — stat growth and automatic spell learning
- Magic system with spells loaded from `data/spells.json`
- Inventory and equipment system (weapons, armour, accessories)
- Pause menu with seven tabs: **Items**, **Equipment**, **Magic**, **Stats**, **Quests**, **Save**, **Options**
  - Secret **Cheats** tab unlockable via the Konami code (↑↑↓↓←→←→) while viewing the Quests tab
- Inn — pay gold to restore HP and MP fully
- **Quest log** — track active objectives and collect gold, item, and spell rewards on completion

### Audio
- Background music (BGM) for title, overworld, town, battle, boss battle, cutscene, victory, and game over
- Sound effects (SFX) for menu cursor, confirm/cancel, attack, spell cast, item use, level up, door open, and dialog
- Audio gracefully degrades — game runs normally when audio files are absent

### Systems
- Quest flag system for tracking story progression
- Quest log — full objectives, flag-driven completion, and rewards (`data/quests.json`)
- JSON save / load system with multiple save slots (accessible from the **Save** tab in the pause menu)
- **Options / Settings menu** — adjust music volume, SFX volume, battle speed, and text speed; settings are persisted to `data/config.json` and loaded at startup. Accessible from the title screen and the pause menu's **Options** tab.

## Requirements
- Python 3.10+
- pygame 2.5+

## Setup

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the game
python run.py
```

## Controls

| Key | Action |
|-----|--------|
| W / ↑ | Move up |
| S / ↓ | Move down |
| A / ← | Move left |
| D / → | Move right |
| Z / Enter | Interact with NPC / Confirm menu selection |
| M | Toggle mini-map overlay (overworld) |
| Esc | Open pause menu / Go back |
| \\ (Backslash) | Skip intro cutscene |

## Project Structure

```
top-down-rpg-01/
├── run.py                   # Entry point
├── settings.py              # Global constants and configuration
├── requirements.txt         # Python dependencies
├── data/                    # Game data files
│   ├── items.json           # Item definitions
│   ├── spells.json          # Spell definitions
│   ├── enemies.json         # Enemy definitions
│   ├── encounters.json      # Random encounter zone tables
│   ├── levels.json          # Level-up stat table
│   ├── shops.json           # Shop inventories
│   ├── dialog.json          # NPC dialog scripts
│   ├── quests.json          # Quest definitions (objectives, rewards, flags)
│   └── maps/
│       └── map01.csv        # Overworld tile map (CSV)
├── assets/                  # Game assets
│   ├── music/               # BGM tracks (WAV/OGG)
│   ├── sfx/                 # Sound effects (WAV)
│   ├── sprites/             # Player, enemy, and NPC sprites
│   ├── tilesets/            # Tileset images
│   └── ui/                  # UI graphics
└── src/                     # Game source code
    ├── game.py              # Main loop and state-machine manager
    ├── states/
    │   ├── title.py         # Title screen
    │   ├── intro.py         # Scripted intro cutscene
    │   ├── overworld.py     # Overworld exploration
    │   ├── battle.py        # Turn-based battle
    │   ├── town.py          # Town exploration
    │   ├── shop.py          # Shop (buy / sell)
    │   ├── inn.py           # Inn (rest to restore HP/MP)
    │   ├── dialog.py        # Dialog overlay
    │   ├── pause_menu.py    # Pause / inventory menu
    │   ├── options.py       # Options / Settings menu
    │   ├── world_map.py     # Full-screen world map
    │   ├── fade.py          # Fade-to-black screen transition overlay
    │   └── game_over.py     # Game over screen
    ├── entities/
    │   ├── player.py        # Player entity and RPG stats
    │   ├── enemy.py         # Enemy entity
    │   └── npc.py           # NPC entity
    ├── systems/
    │   ├── audio.py         # BGM and SFX manager
    │   ├── battle_engine.py # Damage, hit, and crit formulas
    │   ├── config.py        # Persistent player-adjustable options
    │   ├── encounter.py     # Random encounter system
    │   ├── magic.py         # Spell definitions and casting logic
    │   ├── inventory.py     # Inventory and equipment management
    │   ├── camera.py        # Camera that follows the player
    │   ├── save_load.py     # JSON save / load (multiple slots)
    │   ├── quest_flags.py   # Story progression flags
    │   └── quest_log.py     # Quest log (objectives, state, rewards)
    └── ui/
        ├── text_box.py      # Typewriter dialog box with speaker banner
        ├── menu.py          # Reusable menu widget
        ├── hud.py           # In-game HUD
        ├── battle_hud.py    # Battle HUD
        └── floating_text.py # Floating damage / heal numbers in battle
```

## Tile IDs

Tile colours are defined in `settings.py`; the overworld map uses the following IDs:

| ID | Constant | Description |
|----|----------|-------------|
| 0 | `TILE_GRASS` | Walkable grassland (encounter zone) |
| 1 | `TILE_WALL` | Impassable wall |
| 2 | `TILE_WATER` | Impassable water |
| 3 | `TILE_PATH` | Walkable path (no encounters) |
| 4 | `TILE_TOWN` | Town entrance marker |
| 5 | `TILE_ZONE_EXIT` | Zone transition tile (leads to the adjacent overworld zone) |
| 6 | `TILE_DUNGEON` | Dungeon / boss arena entrance |
| 7 | `TILE_HIDDEN` | Hidden interactable tile (e.g. secret wall in Subterra) |
| 8 | `TILE_CHEST` | Treasure chest (walkable; triggers chest reward on step) |
