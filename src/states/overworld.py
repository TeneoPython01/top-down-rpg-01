"""
src/states/overworld.py - Overworld exploration state.

Handles tile-map rendering, player movement, camera, collision, NPC
interaction, random encounter triggering, zone transitions, dungeon boss
triggers, and hidden-wall mechanics.
"""

from __future__ import annotations

import json
import os
import random
from typing import TYPE_CHECKING, Any, Dict, List

import pygame

from settings import (
    DATA_DIR,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
    PLAYER_SIZE,
    TILE_DUNGEON,
    TILE_HIDDEN,
    TILE_SIZE,
    TILE_TOWN,
    TILE_WALL,
    TILE_WATER,
    TILE_ZONE_EXIT,
    TOWN_ENTRY_COOLDOWN,
    WHITE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.npc import NPC
from src.systems.camera import Camera
from src.systems.encounter import EncounterSystem
from src.utils.tilemap import TileMap, get_zone_data

if TYPE_CHECKING:
    from src.game import Game

# ── Per-zone NPC definitions ──────────────────────────────────────────────────
# Each entry: dialog_id, display name, tile col, tile row.
_ZONE_NPCS: Dict[str, List[Dict[str, Any]]] = {
    "verdant_plains": [
        {"dialog_id": "village_elder_before", "name": "Village Elder", "col": 10, "row": 4},
        {"dialog_id": "farmer_ashenvale",     "name": "Farmer",        "col": 8,  "row": 14},
        {"dialog_id": "healer_npc",           "name": "Healer",        "col": 20, "row": 9},
    ],
    "silverwood_forest": [
        {"dialog_id": "willowmere_traveler", "name": "Wanderer", "col": 15, "row": 5},
    ],
    "stormcrag_mountains": [],
    "dark_lands": [],
    "subterra_passage": [],
}

# Scene narration shown once on first overworld entry.
_INTRO_LINES = [
    "Ashenvale -- a quiet village on the edge of the Verdant Plains.",
    "100 years after the pandemic, nature has reclaimed the land.",
    "Strange beast attacks have been increasing near the village.",
    "The White Knight has returned to investigate...",
]


def _load_json(path: str) -> Any:
    with open(path) as fh:
        return json.load(fh)


class OverworldState(BaseState):
    """Overworld exploration: tile map, player, camera, collision, NPCs."""

    # Proximity threshold (native pixels) for NPC interaction via Z key.
    _INTERACT_RANGE = 20

    def __init__(
        self,
        game: "Game",
        player: Player | None = None,
        zone_name: str = "verdant_plains",
        spawn_override: tuple | None = None,
    ) -> None:
        super().__init__(game)

        self._zone_name = zone_name
        zone_data = get_zone_data(zone_name)

        self.tilemap = TileMap(
            data=zone_data["map"],
            spawn=zone_data["spawn"],
            town_entrances=zone_data["town_entrances"],
            zone_exits=zone_data["zone_exits"],
            dungeon_entries=zone_data["dungeon_entries"],
            hidden_walls=zone_data["hidden_walls"],
        )

        # Reuse an existing player or create a fresh one.
        if player is None:
            spawn_col, spawn_row = self.tilemap.spawn
            self.player = Player(spawn_col, spawn_row)
        else:
            self.player = player

        # Override spawn position when arriving via zone exit.
        if spawn_override is not None:
            sc, sr = spawn_override
            _margin = (TILE_SIZE - PLAYER_SIZE) // 2
            _px = sc * TILE_SIZE + _margin
            _py = sr * TILE_SIZE + _margin
            self.player.pos = pygame.Vector2(_px, _py)
            self.player.rect.topleft = (round(_px), round(_py))

        # Register player with the game object for save/load access.
        game.player = self.player

        self.camera = Camera(self.tilemap.pixel_width, self.tilemap.pixel_height)

        # ── Encounter system ──────────────────────────────────────────────────
        self._zone = zone_data.get("encounter_zone", "grasslands")
        self._encounter = EncounterSystem(encounter_rate=20)
        self._last_tile = self.tilemap.pixel_to_tile(
            self.player.pos.x, self.player.pos.y
        )
        self._enemies_by_id: dict = {}
        self._encounters_data: dict = {}
        self._data_loaded = False

        self._town_cooldown = 0.0
        # Only show the intro scene once per OverworldState instance.
        self._intro_shown = player is not None or zone_name != "verdant_plains"

        # ── Dialog / NPC data ─────────────────────────────────────────────────
        dialog_path = os.path.join(DATA_DIR, "dialog.json")
        with open(dialog_path, encoding="utf-8") as fh:
            self._dialog_data: dict = json.load(fh)

        npc_specs = _ZONE_NPCS.get(zone_name, [])
        self._npcs: List[NPC] = [
            NPC(spec, col=spec["col"], row=spec["row"], color_index=idx)
            for idx, spec in enumerate(npc_specs)
        ]

        # ── Zone-specific area display name ───────────────────────────────────
        self._display_name: str = zone_data.get("display_name", zone_name.replace("_", " ").title())

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        self._town_cooldown = TOWN_ENTRY_COOLDOWN
        self.game.current_location = f"overworld:{self._zone_name}"
        self.game.audio.play_music("overworld")
        if not self._intro_shown:
            self._intro_shown = True
            self._push_scene_dialog(_INTRO_LINES, speaker="")

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from src.states.pause_menu import PauseMenuState
                self.game.push_state(PauseMenuState(self.game, self.player))
            elif event.key in (pygame.K_z, pygame.K_RETURN):
                self._try_interact()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.player.update(dt, self.tilemap.blocked_rects)
        self.camera.update(self.player)
        self._check_encounter()

        if self._town_cooldown > 0:
            self._town_cooldown = max(0.0, self._town_cooldown - dt)
            return

        col, row = self.tilemap.pixel_to_tile(
            self.player.rect.centerx, self.player.rect.centery
        )
        tile_id = self.tilemap.tile_at(col, row)

        if tile_id == TILE_TOWN:
            town_name = self.tilemap.town_entrances.get((col, row), "")
            if town_name:
                from src.states.town import TownState
                self.game.push_state(TownState(self.game, town_name))

        elif tile_id == TILE_ZONE_EXIT:
            exit_data = self.tilemap.zone_exits.get((col, row))
            if exit_data:
                target_zone, sc, sr = exit_data
                self._transition_zone(target_zone, spawn=(sc, sr))

        elif tile_id == TILE_DUNGEON:
            dungeon_data = self.tilemap.dungeon_entries.get((col, row))
            if dungeon_data:
                self._check_dungeon_entry(dungeon_data)

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        self.tilemap.draw(surface, self.camera.offset)

        for npc in sorted(self._npcs, key=lambda n: n.rect.bottom):
            npc.draw(surface, self.camera.offset)

        surface.blit(self.player.image, self.player.rect.move(self.camera.offset))

        self._draw_hud(surface)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _try_interact(self) -> None:
        """Check for a nearby NPC, hidden wall, or dungeon — interact as appropriate."""
        player_center = pygame.Vector2(self.player.rect.center)

        # NPC interaction
        for npc in self._npcs:
            npc_center = pygame.Vector2(npc.rect.center)
            if player_center.distance_to(npc_center) <= self._INTERACT_RANGE:
                entry = self._dialog_data.get(npc.dialog_id)
                if entry:
                    lines = entry.get("lines", [])
                    self._push_npc_dialog(lines, speaker=npc.name)
                    return

        # Hidden wall interaction
        col, row = self.tilemap.pixel_to_tile(
            self.player.rect.centerx, self.player.rect.centery
        )
        # Check surrounding tiles for TILE_HIDDEN
        for dc, dr in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            check_col, check_row = col + dc, row + dr
            tile_id = self.tilemap.tile_at(check_col, check_row)
            if tile_id == TILE_HIDDEN:
                hw_data = self.tilemap.hidden_walls.get((check_col, check_row))
                if hw_data:
                    self._trigger_hidden_wall(hw_data)
                    return

    def _trigger_hidden_wall(self, hw_data: Dict[str, Any]) -> None:
        """Handle a hidden wall interaction (secret passage)."""
        flag_required = hw_data.get("flag_required")
        if flag_required and not self.game.quest_flags.get(flag_required):
            return  # quest gate not met

        reveal_text = hw_data.get("reveal_text", "A hidden passage is revealed!")
        target_zone = hw_data.get("to_zone", "subterra_passage")
        spawn = hw_data.get("spawn", (10, 13))

        def _enter_passage() -> None:
            self._transition_zone(target_zone, spawn=tuple(spawn))

        self._push_scene_dialog([reveal_text], speaker="", callback=_enter_passage)

    def _push_scene_dialog(
        self,
        lines: List[str],
        speaker: str = "",
        callback: Any = None,
    ) -> None:
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines, speaker=speaker, callback=callback))

    def _push_npc_dialog(self, lines: List[str], speaker: str) -> None:
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines, speaker=speaker))

    def _transition_zone(self, zone_name: str, spawn: tuple = (12, 17)) -> None:
        """Replace this overworld state with a new one for the target zone."""
        new_state = OverworldState(
            self.game,
            player=self.player,
            zone_name=zone_name,
            spawn_override=spawn,
        )
        self.game.change_state(new_state)

    def _check_dungeon_entry(self, dungeon_data: Dict[str, Any]) -> None:
        """Trigger a boss encounter if not already cleared."""
        flag = dungeon_data.get("flag", "")
        if flag and self.game.quest_flags.get(flag):
            return  # already cleared

        narration = dungeon_data.get("narration", "")
        boss_id = dungeon_data.get("boss_id", "")

        def _start_boss() -> None:
            self._trigger_boss_battle(dungeon_data)

        if narration:
            self._push_scene_dialog([narration], speaker="", callback=_start_boss)
        else:
            _start_boss()

    def _trigger_boss_battle(self, dungeon_data: Dict[str, Any]) -> None:
        """Start the boss battle for the given dungeon entry config."""
        from src.states.battle import BattleState
        from src.entities.enemy import Enemy

        self._ensure_data_loaded()
        boss_id = dungeon_data.get("boss_id", "")
        flag = dungeon_data.get("flag", "")
        boss_data = self._enemies_by_id.get(boss_id)
        if not boss_data:
            return

        enemy = Enemy(boss_data, x=80, y=16)

        # Chain boss (e.g. Black Knight after Beast King)
        chain_boss_id = dungeon_data.get("chain_boss_id", "")
        chain_flag = dungeon_data.get("chain_flag", "")
        chain_narration = dungeon_data.get("chain_narration", "")

        victory_flags = [flag] if flag else []

        if chain_boss_id and not self.game.quest_flags.get(chain_flag):
            # Build a callback that starts the chain boss after the first victory
            def _chain_after_victory() -> None:
                chain_data = self._enemies_by_id.get(chain_boss_id)
                if not chain_data:
                    return
                chain_enemy = Enemy(chain_data, x=80, y=16)

                def _start_chain() -> None:
                    battle = BattleState(
                        self.game,
                        [chain_enemy],
                        self.player,
                        victory_flags=[chain_flag] if chain_flag else [],
                    )
                    self.game.push_state(battle)

                if chain_narration:
                    self._push_scene_dialog([chain_narration], speaker="", callback=_start_chain)
                else:
                    _start_chain()

            battle = BattleState(
                self.game,
                [enemy],
                self.player,
                victory_flags=victory_flags,
                on_victory=_chain_after_victory,
            )
        else:
            battle = BattleState(
                self.game,
                [enemy],
                self.player,
                victory_flags=victory_flags,
            )

        self.game.push_state(battle)

    def _ensure_data_loaded(self) -> None:
        if self._data_loaded:
            return
        enemies_list = _load_json(os.path.join(DATA_DIR, "enemies.json"))
        self._enemies_by_id = {e["id"]: e for e in enemies_list}
        self._encounters_data = _load_json(os.path.join(DATA_DIR, "encounters.json"))
        self._data_loaded = True

    def _check_encounter(self) -> None:
        """Count tile steps and fire a random encounter when threshold is hit."""
        col, row = self.tilemap.pixel_to_tile(self.player.pos.x, self.player.pos.y)
        new_tile = (col, row)
        if new_tile == self._last_tile:
            return
        self._last_tile = new_tile

        tile_id = self.tilemap.tile_at(col, row)
        if tile_id in (TILE_WALL, TILE_WATER, TILE_TOWN, TILE_ZONE_EXIT, TILE_DUNGEON):
            return

        if self._encounter.step():
            self._trigger_encounter()

    def _trigger_encounter(self) -> None:
        """Pick a random enemy group for the current zone and start a battle."""
        from src.states.battle import BattleState
        from src.entities.enemy import Enemy

        self._ensure_data_loaded()
        zone_data = self._encounters_data.get("zones", {}).get(self._zone, {})
        groups = zone_data.get("groups", [])
        if not groups:
            return

        group = random.choice(groups)
        enemies = []
        for i, enemy_id in enumerate(group):
            data = self._enemies_by_id.get(enemy_id)
            if data:
                enemies.append(Enemy(data, x=16 + i * 56, y=16))

        if enemies:
            self.game.push_state(BattleState(self.game, enemies, self.player))

    def _draw_hud(self, surface: pygame.Surface) -> None:
        """Draw the in-world heads-up display."""
        font = pygame.font.SysFont("monospace", 7)

        area_surf = font.render(self._display_name, True, WHITE)
        surface.blit(area_surf, (4, 4))

        p = self.player
        hud_text = f"HP:{p.hp}/{p.max_hp}  MP:{p.mp}/{p.max_mp}  G:{p.gold}"
        hud_surf = font.render(hud_text, True, (180, 255, 180))
        surface.blit(hud_surf, (4, 14))

        hint_surf = font.render(
            "WASD/Arrows: move  Z: talk  ESC: menu", True, (160, 160, 160)
        )
        surface.blit(hint_surf, (4, NATIVE_HEIGHT - 10))

        # Contextual banners
        if self._town_cooldown <= 0:
            col, row = self.tilemap.pixel_to_tile(
                self.player.rect.centerx, self.player.rect.centery
            )
            tile_id = self.tilemap.tile_at(col, row)

            if tile_id == TILE_TOWN:
                town_name = self.tilemap.town_entrances.get((col, row), "")
                if town_name:
                    lbl = font.render(
                        f"Entering {town_name.capitalize()}...", True, YELLOW
                    )
                    surface.blit(
                        lbl, lbl.get_rect(centerx=NATIVE_WIDTH // 2, top=4)
                    )

            elif tile_id == TILE_ZONE_EXIT:
                exit_data = self.tilemap.zone_exits.get((col, row))
                if exit_data:
                    next_zone = exit_data[0].replace("_", " ").title()
                    lbl = font.render(f"→ {next_zone}", True, YELLOW)
                    surface.blit(lbl, lbl.get_rect(centerx=NATIVE_WIDTH // 2, top=4))

            elif tile_id == TILE_DUNGEON:
                dungeon_data = self.tilemap.dungeon_entries.get((col, row))
                if dungeon_data:
                    flag = dungeon_data.get("flag", "")
                    if flag and self.game.quest_flags.get(flag):
                        lbl = font.render("Area cleared", True, (100, 200, 100))
                    else:
                        lbl = font.render("[Z] Enter dungeon", True, YELLOW)
                    surface.blit(lbl, lbl.get_rect(centerx=NATIVE_WIDTH // 2, top=4))

            else:
                # Show hidden-wall hint when adjacent
                for dc, dr in [(0, 0), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                    if self.tilemap.tile_at(col + dc, row + dr) == TILE_HIDDEN:
                        lbl = font.render("[Z] Examine wall", True, (180, 180, 140))
                        surface.blit(lbl, lbl.get_rect(centerx=NATIVE_WIDTH // 2, top=4))
                        break

