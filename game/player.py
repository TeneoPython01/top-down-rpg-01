"""
game/player.py - Player class with keyboard-driven movement.
"""

import pygame
from game.settings import PLAYER_SPEED, PLAYER_COLOR, PLAYER_SIZE, TILE_SIZE


class Player(pygame.sprite.Sprite):
    """The player character."""

    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(PLAYER_COLOR)
        # Center the player inside the spawn tile
        offset = (TILE_SIZE - PLAYER_SIZE) // 2
        self.rect = self.image.get_rect(
            topleft=(x * TILE_SIZE + offset, y * TILE_SIZE + offset)
        )
        self.velocity = pygame.Vector2(0, 0)
        self.pos = pygame.Vector2(self.rect.topleft)

    def handle_input(self) -> None:
        """Read keyboard state and set velocity."""
        keys = pygame.key.get_pressed()
        self.velocity = pygame.Vector2(0, 0)

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity.y = -PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity.y = PLAYER_SPEED

        # Normalize diagonal movement
        if self.velocity.length() > 0:
            self.velocity = self.velocity.normalize() * PLAYER_SPEED

    def update(self, dt: float, walls: pygame.sprite.Group) -> None:
        """Update position with collision detection."""
        self.handle_input()

        # Move horizontally and resolve collisions
        self.pos.x += self.velocity.x * dt
        self.rect.x = round(self.pos.x)
        self._resolve_collisions(walls, axis="x")

        # Move vertically and resolve collisions
        self.pos.y += self.velocity.y * dt
        self.rect.y = round(self.pos.y)
        self._resolve_collisions(walls, axis="y")

    def _resolve_collisions(
        self, walls: pygame.sprite.Group, axis: str
    ) -> None:
        """Push the player out of any overlapping wall tiles."""
        for wall in pygame.sprite.spritecollide(self, walls, False):
            if axis == "x":
                if self.velocity.x > 0:
                    self.rect.right = wall.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = wall.rect.right
                self.pos.x = float(self.rect.x)
            else:
                if self.velocity.y > 0:
                    self.rect.bottom = wall.rect.top
                elif self.velocity.y < 0:
                    self.rect.top = wall.rect.bottom
                self.pos.y = float(self.rect.y)
