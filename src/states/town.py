"""
src/states/town.py - Town exploration state (Phase 4).

Similar to OverworldState but without random encounters.
Features: NPC interaction, shop/inn event tiles, exit back to overworld.
"""

from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING, Dict, Any, List, Optional

import pygame

from settings import (
    NATIVE_WIDTH,
    NATIVE_HEIGHT,
    PLAYER_SIZE,
    TILE_SIZE,
    TOWN_EVENT_COOLDOWN,
    FONT_NAME,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    WHITE,
    YELLOW,
    DATA_DIR,
)
from src.states.base_state import BaseState
from src.entities.player import Player
from src.entities.npc import NPC
from src.systems.camera import Camera
from src.utils.tilemap import TileMap

if TYPE_CHECKING:
    from src.game import Game


class TownState(BaseState):
    """Town exploration — no random encounters, NPC interaction, shops, inn."""

    def __init__(self, game: "Game", town_name: str) -> None:
        super().__init__(game)
        self.town_name = town_name.lower()

        from src.utils.town_maps import get_town_data
        town_data = get_town_data(self.town_name)

        self._display_name: str = town_data.get("display_name", town_name.capitalize())
        self._events: Dict[tuple, Dict[str, Any]] = town_data.get("events", {})

        # Tile map
        self.tilemap = TileMap(
            data=town_data["tiles"],
            spawn=town_data["spawn"],
        )

        # Player: reuse the overworld player and teleport it to the town spawn.
        spawn_col, spawn_row = town_data["spawn"]
        if game.player is not None:
            self.player = game.player
        else:
            self.player = Player(spawn_col, spawn_row)
            game.player = self.player
        # Move player to town spawn position.
        _margin = (TILE_SIZE - PLAYER_SIZE) // 2
        _px = spawn_col * TILE_SIZE + _margin
        _py = spawn_row * TILE_SIZE + _margin
        self.player.pos = pygame.Vector2(_px, _py)
        self.player.rect.topleft = (round(_px), round(_py))

        # Camera
        self.camera = Camera(
            self.tilemap.pixel_width,
            self.tilemap.pixel_height,
        )

        # NPCs
        self._npcs: List[NPC] = [
            NPC(npc_data, npc_data["col"], npc_data["row"])
            for npc_data in town_data.get("npcs", [])
        ]

        # Dialog data loaded once
        self._dialog: Dict[str, Any] = self._load_dialog()

        # Interaction state
        self._near_npc: Optional[NPC] = None
        self._last_event_tile: tuple = (-1, -1)
        self._event_cooldown = 0.0

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        # Brief cooldown prevents the exit tile from immediately retriggering
        # if e.g. a sub-state (dialog, shop) just popped back to this state.
        self._event_cooldown = TOWN_EVENT_COOLDOWN
        self.game.current_location = f"town:{self.town_name}"
        self.game.audio.play_music("town")

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_ESCAPE:
            self.game.pop_state()
        elif event.key in (pygame.K_z, pygame.K_RETURN, pygame.K_KP_ENTER):
            if self._near_npc is not None:
                self._start_dialog(self._near_npc.dialog_id)

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self.player.update(dt, self.tilemap.blocked_rects)
        self.camera.update(self.player)

        # NPC proximity check
        interact_zone = self.player.rect.inflate(TILE_SIZE, TILE_SIZE)
        self._near_npc = None
        for npc in self._npcs:
            if interact_zone.colliderect(npc.rect):
                self._near_npc = npc
                break

        # Tile event check (with cooldown to avoid double-triggers)
        if self._event_cooldown > 0:
            self._event_cooldown = max(0.0, self._event_cooldown - dt)
        else:
            col, row = self.tilemap.pixel_to_tile(
                self.player.rect.centerx, self.player.rect.centery
            )
            tile_pos = (col, row)
            if tile_pos != self._last_event_tile:
                self._last_event_tile = tile_pos
                if tile_pos in self._events:
                    self._trigger_event(self._events[tile_pos])

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        # Tile map
        self.tilemap.draw(surface, self.camera.offset)

        # NPCs
        for npc in self._npcs:
            surface.blit(npc.image, npc.rect.move(self.camera.offset))

        # Player (drawn on top of NPCs)
        surface.blit(self.player.image, self.player.rect.move(self.camera.offset))

        # HUD
        self._draw_hud(surface)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _trigger_event(self, event_data: Dict[str, Any]) -> None:
        etype = event_data.get("type", "")
        if etype == "exit":
            self.game.pop_state()
        elif etype == "shop":
            from src.states.shop import ShopState
            self.game.push_state(ShopState(self.game, event_data["shop_id"]))
        elif etype == "inn":
            from src.states.inn import InnState
            self.game.push_state(InnState(self.game))
        elif etype == "journal":
            # Ancestral home in Subterra: show the journal + give Exo items
            self._trigger_journal_event()

    def _start_dialog(self, dialog_id: str) -> None:
        entry = self._dialog.get(dialog_id, {})
        lines: List[str] = entry.get("lines", ["..."])
        from src.states.dialog import DialogState
        self.game.push_state(DialogState(self.game, lines))

    def _trigger_journal_event(self) -> None:
        """Show the grandmother's journal and grant Exo Weapon + Exo Armor."""
        entry = self._dialog.get("journal_grandmother", {})
        lines: List[str] = entry.get("lines", ["A journal, worn with age."])

        already_found = self.game.quest_flags.get("journal_found")

        def _on_journal_close() -> None:
            if not already_found:
                self.game.quest_flags.set("journal_found")
                # Grant the Exo Weapon and Exo Armor
                inv = self.game.inventory
                inv.add("exo_weapon", 1)
                inv.add("exo_armor", 1)
                reward_entry = self._dialog.get("journal_reward", {})
                reward_lines = reward_entry.get(
                    "lines",
                    [
                        "You found the Exo Weapon and Exo Armor hidden behind the journal!",
                        "These ancient tools have been waiting for the right hands.",
                    ],
                )
                from src.states.dialog import DialogState
                self.game.push_state(
                    DialogState(self.game, reward_lines, speaker="Discovery")
                )

        from src.states.dialog import DialogState
        self.game.push_state(
            DialogState(self.game, lines, speaker="Journal of Elena", callback=_on_journal_close)
        )

    def _load_dialog(self) -> Dict[str, Any]:
        path = os.path.join(DATA_DIR, "dialog.json")
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except (OSError, json.JSONDecodeError):
            return {}

    def _draw_hud(self, surface: pygame.Surface) -> None:
        font_sm = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)

        # Town name — top left
        name_surf = font_sm.render(self._display_name, True, WHITE)
        surface.blit(name_surf, (4, 4))

        # Gold — top right
        gold_text = f"Gold: {self.game.inventory.gold}G"
        gold_surf = font_sm.render(gold_text, True, YELLOW)
        surface.blit(gold_surf, (NATIVE_WIDTH - gold_surf.get_width() - 4, 4))

        # NPC interaction hint — bottom centre
        if self._near_npc is not None:
            hint = font_sm.render(
                f"[Z] Talk to {self._near_npc.name}", True, YELLOW
            )
            surface.blit(
                hint,
                hint.get_rect(centerx=NATIVE_WIDTH // 2, bottom=NATIVE_HEIGHT - 12),
            )

        # Controls hint — bottom left
        ctrl = font_sm.render(
            "WASD: move  Z: talk  ESC: exit town", True, (160, 160, 160)
        )
        surface.blit(ctrl, (4, NATIVE_HEIGHT - 10))
