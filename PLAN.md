# Plan: Top-Down RPG — Post-Pandemic Fantasy

## TL;DR

Build a Final Fantasy-style top-down RPG using **Pygame-CE** (Python). The game features overworld exploration, random turn-based encounters, towns with shops/NPCs, and a story about a White Knight vs. Black Knight in a world 100 years after a pandemic. Architecture uses a **state machine** pattern with data-driven content (JSON for items, spells, enemies). Built in 6 incremental phases, each producing a playable milestone.

**Setting:** Lush, overgrown post-pandemic world. 99.5% of humanity gone 100 years ago. Sparse villages, overpopulated aggressive beasts, magic has returned. White Knight (protector) vs. Black Knight (warlord).

---

## Architecture

### Tech Stack

- **Engine:** Pygame-CE (actively maintained Pygame fork)
- **Maps:** Tiled Map Editor → TMX files loaded via `pytmx` + `pyscroll` (scrolling camera)
- **Data:** JSON files for items, spells, enemies, dialog, shops
- **Art:** 16-bit SNES style, 16x16 tile grid, 32x32 or 48x48 character sprites (free tilesets from OpenGameArt / itch.io initially)
- **Resolution:** 256×224 native (SNES-like), scaled up 3x to 768×672 window
- **Audio:** Pygame mixer, OGG/WAV files (free chiptune/RPG packs from itch.io / OpenGameArt initially)

### Core Pattern: State Machine

The game loop delegates to the current state. States manage their own input, update, and rendering.

```
States: Title → Overworld ↔ Battle
                         ↔ Town → Shop / Dialog / Inn
                         ↔ PauseMenu (inventory, equipment, stats, save)
        Battle → Victory → Overworld
               → Defeat → Game Over → Title
```

### Project Structure

```
top-down-rpg-01/
├── run.py                  # Entry point
├── requirements.txt        # pygame-ce, pytmx, pyscroll
├── settings.py             # Constants (resolution, FPS, colors, paths)
├── src/
│   ├── game.py             # Game class: loop, state manager
│   ├── states/
│   │   ├── base_state.py   # Abstract state (enter/exit/update/draw/handle_input)
│   │   ├── title.py        # Title screen
│   │   ├── overworld.py    # Overworld exploration + random encounters
│   │   ├── battle.py       # Turn-based battle
│   │   ├── town.py         # Town exploration (subset of overworld mechanics)
│   │   ├── shop.py         # Buy/sell UI
│   │   ├── dialog.py       # NPC dialog state (overlay)
│   │   ├── pause_menu.py   # Inventory, equipment, stats, save
│   │   └── game_over.py    # Game over screen
│   ├── entities/
│   │   ├── player.py       # Player entity (stats, equipment, position, sprites)
│   │   ├── npc.py          # NPC entity (dialog ref, position, sprite)
│   │   └── enemy.py        # Enemy template (stats, sprite, loot table, AI)
│   ├── systems/
│   │   ├── battle_engine.py    # Turn order, damage calc, status effects
│   │   ├── magic.py            # Spell definitions, casting, MP management
│   │   ├── inventory.py        # Item storage, use, equip/unequip
│   │   ├── encounter.py        # Step counter, encounter rate, zone tables
│   │   ├── camera.py           # Follow-cam with map bounds clamping
│   │   ├── save_load.py        # Serialize/deserialize game state to JSON
│   │   └── quest_flags.py      # Story progression flags
│   ├── ui/
│   │   ├── text_box.py     # Dialog box with typewriter text
│   │   ├── menu.py         # Reusable menu component (cursor, selection)
│   │   ├── hud.py          # Overworld HUD (minimap, HP bar)
│   │   └── battle_hud.py   # Battle UI (HP/MP bars, command menu, enemy list)
│   └── utils/
│       ├── spritesheet.py  # Load and slice spritesheets
│       ├── animation.py    # Frame-based animation controller
│       └── tilemap.py      # TMX map loader wrapper
├── assets/
│   ├── maps/               # .tmx files (overworld, towns, dungeons)
│   ├── tilesets/            # Tileset PNGs for Tiled
│   ├── sprites/
│   │   ├── player/         # White Knight walk/battle sprites
│   │   ├── enemies/        # Enemy battle sprites
│   │   └── npcs/           # NPC sprites
│   ├── ui/                 # Menu frames, cursors, icons
│   ├── music/              # BGM (OGG)
│   └── sfx/                # Sound effects (WAV)
└── data/
    ├── items.json           # All items (healing, equipment, key items)
    ├── spells.json          # All spells with costs, effects, elements
    ├── enemies.json         # Enemy stats, AI patterns, loot
    ├── encounters.json      # Zone-based encounter tables
    ├── shops.json           # Shop inventories per town
    ├── dialog.json          # NPC dialog trees
    └── levels.json          # XP thresholds, stat gains per level
```

---

## Game Design

### Stats (FF-style)

- **HP** / **MP** — Health and Magic points
- **STR** — Physical attack power
- **DEF** — Physical defense
- **MAG** — Magic attack power
- **MDF** — Magic defense
- **SPD** — Turn order priority, flee chance
- **LCK** — Critical hit rate, item drop rate
- **Level** / **EXP** — Standard leveling system

### Damage Formulas

- Physical: `damage = (attacker.STR * attack_power / 2) - (target.DEF * armor_defense / 4)`
- Magical: `damage = (caster.MAG * spell_power) - (target.MDF * resist / 4)`
- Critical: 2x damage, chance = `LCK / 256`
- Variance: ±10% random modifier

### Elements

Fire, Ice, Lightning, Earth, Wind, Water, Holy, Dark

- Enemies have weaknesses/resistances (0.5x, 1x, 2x multipliers)
- Equipment can grant elemental resistance

### Spells (White Knight learns both White and some Black magic)

**White Magic:**

| Spell | MP | Effect | Learn Lv |
|-------|----|--------|----------|
| Cure | 4 | Heal ~100 HP | 1 |
| Protect | 6 | +50% DEF for 5 turns | 5 |
| Cura | 12 | Heal ~400 HP | 12 |
| Shell | 8 | +50% MDF for 5 turns | 15 |
| Raise | 20 | Revive ally (50% HP) | 20 |
| Holy | 30 | Heavy Holy damage | 30 |

**Black Magic:**

| Spell | MP | Effect | Learn Lv |
|-------|----|--------|----------|
| Fire | 5 | Fire damage (single) | 3 |
| Blizzard | 5 | Ice damage (single) | 6 |
| Thunder | 5 | Lightning damage (single) | 9 |
| Fira | 15 | Heavy Fire damage | 18 |
| Blizzara | 15 | Heavy Ice damage | 22 |
| Thundara | 15 | Heavy Lightning damage | 26 |

**Support:**

| Spell | MP | Effect | Learn Lv |
|-------|----|--------|----------|
| Scan | 2 | Reveal enemy stats | 1 |
| Haste | 8 | +50% SPD for 5 turns | 10 |
| Slow | 6 | -50% SPD, 3 turns (enemy) | 8 |
| Dispel | 10 | Remove buffs/debuffs | 16 |

### Items

**Consumables:**

- Potion (Heal 100 HP) — 50 gold
- Hi-Potion (Heal 500 HP) — 300 gold
- Ether (Restore 30 MP) — 200 gold
- Hi-Ether (Restore 100 MP) — 800 gold
- Phoenix Down (Revive, 25% HP) — 500 gold
- Elixir (Full HP+MP) — rare/shops only
- Antidote (Cure Poison) — 30 gold
- Eye Drops (Cure Blind) — 30 gold
- Echo Herb (Cure Silence) — 50 gold
- Tent (Restore 50% HP/MP at save points) — 400 gold

**Battle Items:**

- Bomb Fragment (Fire damage ~200) — 200 gold
- Arctic Wind (Ice damage ~200) — 200 gold
- Zeus's Wrath (Lightning damage ~200) — 200 gold
- Smoke Bomb (Guaranteed flee) — 100 gold

### Equipment Slots

Weapon, Shield, Helmet, Armor, Accessory

### Status Effects

Poison (tick damage), Blind (-50% hit rate), Silence (can't cast), Sleep (skip turns, wake on hit), Haste, Slow, Protect, Shell

### Enemies (thematic — overpopulated, aggressive, magically mutated beasts)

**Grasslands (Lv 1-8):**

- Dire Wolf (HP 45, weak to Fire)
- Giant Rat (HP 25)
- Feral Boar (HP 60, high DEF)
- Venomous Viper (HP 30, can Poison)

**Forest (Lv 8-15):**

- Shadow Panther (HP 120, high SPD)
- Thunder Hawk (HP 90, Lightning attacks)
- Iron Bear (HP 200, very high DEF)
- Poison Toad (HP 70, Poison + Blind)

**Mountains (Lv 15-22):**

- Rock Golem (HP 350, immune to physical)
- Storm Drake (HP 280, Lightning + Wind)
- Crystal Stag (HP 180, casts Cure, high LCK drops)
- Fire Lizard (HP 220, Fire attacks, weak to Ice)

**Dark Lands (Lv 22-30):**

- Black Knight Soldier (HP 300, human enemy)
- Corrupted Wolf (HP 250, Dark element)
- Nightmare Stallion (HP 400, casts Haste on self)
- Dark Mage (HP 200, casts black magic)

**Bosses:**

- Dire Wolf Alpha (end of Act 1, Lv ~8)
- Black Knight Lieutenant (mid Act 2, Lv ~18)
- Corrupted Beast King (end of Act 2, Lv ~25)
- The Black Knight (final boss, Lv ~30)

---

## Story Outline

### Act 1 — "The Quiet Village" (Lv 1-8)

The White Knight lives in Ashenvale, a peaceful farming village. Strange beast attacks increase. Village elder asks the Knight to investigate. Journey to the nearby Silverwood Forest. Defeat the Dire Wolf Alpha. Discover evidence of someone driving beasts toward settlements deliberately.

### Act 2 — "The Rising Shadow" (Lv 8-22)

Travel across the Verdant Plains to warn other villages. Visit Ironhaven (mining town, buy better equipment). Learn of the Black Knight's army gathering in the northern Dark Lands. Meet a traveling healer NPC who provides clues about magic's return. Cross the Stormcrag Mountains. Encounter and defeat the Black Knight's Lieutenant. Discover the Black Knight is harnessing ancient magic from a pre-pandemic facility.

### Act 3 — "The Final Stand" (Lv 22-30)

Enter the Dark Lands. Push through the Black Knight's forces. Reach the Black Knight's fortress. Confront the Corrupted Beast King (guard). Face the Black Knight in the final battle. Ending: the world is freed from the Black Knight's tyranny, but the return of magic promises both hope and new dangers.

### World Map Locations

1. **Ashenvale** — Starting village (inn, basic shop, tutorial NPCs)
2. **Silverwood Forest** — First dungeon area
3. **Verdant Plains** — Overworld grasslands connecting locations
4. **Ironhaven** — Mining town (better equipment shop, quest NPCs)
5. **Stormcrag Mountains** — Mountain dungeon area
6. **Willowmere** — Lakeside hamlet (inn, magic shop)
7. **Dark Lands** — Final overworld region
8. **Black Fortress** — Final dungeon
9. **Subterra** — Hidden underground city *(secret, optional)*

---

## Secret Quest: "Subterra — The City Below"

### Discovery

In the Stormcrag Mountains, there is an unremarkable rock wall that looks slightly different from surrounding tiles (subtle texture variation — easy to miss). No NPC hints at this directly; the only clue is a cryptic journal entry found in Willowmere from a traveler who writes: *"The mountains breathe. I swear I felt warm air from solid stone."* Interacting with the wall reveals a hidden passage.

### Subterra — The Underground City

The passage leads to a vast underground cavern containing Subterra, a thriving city of ~5,000 people — more humans than the White Knight has ever seen. The city is lit by bioluminescent plants and pre-pandemic lighting technology they've maintained. The residents are polite but cautious of the surface world's dangers.

### Key NPCs in Subterra

- **Elder Marek** — City leader. Explains: during the pandemic collapse 100 years ago, a large group fled underground into an old military bunker complex. Over generations they expanded it into a full city. They chose to stay hidden, afraid the surface was still deadly. He asks the White Knight not to reveal them yet — they aren't ready.
- **Archivist Lena** — Runs the city library. Tells the White Knight that records show two families left Subterra 60 years ago, believing the surface was safe. One family's surname matches the White Knight's. She points him to the old residential quarter.
- **Merchant Dax** — Subterra has its own shop with unique items not found anywhere else:
  - Nano Potion (Heal 999 HP) — 2000 gold
  - Plasma Grenade (Heavy non-elemental damage ~800 to all enemies) — 1500 gold
  - Stasis Field (Inflicts Sleep on all enemies, 80% chance) — 1000 gold

### The Ancestral Home

In the old residential quarter, the White Knight finds his ancestors' house. Inside:

- **The Journal** — Written by his grandmother. Entries describe life in Subterra, the decision to leave for the surface, and her hope: *"Our children will see the sky. And if the world is broken, I believe they will be the ones to mend it. We leave behind our old tools — we won't need weapons where we're going. We go in peace."*
- **The Exo Weapon** — A pre-pandemic exosuit-powered sword. Mechanically enhanced blade with integrated energy projection. Best weapon in the game.
  - ATK +80 (compared to next best purchasable sword at +45)
  - Bonus: attacks deal hybrid physical+non-elemental magic damage
  - Visual: blade glows with faint blue energy
- **The Exo Armor** — A pre-pandemic exosuit chest piece. Lightweight mechanical armor with kinetic energy absorption.
  - DEF +60, MDF +40 (compared to next best purchasable armor at DEF +35)
  - Bonus: reduces all elemental damage by 25%
  - Visual: sleek, slightly futuristic plating under the knight's cloak

### Quest Flags

- `found_subterra` — opened the hidden passage
- `met_elder_marek` — spoke with the elder
- `found_ancestral_home` — entered the house
- `read_journal` — read the grandmother's journal
- `obtained_exo_weapon` — picked up the Exo Weapon
- `obtained_exo_armor` — picked up the Exo Armor

### Story Impact

None on the main storyline. No NPCs outside Subterra reference it. The Black Knight does not know about Subterra. The quest is purely a reward for exploration — the ultimate gear and an emotional story beat about the White Knight's origins.

### Enemies in the Passage (Lv 18-22)

- Cave Crawler (HP 200, high DEF, weak to Fire)
- Pale Lurker (HP 160, high SPD, can Blind)
- Crystal Sentinel (HP 400, immune to magic, guards the entrance to Subterra — mini-boss)

---

## Implementation Phases

### Phase 1: Core Engine & Overworld Movement ✅ COMPLETE

*Goal: Walk around a scrolling tile map*

**Steps:**

1. Initialize the project: `requirements.txt` (pygame-ce, pytmx, pyscroll), `run.py` entry point, `settings.py` constants
2. Implement `src/game.py` — Game class with the main loop (60 FPS, delta time, event pump, state manager)
3. Implement `src/states/base_state.py` — abstract state with `enter()`, `exit()`, `update(dt)`, `draw(surface)`, `handle_input(event)` methods
4. Implement `src/utils/spritesheet.py` — load a spritesheet PNG and slice into frames
5. Implement `src/entities/player.py` — Player class with 4-directional movement, animated walk cycle, collision rect
6. Create a simple test tilemap (hardcoded 2D array first, upgrade to TMX in Phase 4)
7. Implement `src/systems/camera.py` — camera follows player, clamps to map boundaries
8. Implement `src/states/overworld.py` — renders the tile map, player, handles movement input, tile collisions
9. Add `src/states/title.py` — simple title screen with "Press Enter to Start"

**Verification:**

- Player walks in 4 directions on a scrolling tile map
- Camera follows smoothly and stops at edges
- Collision with blocked tiles (water, walls) works
- Pressing Escape opens a placeholder pause state

**Dependencies:** None — this is the foundation.

---

### Phase 2: Battle System ✅ COMPLETE

*Goal: Random encounters trigger turn-based battles*

**Steps:**

1. Implement `src/systems/encounter.py` — step counter on overworld, configurable encounter rate per zone, triggers battle state
2. Define enemy data format in `data/enemies.json` — stats, elemental info, sprite reference, XP/gold rewards
3. Implement `src/entities/enemy.py` — Enemy class loaded from JSON, simple AI (random attack selection)
4. Implement `src/systems/battle_engine.py`:
   - Turn order calculation (SPD-based across all combatants — party list + enemy list — recalc each round)
   - Party abstraction: player side is a list of combatants (initially just `[white_knight]`), enemy side is a list
   - Target selection: player chooses target from enemy list; enemies pick from party list
   - Physical damage formula with variance
   - Hit/miss calculation (base 90% hit rate, modified by Blind)
   - Defend command (+50% DEF for one turn)
   - Flee calculation (SPD comparison, average party SPD vs average enemy SPD)
   - Victory: grant EXP + gold to all living party members, check level up for each
   - Defeat (all party members at 0 HP): game over state
5. Implement `src/states/battle.py` — battle scene rendering:
   - Enemy sprites (front-facing, static or animated)
   - Player HP/MP display
   - Command menu (Attack / Magic / Item / Defend / Flee)
   - Damage numbers / text feedback
   - Turn flow with brief delays for readability
6. Implement `src/states/game_over.py` — game over screen
7. Implement leveling system in `data/levels.json` — XP thresholds, stat gains per level
8. Wire encounter system into overworld state

**Verification:**

- Walking on the overworld triggers random battles after variable steps
- Battle loads with correct enemies for the zone
- Player can Attack, Defend, and Flee
- Damage calculations feel balanced (enemies don't one-shot, battles aren't trivial)
- Victory grants XP, and if threshold met, level up with stat gains
- Defeat shows game over screen

**Dependencies:** Phase 1 (overworld, state machine, player entity)

---

### Phase 3: Magic & Inventory ✅ COMPLETE

*Goal: Cast spells, use items, equip gear*

**Steps:**

1. Define spell data in `data/spells.json` — name, MP cost, power, element, target (single/all), status effect, learn level
2. Implement `src/systems/magic.py` — spell casting with MP check, magical damage formula, elemental weakness/resistance multipliers, healing spells, buff/debuff application
3. Implement status effect system inside `battle_engine.py` — Poison tick, Blind hit reduction, Silence spell block, Sleep skip turn, buff durations
4. Define item data in `data/items.json` — consumables and equipment with stats, prices, effects
5. Implement `src/systems/inventory.py` — add/remove items, item stack limits (99), use consumable (heal, cure status), equip/unequip (recalculate stats)
6. Add Magic submenu and Item submenu to battle state — spell list filtered by known spells, item list filtered to usable-in-battle
7. Implement `src/states/pause_menu.py` — out-of-battle menu with tabs: Items (use healing items), Equipment (weapon/shield/armor/helmet/accessory), Magic (view spells), Stats (view character stats)
8. Update enemy AI to use spells and abilities (defined per enemy in JSON)

**Verification:**

- Player can cast spells in battle, MP decreases correctly
- Elemental weaknesses deal 2x damage, resistances 0.5x
- Healing spells and items restore HP correctly
- Status effects apply and wear off after correct turns
- Equipment changes affect stats visibly in battle
- Pause menu accessible from overworld, all tabs functional

**Dependencies:** Phase 2 (battle system, damage formulas, enemy entities)

---

### Phase 4: Towns, NPCs & Shops ✅ COMPLETE

*Goal: Enter towns, talk to NPCs, buy/sell items*

> **Note:** Maps are implemented as hardcoded 2D arrays rather than Tiled TMX files. The `pytmx`/`pyscroll` workflow from the original plan was skipped in favour of a simpler in-code approach. Everything else in this phase is implemented as planned.

**Steps:**

1. Set up Tiled Map Editor workflow — create tileset from 16x16 tile PNGs, define tile properties (blocked, encounter zone, town entrance, NPC spawn)
2. Implement `src/utils/tilemap.py` — load TMX maps via pytmx, integrate with pyscroll for efficient scrolling and layer rendering
3. Convert overworld to TMX-based map with multiple layers (ground, decoration, collision, events)
4. Create town maps in Tiled with NPC spawn points, shop triggers, inn triggers
5. Implement `src/states/town.py` — similar to overworld but no random encounters, enter/exit transitions
6. Implement `src/entities/npc.py` — NPC with position, sprite, dialog reference, interaction trigger (face NPC + press action key)
7. Define dialog in `data/dialog.json` — dialog trees with sequential text, optional branches/choices
8. Implement `src/states/dialog.py` — overlay state that renders dialog box, typewriter text effect, advance on button press
9. Implement `src/ui/text_box.py` — reusable bordered text box with word wrap, typewriter effect
10. Define shop inventories in `data/shops.json` — per-town item lists with prices
11. Implement `src/states/shop.py` — buy/sell interface, gold management, inventory integration
12. Add inn functionality — pay gold, full HP/MP restore, fade to black transition

**Verification:**

- Walking onto a town entrance tile transitions to town map
- NPCs display on the map, can be talked to with action key
- Dialog appears in text box with typewriter effect, advances on button press
- Shops display item list with prices, buying deducts gold and adds item
- Selling gives gold and removes item
- Inn restores HP/MP and charges gold

**Dependencies:** Phase 3 (inventory system, items)

---

### Phase 5: Content, Story & Save System 🔄 PARTIALLY COMPLETE

*Goal: Full game content, story progression, save/load*

**What is done:**
- Scripted intro cutscene (`src/states/intro.py`): narration panels, animated characters, dialog, skip key
- Quest flag system (`src/systems/quest_flags.py`)
- JSON save/load with multiple slots (`src/systems/save_load.py`; Save tab in pause menu)
- Overworld HUD (`src/ui/hud.py`)

**What remains:**

**Steps:**

1. ❌ Create all overworld maps — currently only one overworld map exists (`data/maps/map01.csv`); Silverwood Forest, Stormcrag Mountains, and Dark Lands maps still needed
2. ⚠️ Create all town maps — Ashenvale and Ironhaven are implemented; **Willowmere** and **Subterra** (hidden underground city) are not yet built
3. ❌ Create dungeon maps — Silverwood clearing (Dire Wolf Alpha boss), Black Fortress (final dungeon), and **Subterra Passage** (hidden cave) are not yet implemented
4. ✅ Implement `src/systems/quest_flags.py` — done; dictionary of boolean flags tracks story events
5. ❌ Implement boss battles — scripted encounters (not random), unique AI patterns:
   - Dire Wolf Alpha: multi-hit attacks, summons regular wolves
   - Black Knight Lieutenant: uses sword skills + dark magic
   - Corrupted Beast King: high HP, alternates physical/magic phases
   - The Black Knight: multi-phase fight, heals once, full spell kit
   - Crystal Sentinel (Subterra Passage mini-boss): immune to magic, high HP, guards Subterra entrance
6. ⚠️ Write all NPC dialog for each town, update based on quest flags — intro cutscene dialog and basic NPC lines exist; full story-driven, flag-reactive dialog not yet written
7. ❌ **Subterra content** — hidden wall in Stormcrag, passage with unique enemies (Cave Crawler, Pale Lurker), Subterra town map with Elder Marek, Archivist Lena, Merchant Dax, ancestral home with journal + Exo Weapon + Exo Armor
8. ✅ Implement `src/systems/save_load.py` — done; multiple slots, accessible via Save tab in the pause menu
9. ❌ Full map transitions — within-town and town↔overworld transitions work; cross-area transitions (e.g. overworld → Silverwood Forest, → Stormcrag Mountains) not yet implemented
10. ✅ Implement `src/ui/hud.py` — done; shows HP/MP bars and current area name
11. ⚠️ Encounter table variety — `data/encounters.json` exists with zone tables; needs updating as new map zones are added
12. ❌ Balance pass — requires all content to be in place first

**Verification:**

- Can play from Ashenvale through all areas to the Black Fortress
- Quest flags correctly gate story progression and change NPC dialog
- Save and load works correctly — position, stats, inventory, flags all preserved
- Boss battles are unique and challenging
- Level progression feels natural (no excessive grinding needed)
- Map transitions work seamlessly between all connected areas
- Subterra is discoverable only by interacting with the hidden wall in Stormcrag
- Crystal Sentinel mini-boss guards Subterra and is beatable at Lv ~20
- Subterra NPCs display correct dialog; unique shop items purchasable
- Exo Weapon and Exo Armor are obtainable in the ancestral home
- Journal is readable and displays the grandmother's message
- Game is fully completable without ever finding Subterra

**Dependencies:** Phases 1-4 (all systems)

---

### Phase 6: Audio, Polish & Final ✅ COMPLETE

*Goal: Complete, polished game*

**What is done:**
- `src/systems/audio.py` — `AudioManager` supports BGM streaming and pre-loaded SFX, fails silently when files are absent
- BGM tracks present in `assets/music/`: title, overworld, town, battle, boss_battle, cutscene, victory, game_over (WAV)
- SFX present in `assets/sfx/`: cursor, confirm, cancel, attack_hit, spell_cast, item_use, level_up, door_open, dialog_open, dialog_close (WAV)
- Opening intro cutscene (`src/states/intro.py`) with narration panels and animated character sequence
- `src/states/battle.py` fully rewritten — fixed broken merged-implementation, restored Magic/Item submenus
- Battle animations: coloured flash overlays on enemy sprites (physical=white, fire=orange, ice=blue, lightning=yellow, dark=purple, etc.) + incoming-damage flash on player panel
- Battle intro: FF-style horizontal-stripe wipe animation when entering combat (`_Phase.INTRO`, 0.55 s)
- `src/states/fade.py` — `FadeOverlay` state for smooth cross-map screen transitions
- Cross-map zone transitions now fade to black and back via `FadeOverlay`
- Polish: animated bobbing ▶ cursor in all menus (`src/ui/menu.py`)
- Cursor-move SFX wired into battle command, spell and item menus
- All story dialog and item flavour text present in `data/dialog.json` and `data/items.json`

**Steps:**

1. ✅ Add background music — `AudioManager` + WAV files in `assets/music/` cover all planned tracks
2. ✅ Add sound effects — all planned SFX WAV files present and hooked into `AudioManager`
3. ✅ Battle animations — coloured flash overlays per element; "SLASH" label on physical attacks; player panel flash on incoming damage
4. ✅ Screen transitions — `FadeOverlay` (black fade-in/out) wraps every cross-map zone transition
5. ✅ Battle intro — FF-style horizontal stripe wipe effect at battle start
6. ✅ Dialog and item descriptions — full story dialog in `data/dialog.json`; all items have `description` fields in `data/items.json`
7. ✅ Opening crawl / intro sequence — implemented as `src/states/intro.py` (narration panels + animated cutscene)
8. ⚠️ Final balance testing — stat/difficulty tuning deferred; requires full content playthrough
9. ✅ Polish pass — animated bobbing cursor in all menus; cursor SFX on navigation; consistent panel styling in battle HUD
10. ⚠️ Pixel art assets — placeholder procedural art remains; free tileset integration deferred to a future pass

**Verification:**

- Full playthrough from title screen to credits
- All audio plays correctly and loops properly
- Battle animations make combat feel impactful
- No crashes, no softlocks, no inaccessible areas
- Game can be saved and loaded at any point in the story

**Dependencies:** Phase 5 (all content)

---

## Verification (End-to-End)

1. Run `pip install -r requirements.txt` — installs cleanly
2. Run `python run.py` — title screen appears
3. Start game → walk around overworld → encounter battle → win → gain XP → level up
4. Enter town → talk to NPC → see dialog → visit shop → buy item → use item in battle
5. Equip weapon → damage increases in next battle
6. Cast spell → MP decreases, enemy takes elemental damage
7. Save game → quit → reload → resume from save point with all progress intact
8. Play through entire story arc (Acts 1-3) → reach credits
9. Find hidden wall in Stormcrag → enter Subterra Passage → defeat Crystal Sentinel → enter Subterra
10. Talk to Elder Marek, Archivist Lena → visit ancestral home → read journal → obtain Exo Weapon + Exo Armor
11. Equip Exo gear → noticeably stronger in subsequent battles
12. Complete game without ever visiting Subterra — verify it's fully optional

---

## Decisions

- **Party-ready battle engine** — Battle engine supports N combatants on player side from day one. Initially only the White Knight fights solo, but the architecture allows adding party members later without refactoring.
- **Pygame-CE over vanilla Pygame** — more actively maintained, better performance, more features.
- **pytmx + pyscroll** for maps — originally planned for Phase 4 upgrade; currently using hardcoded 2D arrays which are simpler to maintain for a small game. TMX upgrade remains an option if maps become large or complex enough to warrant it.
- **JSON for game data** — easy to edit, no database needed, version-controllable.
- **16x16 tiles, 3x scale** — authentic SNES feel at 768×672 window (48×42 tiles visible).
- **Art assets** — Free tilesets from OpenGameArt / itch.io to unblock development. Replace with custom art later.
- **Audio assets** — Free chiptune/RPG music packs from itch.io / OpenGameArt initially.

---

## Future Ideas & Stretch Goals

These are features not in the original six-phase plan but worth considering once the core game is complete:

### Gameplay Enhancements
- **Party members** — The battle engine already supports N combatants. Add 1–2 companion characters (e.g. the traveling healer NPC from Act 2) who join the party and can be controlled in battle.
- **Crafting system** — Combine raw materials found in the world into consumables or upgrade components for equipment.
- **Fishing / foraging mini-game** — Low-stakes exploration activity near water/forest tiles that yields consumable ingredients.
- **New Game+** — After finishing the game, restart with all stats and equipment carried over, with enemy HP/damage scaled up.

### World & Story
- **Willowmere** — The third town (lakeside hamlet, magic shop, inn) planned in the original story but not yet built.
- **Act 2 & Act 3 maps** — Silverwood Forest, Stormcrag Mountains, Dark Lands overworld tiles, and the Black Fortress dungeon.
- **Companion NPC quests** — Short personal questlines for each party companion that expand their backstory.
- **Branching dialog choices** — Player responses that can shift NPC attitudes or unlock alternate routes through a conversation.

### Technical & Polish
- **Controller support** — Map gamepad buttons via pygame's joystick API; show button glyphs in the HUD when a controller is detected.
- **Accessibility options** — Configurable text speed, toggle for reduced-motion (disable screen shakes/flashes), font size scaling.
- **Achievements / journal** — In-game codex tracking enemies defeated, areas explored, and optional challenges completed.
- **Procedural dungeon floors** — Optional: one or more "infinite" bonus dungeons generated at runtime for extended replayability.
- **Localization support** — Externalize all display strings into a locale JSON file to support multiple languages.
