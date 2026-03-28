"""
src/entities/npc.py - NPC entity (Phase 4).
"""

from __future__ import annotations

from typing import Dict, Any

import pygame

from settings import TILE_SIZE, FONT_NAME, FONT_SIZE_SMALL, WHITE, BLACK, DARK_GRAY, LIGHT_GRAY, NPC_SKIN_COLOR


# Unique colours per NPC role so they're easy to distinguish on the map.
_NPC_COLORS: list[tuple[int, int, int]] = [
    (180, 100, 60),   # brownish — elder
    (80, 160, 80),    # green — farmer
    (160, 80, 160),   # purple — healer / mage
    (200, 160, 60),   # gold
    (60, 160, 200),   # cyan
]


def _build_sprite(color: tuple[int, int, int]) -> pygame.Surface:
    """Draw a simple 16×16 humanoid placeholder for an NPC."""
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    # Robe / body
    pygame.draw.rect(surf, color, (3, 5, 10, 9))
    # Head
    pygame.draw.rect(surf, NPC_SKIN_COLOR, (4, 0, 8, 7))
    # Eyes
    pygame.draw.rect(surf, BLACK, (6, 2, 2, 2))
    pygame.draw.rect(surf, BLACK, (9, 2, 2, 2))
    # Simple feet
    pygame.draw.rect(surf, (60, 40, 20), (3, 14, 4, 2))
    pygame.draw.rect(surf, (60, 40, 20), (9, 14, 4, 2))
    return surf
from settings import TILE_SIZE, LIGHT_GRAY, BLACK, WHITE


class NPC(pygame.sprite.Sprite):
    """A non-player character with a dialog reference and sprite.

    Parameters
    ----------
    data:
        Dict with at least ``"name"`` and ``"dialog_id"`` keys.
    col, row:
        Tile-grid position.
    color_index:
        Index into the internal colour palette (cycles automatically).
        Dict with keys: name, dialog_id, and optional color (RGB tuple).
    col, row:
        Tile-grid position of the NPC.
    """

    def __init__(
        self,
        data: Dict[str, Any],
        col: int,
        row: int,
        color_index: int = 0,
    ) -> None:
        super().__init__()
        self.name: str = data.get("name", "NPC")
        self.dialog_id: str = data.get("dialog_id", "")

        color = _NPC_COLORS[color_index % len(_NPC_COLORS)]
        self.image = _build_sprite(color)
        color = data.get("color", LIGHT_GRAY)

        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        # Simple face: two dark eye dots
        pygame.draw.rect(self.image, BLACK, (4, 5, 2, 2))
        pygame.draw.rect(self.image, BLACK, (10, 5, 2, 2))
        # White highlight on top half to suggest a head shape
        pygame.draw.rect(self.image, WHITE, (5, 1, 6, 3))

        self.rect = self.image.get_rect(
            topleft=(col * TILE_SIZE, row * TILE_SIZE)
        )

        # Pre-render the name label (drawn just above the sprite each frame).
        self._name_label: pygame.Surface = self._make_label()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _make_label(self) -> pygame.Surface:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        text_surf = font.render(self.name, True, WHITE)
        w = text_surf.get_width() + 4
        h = text_surf.get_height() + 2
        label = pygame.Surface((w, h), pygame.SRCALPHA)
        label.fill((0, 0, 0, 160))
        label.blit(text_surf, (2, 1))
        return label

    # ── Public API ────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera_offset: pygame.Vector2) -> None:
        """Blit the sprite and name label at the camera-adjusted position."""
        draw_pos = self.rect.move(camera_offset)
        surface.blit(self.image, draw_pos)
        # Centre the label above the sprite
        lx = draw_pos.x + (TILE_SIZE - self._name_label.get_width()) // 2
        ly = draw_pos.y - self._name_label.get_height() - 1
        surface.blit(self._name_label, (lx, ly))

    def interaction_rect(self) -> pygame.Rect:
        """Return a slightly enlarged rect used to detect player proximity."""
        return self.rect.inflate(8, 8)
