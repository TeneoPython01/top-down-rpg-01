"""
src/states/world_map.py - Full-screen world map overlay.

Displays all overworld zones as small pre-rendered tiles arranged on a fixed
grid.  Visited zones are shown in full colour; unvisited zones are darkened.
The player's current zone is highlighted with a blinking marker.

Press M or ESC to close and return to the overworld.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

import pygame

from settings import (
    BLACK,
    DARK_GRAY,
    LIGHT_GRAY,
    MINIMAP_ALPHA,
    MINIMAP_BORDER_COLOR,
    MINIMAP_PLAYER_COLOR,
    MINIMAP_TILE_SIZE,
    MINIMAP_UNVISITED_COLOR,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
    TILE_COLORS,
    WHITE,
    WORLD_MAP_ZONE_POSITIONS,
    WORLD_MAP_ZONE_SIZE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.utils.tilemap import get_all_zones

if TYPE_CHECKING:
    from src.game import Game


def _build_zone_surface(
    map_data: list,
    cell_w: int,
    cell_h: int,
    visited: bool,
) -> pygame.Surface:
    """Pre-render a zone map into a *cell_w* × *cell_h* surface.

    Each tile in the map is reduced to a single pixel (or fraction) using
    MINIMAP_TILE_SIZE.  Unvisited zones are filled with MINIMAP_UNVISITED_COLOR
    instead of their true colours.
    """
    surf = pygame.Surface((cell_w, cell_h))
    surf.fill(BLACK)

    rows = len(map_data)
    cols = max(len(r) for r in map_data) if rows else 0
    if rows == 0 or cols == 0:
        return surf

    # Fit the entire map into the cell
    px_per_col = cell_w / cols
    px_per_row = cell_h / rows

    for r, row in enumerate(map_data):
        for c, tile_id in enumerate(row):
            x = int(c * px_per_col)
            y = int(r * px_per_row)
            w = max(1, int((c + 1) * px_per_col) - x)
            h = max(1, int((r + 1) * px_per_row) - y)
            if visited:
                color = TILE_COLORS.get(tile_id, TILE_COLORS[0])
            else:
                color = MINIMAP_UNVISITED_COLOR
            pygame.draw.rect(surf, color, (x, y, w, h))

    return surf


class WorldMapState(BaseState):
    """Full-screen world map showing all zones with the player's position.

    is_overlay is False so the overworld beneath is not rendered (the world
    map fills the entire native surface).
    """

    is_overlay: bool = False

    # Blinking frequency for the current-zone highlight (flips every N seconds)
    _BLINK_PERIOD = 0.5

    def __init__(self, game: "Game", player: Any, current_zone: str) -> None:
        super().__init__(game)
        self._player = player
        self._current_zone = current_zone
        self._blink_timer = 0.0
        self._blink_on = True

        # Pre-render each zone cell once
        cell_w, cell_h = WORLD_MAP_ZONE_SIZE
        self._zone_surfs: Dict[str, pygame.Surface] = {}
        all_zones = get_all_zones()
        for zone_name, zone_data in all_zones.items():
            visited = zone_name in getattr(player, "visited_zones", set())
            surf = _build_zone_surface(zone_data["map"], cell_w, cell_h, visited)
            self._zone_surfs[zone_name] = surf

        self._font: pygame.font.Font | None = None
        self._font_sm: pygame.font.Font | None = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def enter(self) -> None:
        self._blink_timer = 0.0
        self._blink_on = True

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 8)
        return self._font

    def _get_font_sm(self) -> pygame.font.Font:
        if self._font_sm is None:
            self._font_sm = pygame.font.SysFont("monospace", 7)
        return self._font_sm

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (
            pygame.K_ESCAPE,
            pygame.K_m,
        ):
            self.game.pop_state()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        self._blink_timer += dt
        if self._blink_timer >= self._BLINK_PERIOD:
            self._blink_timer -= self._BLINK_PERIOD
            self._blink_on = not self._blink_on

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill((10, 10, 20))
        font = self._get_font()
        font_sm = self._get_font_sm()

        # Title
        title = font.render("World Map", True, YELLOW)
        surface.blit(title, title.get_rect(centerx=NATIVE_WIDTH // 2, top=4))

        cell_w, cell_h = WORLD_MAP_ZONE_SIZE
        all_zones = get_all_zones()

        # Determine grid bounds so we can centre the layout
        positions = {z: WORLD_MAP_ZONE_POSITIONS[z] for z in WORLD_MAP_ZONE_POSITIONS}
        if not positions:
            return
        max_gc = max(p[0] for p in positions.values())
        max_gr = max(p[1] for p in positions.values())

        gap = 6  # pixels between cells
        total_w = (max_gc + 1) * (cell_w + gap) - gap
        total_h = (max_gr + 1) * (cell_h + gap) - gap
        origin_x = (NATIVE_WIDTH - total_w) // 2
        origin_y = 18  # below the title

        for zone_name, (gc, gr) in positions.items():
            cx = origin_x + gc * (cell_w + gap)
            cy = origin_y + gr * (cell_h + gap)
            cell_rect = pygame.Rect(cx, cy, cell_w, cell_h)

            # Zone surface (greyed out if unvisited)
            zone_surf = self._zone_surfs.get(zone_name)
            if zone_surf:
                surface.blit(zone_surf, (cx, cy))

            # Highlight the current zone with a blinking border
            if zone_name == self._current_zone and self._blink_on:
                pygame.draw.rect(surface, MINIMAP_PLAYER_COLOR, cell_rect, 2)
            else:
                pygame.draw.rect(surface, MINIMAP_BORDER_COLOR, cell_rect, 1)

            # Zone label beneath the cell
            visited = zone_name in getattr(self._player, "visited_zones", set())
            if visited:
                display = all_zones[zone_name].get(
                    "display_name", zone_name.replace("_", " ").title()
                )
                label_color = WHITE if zone_name != self._current_zone else YELLOW
            else:
                display = "???"
                label_color = LIGHT_GRAY
            lbl = font_sm.render(display, True, label_color)
            surface.blit(lbl, lbl.get_rect(centerx=cx + cell_w // 2, top=cy + cell_h + 2))

        # Hint bar at the bottom
        hint = font_sm.render("M / ESC: close map", True, (120, 120, 160))
        surface.blit(hint, hint.get_rect(centerx=NATIVE_WIDTH // 2, bottom=NATIVE_HEIGHT - 2))
