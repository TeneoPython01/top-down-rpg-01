# Feature Ideas for Top-Down RPG

50 expansion ideas for growing the game beyond its current Phase 5 state. Each idea includes a recommended implementation approach and a status field.

> **Current implementation baseline:** Single-character overworld exploration, turn-based battle system, 5-slot save/load, dialog system with typewriter effect, 4 towns, 6+ zones, 17 spells, 20+ consumable/equipment items, quest flags, intro cutscene, and basic audio.

---

## Gameplay Mechanics

### 1. Party System (Allies / Companions)
**Status:** `Not Started`

**Description:** Allow up to 3 additional characters to join the player's party, each with unique stats, spells, and personalities. Party members take turns in battle and appear as sprites in the overworld.

**Recommended Approach:**
- Add a `party` list to `src/entities/player.py` (or a new `src/entities/party_member.py` class).
- Update `src/systems/battle_engine.py` to iterate over all active party members in the SPD-based turn queue.
- Add party member stat definitions to `data/party_members.json`.
- Update `src/states/pause_menu.py` to render each member's stats/equipment in the Stats and Equipment tabs.
- In the overworld, render follower sprites behind the player using stored offset positions.

---

### 2. Skill / Ability Tree
**Status:** `Not Started`

**Description:** Give each character a branching tree of passive and active abilities that can be unlocked by spending Skill Points earned on level-up (e.g., "Sword Mastery," "Iron Skin," "Spellblade").

**Recommended Approach:**
- Define the tree structure in `data/skills.json` with `id`, `name`, `description`, `cost`, `prereqs`, `effect`.
- Add `skill_points` and `unlocked_skills` fields to the player entity and save schema.
- Create `src/states/skill_tree.py` as a new pause-menu tab that renders nodes and connections.
- Apply passive skill bonuses inside `src/systems/battle_engine.py` and stat formulas.

---

### 3. Crafting System
**Status:** `Not Started`

**Description:** Combine materials gathered from enemies or the environment to forge new weapons, armor, and potions at a blacksmith NPC or crafting station.

**Recommended Approach:**
- Add a `materials` item category to `data/items.json` and enemy drop tables in `data/enemies.json`.
- Create `data/recipes.json` mapping ingredient lists to output items.
- Add a "Crafting" event tile or NPC interaction in town maps (`src/utils/town_maps.py`).
- Build `src/states/crafting.py` (overlay) that shows available recipes, required materials, and a "Forge" button.

---

### 4. Day / Night Cycle
**Status:** `Not Started`

**Description:** The overworld transitions between day and night every N real-time minutes, changing ambient lighting, NPC availability, enemy encounter tables, and some shop prices.

**Recommended Approach:**
- Track `game_time` (0–1 normalized, looping) in `src/game.py` updated by `dt`.
- Apply a semi-transparent overlay in `src/states/overworld.py` whose alpha is derived from `game_time`.
- Store dual encounter tables in `data/encounters.json` under `"day"` and `"night"` keys.
- Flag certain NPCs as day-only or night-only in `data/dialog.json`.

---

### 5. Weather System
**Status:** `Not Started`

**Description:** Random weather events (rain, fog, blizzard, sandstorm) affect visibility, movement speed, and battle conditions (e.g., Thunder spells strengthened in storms).

**Recommended Approach:**
- Add a `WeatherSystem` in `src/systems/weather.py` with states: `clear`, `rain`, `fog`, `blizzard`.
- Draw particle overlays in `src/states/overworld.py` based on current weather state.
- In `src/systems/battle_engine.py`, check weather flags when calculating elemental damage multipliers.
- Tie weather to zone biome: rain in forest, blizzard in mountains.

---

### 6. Stealth / Detection System
**Status:** `Not Started`

**Description:** Add a crouch/sneak mode that reduces enemy encounter rate and allows the player to pass patrolling enemies or approach NPCs without triggering combat.

**Recommended Approach:**
- Add a `sneaking` boolean to `src/entities/player.py`; toggle with a key (e.g., `C`).
- Halve player speed and encounter step count while sneaking.
- Add patrolling NPCs with a sight-cone rectangle in `src/entities/npc.py`; entering the cone triggers combat or alert dialog.

---

### 7. Puzzle Rooms / Dungeon Puzzles
**Status:** `Not Started`

**Description:** Special dungeon rooms with environmental puzzles (push-block, light-beam, pressure-plate) that must be solved to unlock doors or reach treasure chests.

**Recommended Approach:**
- Define puzzle layouts in JSON with tile types: `pushable_block`, `pressure_plate`, `laser_emitter`, `mirror`.
- Create `src/states/puzzle_room.py` that handles puzzle-specific tile logic and win condition checks.
- Transition into a puzzle room from a dungeon entrance tile, then return to overworld on completion.

---

### 8. Fishing Mini-Game
**Status:** `Not Started`

**Description:** Cast a line in water tiles to catch fish that can be sold, cooked for stat buffs, or traded to NPCs for rare items.

**Recommended Approach:**
- Detect player standing adjacent to a water tile; pressing `F` opens `src/states/fishing.py`.
- Mini-game loop: a bar with a moving cursor—press `Z` in a shrinking window to "hook" the fish.
- Add fish items to `data/items.json` with cook/sell/trade flags.
- Add a Fisherman NPC to a coastal town who accepts fish for quest rewards.

---

### 9. Arena / Coliseum Mode
**Status:** `Not Started`

**Description:** An optional battle arena where the player fights escalating waves of enemies or other challengers for gold and rare equipment prizes.

**Recommended Approach:**
- Add an Arena event tile in a town (e.g., Ironhaven).
- Create `src/states/arena.py` that chains `BattleState` instances using a predefined bracket in `data/arena.json`.
- Track win/loss streak and award prizes from a prize table on winning rounds.

---

### 10. Mounts / Transportation
**Status:** `Not Started`

**Description:** Acquire rideable mounts (horse, ship, airship) that grant faster overworld movement, allow crossing water tiles, or fly over all terrain.

**Recommended Approach:**
- Add a `mount` field to the player entity (`None`, `"horse"`, `"ship"`, `"airship"`).
- Override collision logic in `src/states/overworld.py` based on mount type (ship ignores water tiles, airship ignores all).
- Define mount locations and purchase events in town event tiles.
- Swap the player sprite to a mounted variant when a mount is active.

---

## UI / UX

### 11. Animated Sprite Tilesets
**Status:** `Not Started`

**Description:** Replace placeholder colored rectangles with real pixel-art sprite sheets for the player, NPCs, enemies, and environment tiles.

**Recommended Approach:**
- Store sprite sheets as PNG files in `assets/sprites/` and `assets/tiles/`.
- Use `pygame.image.load` + `convert_alpha()` in entity constructors.
- Implement a `SpriteSheet` utility class in `src/utils/sprite_sheet.py` that slices frames by row/column.
- Map animation state (`idle_down`, `walk_left`, etc.) to frame ranges in each entity's class.

---

### 12. Mini-Map / World Map
**Status:** `Complete`

**Description:** Press `M` to toggle a mini-map overlay (corner HUD) or full-screen world map showing explored zones, towns, and the player's current position.

**Recommended Approach:**
- Pre-render each zone map to a small `pygame.Surface` by sampling tile colors.
- Overlay the mini-map surface in the top-right corner of `src/states/overworld.py`.
- Track visited zones in a `visited_zones` set on the player and grey out unvisited areas.
- Build `src/states/world_map.py` for the full-screen view with zone labels and player marker.

---

### 13. Floating Damage Numbers
**Status:** `Complete`

**Description:** Display animated damage and healing numbers that float upward and fade out above the affected target in battle.

**Recommended Approach:**
- Create a `FloatingText` dataclass in `src/ui/floating_text.py` with position, value, color, lifetime, and velocity.
- Maintain a list of active floating texts in `src/states/battle.py` and update/draw them each frame.
- Spawn a text object whenever `battle_engine` returns a damage/heal result.

---

### 14. Achievement System
**Status:** `Not Started`

**Description:** Track and display in-game achievements (e.g., "First Blood," "Level 20," "Complete the Bestiary") with unlock notifications and a permanent achievement log.

**Recommended Approach:**
- Define achievements in `data/achievements.json` with `id`, `name`, `description`, and `condition`.
- Create `src/systems/achievements.py` that checks conditions each frame or on events and marks them complete.
- Save unlocked achievements in the save file.
- Show a non-blocking toast notification in `src/ui/` when an achievement unlocks.

---

### 15. Bestiary / Monster Encyclopedia
**Status:** `Not Started`

**Description:** A log that fills in as the player encounters enemies, showing each enemy's stats, weaknesses, resistances, and lore description.

**Recommended Approach:**
- Add `"lore"` and `"scan_unlock"` fields to `data/enemies.json`.
- Track `seen_enemies` and `defeated_enemies` sets in the player entity and save schema.
- Add a Bestiary tab to `src/states/pause_menu.py` that renders seen enemy portraits and reveals full data only for defeated enemies.

---

### 16. Dialog Choice Trees
**Status:** `Not Started`

**Description:** Replace linear NPC dialogs with branching conversation choices that affect quest outcomes, NPC relationships, and story flags.

**Recommended Approach:**
- Extend `data/dialog.json` with a `"choices"` array per dialog node, each choice pointing to a `next_id` and optionally setting quest flags.
- Update `src/states/dialog.py` to render a choice list after the final line and handle cursor navigation.
- Store choice-derived flags in the quest flags system.

---

### 17. Battle Speed Setting
**Status:** `Complete`

**Description:** Let the player choose battle animation speed (Normal / Fast / Instant) via the Options menu to reduce grind time.

**Recommended Approach:**
- Add a `battle_speed` setting (multiplier) in `settings.py` and an in-game Options menu.
- Thread all animation timers through the multiplier in `src/states/battle.py`.

---

### 18. Controller / Gamepad Support
**Status:** `Not Started`

**Description:** Allow the game to be played with an Xbox/PlayStation controller in addition to keyboard.

**Recommended Approach:**
- Use `pygame.joystick` to poll connected gamepads in the main event loop in `src/game.py`.
- Map d-pad to movement, face buttons to confirm/cancel, shoulder buttons to open menus.
- Store current input scheme in `settings.py` and abstract input reads through a helper `src/utils/input.py`.

---

### 19. Options / Settings Menu
**Status:** `Complete`

**Description:** In-game screen for adjusting music volume, SFX volume, window scale, battle speed, and text speed without editing code.

**Recommended Approach:**
- Create `src/states/options.py` with sliders and toggles.
- Persist settings to `data/config.json` on change; load at startup in `run.py`.
- Link from the title screen and the pause menu.

---

### 20. Animated Battle Backgrounds
**Status:** `Not Started`

**Description:** Each zone has a unique looping parallax background displayed during battles (grassy plains, cave walls, forest canopy, etc.).

**Recommended Approach:**
- Store background layers as PNG strips in `assets/battle_bgs/`.
- Scroll each layer at different speeds in `src/states/battle.py`'s draw method.
- Pass the current zone name when constructing `BattleState` and map it to a background set.

---

## Combat & Enemies

### 21. Multi-Phase Boss Fights
**Status:** `Not Started`

**Description:** Boss enemies transform mid-fight (new sprite, new moveset, increased stats) when their HP drops below a threshold.

**Recommended Approach:**
- Add a `"phases"` array to boss entries in `data/enemies.json`, each phase specifying stat overrides, new AI behavior, and a trigger HP%.
- In `src/systems/battle_engine.py`, check phase thresholds after each damage event and swap the active enemy data when crossed.
- Play a phase-transition animation and music sting.

---

### 22. Elemental Combo System
**Status:** `Not Started`

**Description:** Casting two compatible spells in sequence (e.g., Fire then Wind) produces a Combo that deals bonus damage and applies a unique status effect.

**Recommended Approach:**
- Define combo pairs in `data/combos.json`: `{"first": "Fire", "second": "Wind", "result": "Inferno", "bonus_dmg": 1.5, "status": "burn"}`.
- In `src/systems/battle_engine.py`, track the last spell cast and check for matching combos before resolving the next spell.

---

### 23. Limit Break / Desperation Attacks
**Status:** `Not Started`

**Description:** When HP falls below 25%, the player can unleash a powerful cinematic special move that deals massive damage or provides a game-changing buff.

**Recommended Approach:**
- Add a `limit_gauge` (0–100) to the player, filled by taking damage.
- Display a gauge in the battle HUD.
- Add "Limit" as a battle command visible only when the gauge is full and HP < 25%.
- Define limit break effects in `data/skills.json`.

---

### 24. Enemy Summon / Reinforcement AI
**Status:** `Not Started`

**Description:** Some enemies can call for backup mid-battle, adding new enemies to the encounter if they survive long enough.

**Recommended Approach:**
- Add a `"summon"` AI behavior type in `data/enemies.json` with a cooldown and list of summonable enemy IDs.
- In `src/systems/battle_engine.py`, handle the summon action by appending a new enemy entity to the battle's enemy list (up to max 5).

---

### 25. Traps / Environmental Hazards in Battle
**Status:** `Not Started`

**Description:** Zone-specific hazards trigger automatically each round (lava pools deal fire damage, ice floors reduce accuracy, quicksand slows movement).

**Recommended Approach:**
- Add an optional `"hazard"` field to encounter groups in `data/encounters.json`.
- In `src/states/battle.py`, apply the hazard effect at the start of each round before normal turn resolution.

---

### 26. Steal / Pickpocket Mechanic
**Status:** `Not Started`

**Description:** Add a "Steal" battle command that attempts to take an item from an enemy before it is killed, yielding otherwise unobtainable rare items.

**Recommended Approach:**
- Add `"steal_item"` and `"steal_chance"` fields to `data/enemies.json`.
- Add "Steal" to the player's battle command list in `src/states/battle.py`.
- Implement steal resolution in `src/systems/battle_engine.py` using LCK-based probability.

---

### 27. Timed Button Press Combat
**Status:** `Not Started`

**Description:** When attacking or defending, a small timing window pops up; pressing the action button in the window boosts damage (on attack) or reduces damage (on defend).

**Recommended Approach:**
- After choosing "Attack" or "Defend," show a `TimingBar` UI element in `src/ui/` with a sliding cursor.
- Gate the result in `src/systems/battle_engine.py` with a `timing_bonus` multiplier (1.0 miss, 1.25 good, 1.5 perfect).

---

### 28. Debuff / Ailment Expansion
**Status:** `Not Started`

**Description:** Add new status effects: Burn (recurring fire damage), Frozen (skip 1–3 turns on thaw), Confused (attack random target), Charmed (attack allies), Petrified (permanent skip until cured).

**Recommended Approach:**
- Extend the `STATUS_EFFECTS` dict in `src/systems/battle_engine.py` and `settings.py`.
- Add curing items to `data/items.json` and shops.
- Assign new ailments to appropriate enemy abilities in `data/enemies.json`.

---

## World & Exploration

### 29. Procedurally Generated Dungeons
**Status:** `Not Started`

**Description:** Optional side dungeons with randomly generated floor layouts, random enemy placements, and random treasure chests—different every visit.

**Recommended Approach:**
- Implement a BSP or cellular-automata dungeon generator in `src/utils/dungeon_gen.py` that outputs a 2D tile grid.
- Seed the generator from the current in-game date for reproducibility within a session.
- Reuse existing `TileMap` and encounter machinery to populate the generated floor.

---

### 30. Additional Biomes / Zones
**Status:** `Not Started`

**Description:** Add at least 3 new explorable biomes: a desert (heat damage each step without water), a swamp (movement penalty, poison encounters), and an arctic tundra (blizzard weather, ice enemies).

**Recommended Approach:**
- Add new zone IDs and tile-color palettes in `settings.py`.
- Define zone maps in `src/utils/tilemap.py` or a new file.
- Add biome-specific encounter tables, NPCs, and environmental effects.
- Connect biomes to the existing overworld via zone-exit tiles.

---

### 31. Treasure Maps / Buried Treasure
**Status:** `Not Started`

**Description:** Findable map items that reveal hidden dig spots on the overworld. Digging at the marked location yields rare items or gold.

**Recommended Approach:**
- Add `"treasure_map"` items to `data/items.json` with a `"target_zone"` and `"tile_coords"`.
- When a treasure map is in inventory, render an `X` marker at the specified overworld position.
- Press `G` (dig) when standing on the marker to trigger an excavation animation and reward popup.

---

### 32. Secret / Hidden Passages
**Status:** `Not Started`

**Description:** Expand the hidden-wall mechanic with more complex secret passages that require items (e.g., a torch to see in the dark) or ability checks to unlock.

**Recommended Approach:**
- Add `"requires_item"` or `"requires_flag"` metadata to tile definitions.
- Check these conditions in the collision / interaction code in `src/states/overworld.py`.
- Display a hint ("The wall seems hollow…") when the player bumps a hidden-passage tile.

---

### 33. Overworld Random Events
**Status:** `Not Started`

**Description:** While traversing the overworld, random non-combat events appear (a traveler offers a trade, a merchant cart ambush, a mysterious chest, a wounded animal to rescue).

**Recommended Approach:**
- Create `src/systems/random_events.py` with a weighted list of events defined in `data/random_events.json`.
- Trigger an event after X steps (separate counter from encounter counter).
- Present the event as a dialog overlay with choice options and apply the resulting effects.

---

### 34. Destructible / Interactive Environment
**Status:** `Not Started`

**Description:** Let the player break certain wall tiles (with a hammer item), push boulders to create new paths, or light torches to reveal hidden rooms.

**Recommended Approach:**
- Mark tiles with `"destructible": true` or `"pushable": true` in the tile-map data format.
- Handle player-tile interaction in `src/states/overworld.py` on action-key press.
- Replace the tile with a floor tile or trigger a map-state change stored in quest flags.

---

## NPCs & Story

### 35. Relationship / Reputation System
**Status:** `Not Started`

**Description:** NPCs track the player's actions (helping villagers, defeating bosses, completing quests). High reputation unlocks discounts, new dialog, and hidden quests; low reputation triggers hostility.

**Recommended Approach:**
- Add a `reputation` dict (NPC group → integer) to the player entity and save schema.
- Increment/decrement reputation in quest flag handlers.
- Gate dialog nodes and shop discounts in `data/dialog.json` and `data/shops.json` behind reputation thresholds.

---

### 36. Side Quests & Notice Board
**Status:** `Not Started`

**Description:** A notice board in each town lists optional quests (fetch items, defeat enemies, escort NPCs) with gold/item rewards.

**Recommended Approach:**
- Define quests in `data/quests.json` with `"objectives"` (type, target, count), `"rewards"`, and `"prereq_flags"`.
- Build `src/states/quest_board.py` to display available/active/completed quests.
- Track progress in a `quest_progress` dict on the player and complete them via the quest system.

---

### 37. Escort / NPC Follow Mechanic
**Status:** `Not Started`

**Description:** Certain quests require escorting an NPC from one location to another; the NPC follows the player and must be protected from enemies.

**Recommended Approach:**
- Add a `following` flag and `target` reference to `src/entities/npc.py`.
- Each frame, move the NPC toward the player's previous-frame position (bread-crumb trail).
- If an encounter triggers during escort, add the NPC as a fragile ally in battle with 1 HP.

---

### 38. Expanded Backstory via Collectible Lore Books
**Status:** `Not Started`

**Description:** Scatter 20+ readable books, journals, and stone tablets across the world that reveal faction history, spell origins, and world lore.

**Recommended Approach:**
- Define lore entries in `data/lore.json` with `id`, `title`, `body`, `location`, and `zone`.
- Add lore-book event tiles to town and dungeon maps.
- Build `src/states/lore_reader.py` (overlay) that renders multi-page text with page-turn navigation.
- Track collected entries in the player save and add a "Library" tab to the pause menu.

---

### 39. Villain / Antagonist Story Arc
**Status:** `Not Started`

**Description:** Introduce a named main antagonist with recurring appearances, threatening monologues, and a final climactic boss battle, giving the story a clear narrative spine.

**Recommended Approach:**
- Add antagonist dialog entries to `data/dialog.json` and NPC entries to zone maps.
- Gate appearances behind quest flag milestones (e.g., `"post_boss_2"`, `"post_dungeon_4"`).
- Design a final boss entry in `data/enemies.json` with three phases and unique spells.

---

### 40. Romance / Companion Dialogue
**Status:** `Not Started`

**Description:** Party members develop unique personal story arcs that deepen through optional dialog events at rest points (inns, campfires), unlocking character-specific bonus abilities.

**Recommended Approach:**
- Add companion-specific dialog chains in `data/dialog.json` keyed to companion ID and `relationship_level`.
- Increment `relationship_level` when the player chooses favorable dialog options.
- Unlock a companion's signature skill in `data/skills.json` at relationship thresholds.

---

## Items & Economy

### 41. Equipment Enchantment / Upgrade System
**Status:** `Not Started`

**Description:** At a blacksmith, pay gold and materials to upgrade weapon/armor tier (+1, +2, +3) or add elemental enchantments (Flaming Sword, Frost Shield).

**Recommended Approach:**
- Add `"level"` and `"enchant"` fields to equipped item state in the player entity.
- Create `src/states/enchant.py` at the blacksmith event tile.
- Define upgrade costs and stat bonuses in `data/upgrade_table.json`.
- Apply enchantment bonuses inside the damage formula in `src/systems/battle_engine.py`.

---

### 42. Auction House / Rare Item Bidding
**Status:** `Not Started`

**Description:** A special weekly auction in Ironhaven where the player can bid gold against NPCs for rare gear, art objects, or unique accessories.

**Recommended Approach:**
- Add an Auction event tile in Ironhaven's town map.
- Create `src/states/auction.py` with a simple ascending-bid loop driven by timer-based NPC bids.
- Define rotating auction lots in `data/auction_lots.json` with min bid, item ID, and rotation cycle.

---

### 43. Black Market / Shady Dealer
**Status:** `Not Started`

**Description:** A hidden NPC trader (appears only at night, in back alleys) who sells illegal or banned items—powerful but risky.

**Recommended Approach:**
- Add a night-only NPC to Ashenvale or Subterra with a unique shop in `data/shops.json`.
- Gate the NPC's visibility to the `night` weather/time state.
- Add a reputation penalty for buying from this merchant.

---

### 44. Item Combination / Alchemy
**Status:** `Not Started`

**Description:** At an alchemist NPC, combine two items into a more powerful third item (Hi-Potion + Ether = Hi-Elixir, Bomb Fragment + Arctic Wind = Blizzard Bomb).

**Recommended Approach:**
- Define combination recipes in `data/alchemy.json`.
- Add an Alchemist NPC to Willowmere's town map.
- Build `src/states/alchemy.py` with a two-slot ingredient picker and "Combine" action.

---

### 45. Gold Sinks & Investment System
**Status:** `Not Started`

**Description:** Let players invest gold in rebuilding a damaged town to unlock new shops, improve NPC quality, or earn passive income between sessions.

**Recommended Approach:**
- Add an `"investment_level"` per town in the player save data.
- Gate upgraded shops and NPCs behind investment milestones in `data/shops.json` and `data/dialog.json`.
- Show investment progress and projected returns in an investment-screen overlay.

---

## Audio & Presentation

### 46. Dynamic / Adaptive Music
**Status:** `Not Started`

**Description:** The overworld BGM shifts intensity based on proximity to enemies, danger level, and quest progress (calm → tense → action → triumphant) using layered stems.

**Recommended Approach:**
- Store multi-stem audio files (base, tension, action layers) in `assets/audio/music/`.
- In `src/states/overworld.py`, compute a `tension` value from encounter step proximity and nearby boss proximity.
- Use `pygame.mixer.Channel` volume automation to fade each stem in/out without restarting.

---

### 47. Voice Acting / Battle Grunts
**Status:** `Not Started`

**Description:** Short audio clips for common battle actions (player attack grunt, magic cast whoosh, enemy death cry) to add tactile feedback.

**Recommended Approach:**
- Add SFX audio files to `assets/audio/sfx/`.
- Extend the `AudioSystem` (or `src/systems/audio.py`) to map event names (`"player_attack"`, `"spell_fire"`, `"enemy_death"`) to clip files.
- Trigger SFX calls in `src/systems/battle_engine.py` at appropriate resolution points.

---

### 48. Additional Cutscenes
**Status:** `Not Started`

**Description:** Scripted cutscenes at major story milestones: defeating the first boss, arriving in a new town for the first time, the villain's reveal, and the final confrontation.

**Recommended Approach:**
- Model each new cutscene as a phase list in `src/states/intro.py` (or a refactored `src/states/cutscene.py`).
- Trigger cutscenes by checking quest flags in overworld or post-battle transitions.
- Reuse the existing fade system and NPC-movement infrastructure from the intro cutscene.

---

### 49. Environmental Ambient Sounds
**Status:** `Not Started`

**Description:** Each zone plays looping ambient audio (birds chirping in forest, wind howling in mountains, dripping water in caves) beneath the BGM.

**Recommended Approach:**
- Add an `"ambient_sfx"` field to zone definitions in `settings.py`.
- Play the ambient clip on a dedicated `pygame.mixer.Channel` (lower volume) when entering a zone.
- Fade it out during battle or town entry.

---

### 50. Illustrated Event CG Scenes
**Status:** `Not Started`

**Description:** At key story moments (first boss defeat, companion joining, final battle) display a full-screen illustrated scene (pixel-art CG) before the next cutscene or dialog fires.

**Recommended Approach:**
- Store CG images as full-resolution PNG files in `assets/cg/`.
- Build a lightweight `src/states/cg_display.py` state that renders the image scaled to the window with a caption and a "Press Z to continue" prompt.
- Chain from other states via a `CG_EVENT` constant in `settings.py` mapped to image paths and trigger flags.

---

## Summary Table

| # | Feature | Category | Status |
|---|---------|----------|--------|
| 1 | Party System | Gameplay | Not Started |
| 2 | Skill / Ability Tree | Gameplay | Not Started |
| 3 | Crafting System | Gameplay | Not Started |
| 4 | Day / Night Cycle | Gameplay | Not Started |
| 5 | Weather System | Gameplay | Not Started |
| 6 | Stealth / Detection | Gameplay | Not Started |
| 7 | Puzzle Rooms | Gameplay | Not Started |
| 8 | Fishing Mini-Game | Gameplay | Not Started |
| 9 | Arena / Coliseum | Gameplay | Not Started |
| 10 | Mounts / Transportation | Gameplay | Not Started |
| 11 | Animated Sprite Tilesets | UI/UX | Not Started |
| 12 | Mini-Map / World Map | UI/UX | Complete |
| 13 | Floating Damage Numbers | UI/UX | Complete |
| 14 | Achievement System | UI/UX | Not Started |
| 15 | Bestiary | UI/UX | Not Started |
| 16 | Dialog Choice Trees | UI/UX | Not Started |
| 17 | Battle Speed Setting | UI/UX | Complete |
| 18 | Controller / Gamepad Support | UI/UX | Not Started |
| 19 | Options / Settings Menu | UI/UX | Complete |
| 20 | Animated Battle Backgrounds | UI/UX | Not Started |
| 21 | Multi-Phase Boss Fights | Combat | Not Started |
| 22 | Elemental Combo System | Combat | Not Started |
| 23 | Limit Break | Combat | Not Started |
| 24 | Enemy Summon / Reinforcements | Combat | Not Started |
| 25 | Battle Environmental Hazards | Combat | Not Started |
| 26 | Steal / Pickpocket | Combat | Not Started |
| 27 | Timed Button Press Combat | Combat | Not Started |
| 28 | Expanded Status Effects | Combat | Not Started |
| 29 | Procedural Dungeons | World | Not Started |
| 30 | New Biomes / Zones | World | Not Started |
| 31 | Treasure Maps | World | Not Started |
| 32 | Hidden Passages Expansion | World | Not Started |
| 33 | Overworld Random Events | World | Not Started |
| 34 | Destructible Environment | World | Not Started |
| 35 | Reputation System | NPCs/Story | Not Started |
| 36 | Side Quests / Notice Board | NPCs/Story | Not Started |
| 37 | Escort Mechanic | NPCs/Story | Not Started |
| 38 | Collectible Lore Books | NPCs/Story | Not Started |
| 39 | Villain / Antagonist Arc | NPCs/Story | Not Started |
| 40 | Companion Dialogue / Romance | NPCs/Story | Not Started |
| 41 | Equipment Enchantment | Items/Economy | Not Started |
| 42 | Auction House | Items/Economy | Not Started |
| 43 | Black Market | Items/Economy | Not Started |
| 44 | Item Alchemy / Combination | Items/Economy | Not Started |
| 45 | Town Investment System | Items/Economy | Not Started |
| 46 | Dynamic / Adaptive Music | Audio | Not Started |
| 47 | Voice Acting / Battle Grunts | Audio | Not Started |
| 48 | Additional Cutscenes | Audio | Not Started |
| 49 | Ambient Environmental Sounds | Audio | Not Started |
| 50 | Illustrated CG Event Scenes | Audio | Not Started |
