"""
src/entities/player.py - Player entity with 4-directional movement and animation.

Art placeholder: the sprite is a colored rectangle until real walk-cycle
sprites are added in a later phase.
"""

from __future__ import annotations

from typing import Dict, List

import pygame

from settings import (
    PLAYER_SPEED,
    PLAYER_SIZE,
    PLAYER_ANIM_FPS,
    TILE_SIZE,
    BLUE,
    WHITE,
    DIR_DOWN,
    DIR_LEFT,
    DIR_RIGHT,
    DIR_UP,
)
from src.utils.animation import Animation


def _make_placeholder_frames(color: tuple, direction: int) -> List[pygame.Surface]:
    """Create two simple colored-rectangle frames for *direction*.

    Frame 0: body + hat (idle pose).
    Frame 1: body + hat + tiny leg shift (walk pose).
    """
    frames = []
    for frame_idx in range(2):
        surf = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(surf, color, (3, 4, 10, 10))
        # Head
        pygame.draw.rect(surf, WHITE, (4, 0, 8, 6))
        # Directional marker (tiny dot showing which way the player faces)
        markers = {
            DIR_DOWN: (7, 11),
            DIR_UP: (7, 2),
            DIR_LEFT: (3, 6),
            DIR_RIGHT: (11, 6),
        }
        mx, my = markers[direction]
        pygame.draw.rect(surf, (255, 255, 0), (mx, my, 2, 2))
        # Walk animation: shift legs on frame 1
        if frame_idx == 1:
            leg_shift = 1 if direction in (DIR_LEFT, DIR_RIGHT) else 0
            foot_y = 13 + leg_shift
            pygame.draw.rect(surf, (30, 30, 120), (4, foot_y, 3, 2))
            pygame.draw.rect(surf, (30, 30, 120), (9, foot_y - leg_shift, 3, 2))
        else:
            pygame.draw.rect(surf, (30, 30, 120), (4, 13, 3, 2))
            pygame.draw.rect(surf, (30, 30, 120), (9, 13, 3, 2))
        frames.append(surf)
    return frames


class Player(pygame.sprite.Sprite):
    """The player character — White Knight.

    Attributes
    ----------
    pos:
        Sub-pixel precise position (native pixels), top-left of the sprite.
    rect:
        Integer pixel rect used for rendering and collision.
    direction:
        Current facing direction (DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT).
    velocity:
        Current movement vector in native pixels per second.
    """

    def __init__(self, spawn_col: int, spawn_row: int) -> None:
        super().__init__()
        self.direction = DIR_DOWN
        self._moving = False

        # Build placeholder animation sets
        self._animations: Dict[int, Animation] = {
            DIR_DOWN: Animation(_make_placeholder_frames(BLUE, DIR_DOWN), fps=PLAYER_ANIM_FPS),
            DIR_LEFT: Animation(_make_placeholder_frames(BLUE, DIR_LEFT), fps=PLAYER_ANIM_FPS),
            DIR_RIGHT: Animation(_make_placeholder_frames(BLUE, DIR_RIGHT), fps=PLAYER_ANIM_FPS),
            DIR_UP: Animation(_make_placeholder_frames(BLUE, DIR_UP), fps=PLAYER_ANIM_FPS),
        }
        self._idle: Dict[int, pygame.Surface] = {
            d: anim.frames[0] for d, anim in self._animations.items()
        }

        self.image = self._idle[DIR_DOWN]
        # Centre the sprite within its spawn tile
        margin = (TILE_SIZE - PLAYER_SIZE) // 2
        px = spawn_col * TILE_SIZE + margin
        py = spawn_row * TILE_SIZE + margin
        self.rect = self.image.get_rect(topleft=(px, py))
        self.pos = pygame.Vector2(self.rect.topleft)
        self.velocity = pygame.Vector2(0, 0)

    # ── Private helpers ───────────────────────────────────────────────────────

    def _handle_input(self) -> None:
        """Read keyboard state and set velocity + direction."""
        keys = pygame.key.get_pressed()
        dx = dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
            self.direction = DIR_LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
            self.direction = DIR_RIGHT

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
            self.direction = DIR_UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
            self.direction = DIR_DOWN

        vec = pygame.Vector2(dx, dy)
        if vec.length() > 0:
            vec = vec.normalize()
        self.velocity = vec * PLAYER_SPEED
        self._moving = vec.length() > 0

    def _resolve_collisions(
        self, blocked_rects: List[pygame.Rect], axis: str
    ) -> None:
        """Push the player out of any overlapping blocked tile rects."""
        for wall in blocked_rects:
            if self.rect.colliderect(wall):
                if axis == "x":
                    if self.velocity.x > 0:
                        self.rect.right = wall.left
                    elif self.velocity.x < 0:
                        self.rect.left = wall.right
                    self.pos.x = float(self.rect.x)
                else:
                    if self.velocity.y > 0:
                        self.rect.bottom = wall.top
                    elif self.velocity.y < 0:
                        self.rect.top = wall.bottom
                    self.pos.y = float(self.rect.y)

    # ── Public API ────────────────────────────────────────────────────────────

    def update(self, dt: float, blocked_rects: List[pygame.Rect]) -> None:
        """Update position and animation for this frame."""
        self._handle_input()

        # Move X
        self.pos.x += self.velocity.x * dt
        self.rect.x = round(self.pos.x)
        self._resolve_collisions(blocked_rects, "x")

        # Move Y
        self.pos.y += self.velocity.y * dt
        self.rect.y = round(self.pos.y)
        self._resolve_collisions(blocked_rects, "y")

        # Animate
        anim = self._animations[self.direction]
        if self._moving:
            anim.update(dt)
            self.image = anim.current_frame
        else:
            anim.reset()
            self.image = self._idle[self.direction]
