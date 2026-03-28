"""
src/states/overworld.py - Overworld exploration state.

Handles tile-map rendering, player movement, camera, collision, NPC
interaction, and random encounter triggering.
"""

from __future__ import annotations

import json
import os
import random
from typing import TYPE_CHECKING, Any, List

import pygame

from settings import (
    DATA_DIR,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
    TILE_TOWN,
    TILE_WALL,
    TILE_WATER,
    TOWN_ENTRY_COOLDOWN,
    WHITE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.npc import NPC
from src.systems.camera import Camera
from src.systems.encounter import EncounterSystem
from src.utils.tilemap import TileMap
from src.utils.town_maps import OVERWORLD_TOWN_ENTRANCES

if TYPE_CHECKING:
    from src.game import Game

# ── NPC definitions for the Ashenvale overworld map ──────────────────────────
# Each entry: dialog_id (key in dialog.json), display name, tile col, tile row.
_ASHENVALE_NPCS = [
    {"dialog_id": "village_elder_before", "name": "Village Elder", "col": 10, "row": 4},
    {"dialog_id": "farmer_ashenvale",     "name": "Farmer",        "col": 8,  "row": 14},
    {"dialog_id": "healer_npc",           "name": "Healer",        "col": 20, "row": 9},
]

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

    def __init__(self, game: "Game", player: Player | None = None) -> None:
        super().__init__(game)
        self.tilemap = TileMap(town_entrances=OVERWORLD_TOWN_ENTRANCES)

        # Reuse an existing player (e.g. loaded from save or returning from
        # battle), or create a fresh one for a new game.
        if player is None:
            spawn_col, spawn_row = self.tilemap.spawn
            self.player = Player(spawn_col, spawn_row)
        else:
            self.player = player

        # Register player with the game object for save/load access.
        game.player = self.player

        self.camera = Camera(self.tilemap.pixel_width, self.tilemap.pixel_height)

        # ── Encounter system ──────────────────────────────────────────────────
        self._zone = "grasslands"
        self._encounter = EncounterSystem(encounter_rate=20)
        self._last_tile = self.tilemap.pixel_to_tile(
            self.player.pos.x, self.player.pos.y
        )
        self._enemies_by_id: dict = {}
        self._encounters_data: dict = {}
        self._data_loaded = False

        self._town_cooldown = 0.0
        # Only show the intro scene once per OverworldState instance.
        # When a player is passed in (load/return from battle) we skip it.
        self._intro_shown = player is not None

        # ── Dialog / NPC data ─────────────────────────────────────────────────
        dialog_path = os.path.join(DATA_DIR, "dialog.json")
        with open(dialog_path, encoding="utf-8") as fh:
            self._dialog_data: dict = json.load(fh)

        self._npcs: List[NPC] = [
            NPC(spec, col=spec["col"], row=spec["row"], color_index=idx)
            for idx, spec in enumerate(_ASHENVALE_NPCS)
        ]

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        self._town_cooldown = TOWN_ENTRY_COOLDOWN
        self.game.current_location = "overworld"
        # Show the intro scene the first time the player enters the overworld.
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

        # Town entrance detection
        if self._town_cooldown > 0:
            self._town_cooldown = max(0.0, self._town_cooldown - dt)
        else:
            col, row = self.tilemap.pixel_to_tile(
                self.player.rect.centerx, self.player.rect.centery
            )
            if self.tilemap.tile_at(col, row) == TILE_TOWN:
                town_name = self.tilemap.town_entrances.get((col, row), "")
                if town_name:
                    from src.states.town import TownState
                    self.game.push_state(TownState(self.game, town_name))

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        self.tilemap.draw(surface, self.camera.offset)

        # NPCs sorted by y so closer characters render on top.
        for npc in sorted(self._npcs, key=lambda n: n.rect.bottom):
            npc.draw(surface, self.camera.offset)

        surface.blit(self.player.image, self.player.rect.move(self.camera.offset))

        self._draw_hud(surface)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _try_interact(self) -> None:
        """Check for a nearby NPC and push a DialogState if found."""
        player_center = pygame.Vector2(self.player.rect.center)
        for npc in self._npcs:
            npc_center = pygame.Vector2(npc.rect.center)
            if player_center.distance_to(npc_center) <= self._INTERACT_RANGE:
                entry = self._dialog_data.get(npc.dialog_id)
                if entry:
                    lines = entry.get("lines", [])
                    self._push_npc_dialog(lines, speaker=npc.name)
                    return

    def _push_npc_dialog(self, lines: List[str], speaker: str) -> None:
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines, speaker=speaker))

    def _push_scene_dialog(self, lines: List[str], speaker: str = "") -> None:
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines, speaker=speaker))

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
        if tile_id in (TILE_WALL, TILE_WATER, TILE_TOWN):
            return  # no random encounters on special tiles

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

        area_surf = font.render("Ashenvale", True, WHITE)
        surface.blit(area_surf, (4, 4))

        p = self.player
        hud_text = f"HP:{p.hp}/{p.max_hp}  MP:{p.mp}/{p.max_mp}  G:{p.gold}"
        hud_surf = font.render(hud_text, True, (180, 255, 180))
        surface.blit(hud_surf, (4, 14))

        hint_surf = font.render(
            "WASD/Arrows: move  Z: talk  ESC: menu", True, (160, 160, 160)
        )
        surface.blit(hint_surf, (4, NATIVE_HEIGHT - 10))

        # Town-name banner when standing on an entrance tile
        if self._town_cooldown <= 0:
            col, row = self.tilemap.pixel_to_tile(
                self.player.rect.centerx, self.player.rect.centery
            )
            if self.tilemap.tile_at(col, row) == TILE_TOWN:
                town_name = self.tilemap.town_entrances.get((col, row), "")
                if town_name:
                    lbl = font.render(
                        f"Entering {town_name.capitalize()}...", True, YELLOW
                    )
                    surface.blit(
                        lbl, lbl.get_rect(centerx=NATIVE_WIDTH // 2, top=4)
                    )
