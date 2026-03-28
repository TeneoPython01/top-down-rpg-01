<<<<<<< HEAD
<<<<<<< HEAD
"""Player class with keyboard-driven movement and collision detection."""

import pygame
from game.settings import (
    PLAYER_SPEED,
    PLAYER_SIZE,
    TILE_SIZE,
    YELLOW,
    BLACK,
)


class Player(pygame.sprite.Sprite):
    """The player character.

    Args:
        x: Starting world x-position in pixels.
        y: Starting world y-position in pixels.
    """

    def __init__(self, x: int, y: int) -> None:
        super().__init__()

        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE), pygame.SRCALPHA)
        self._draw_sprite()

        self.rect = self.image.get_rect(topleft=(x, y))
        self.velocity = pygame.math.Vector2(0, 0)

    def _draw_sprite(self) -> None:
        """Draw a simple placeholder sprite (yellow circle with eyes)."""
        self.image.fill((0, 0, 0, 0))  # transparent background
        center = PLAYER_SIZE // 2
        radius = PLAYER_SIZE // 2 - 1
        pygame.draw.circle(self.image, YELLOW, (center, center), radius)
        pygame.draw.circle(self.image, BLACK, (center, center), radius, 2)
        # Eyes
        eye_offset = PLAYER_SIZE // 5
        pygame.draw.circle(self.image, BLACK, (center - eye_offset, center - eye_offset + 2), 2)
        pygame.draw.circle(self.image, BLACK, (center + eye_offset, center - eye_offset + 2), 2)

    def handle_input(self) -> None:
        """Read keyboard state and set the velocity vector."""
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0
=======
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
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity.y = -PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity.y = PLAYER_SPEED

<<<<<<< HEAD
    def move(self, solid_tiles: pygame.sprite.Group) -> None:
        """Move the player and resolve collisions with solid tiles.

        Horizontal and vertical movement are resolved separately so the
        player can slide along walls.

        Args:
            solid_tiles: Sprite group containing all non-walkable tiles.
        """
        # Horizontal movement
        self.rect.x += int(self.velocity.x)
        self._resolve_collisions(solid_tiles, axis="x")

        # Vertical movement
        self.rect.y += int(self.velocity.y)
        self._resolve_collisions(solid_tiles, axis="y")

    def _resolve_collisions(
        self, solid_tiles: pygame.sprite.Group, axis: str
    ) -> None:
        """Push the player out of any overlapping solid tile.

        Args:
            solid_tiles: Sprite group of solid tiles.
            axis: ``"x"`` or ``"y"`` — the axis being resolved.
        """
        hits = pygame.sprite.spritecollide(self, solid_tiles, False)
        for tile in hits:
            if axis == "x":
                if self.velocity.x > 0:
                    self.rect.right = tile.rect.left
                elif self.velocity.x < 0:
                    self.rect.left = tile.rect.right
            else:
                if self.velocity.y > 0:
                    self.rect.bottom = tile.rect.top
                elif self.velocity.y < 0:
                    self.rect.top = tile.rect.bottom

    def update(self, solid_tiles: pygame.sprite.Group) -> None:
        """Full update step called once per frame.

        Args:
            solid_tiles: Sprite group of solid tiles for collision checks.
        """
        self.handle_input()
        self.move(solid_tiles)
=======
import pygame
from game.settings import TILE_SIZE, PLAYER_SPEED


class Player(pygame.sprite.Sprite):
    """Player character controlled by the keyboard."""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4), pygame.SRCALPHA)
        # Draw a simple face so orientation is clear
        pygame.draw.circle(self.image, (255, 200, 100), (14, 14), 14)
        pygame.draw.circle(self.image, (0, 0, 0), (9, 10), 3)
        pygame.draw.circle(self.image, (0, 0, 0), (19, 10), 3)
        pygame.draw.arc(self.image, (0, 0, 0),
                        pygame.Rect(7, 14, 14, 10), 3.14, 0, 2)
        self.rect = self.image.get_rect(topleft=(x * TILE_SIZE, y * TILE_SIZE))
        self._vx = 0
        self._vy = 0

    def handle_input(self):
        keys = pygame.key.get_pressed()
        self._vx = 0
        self._vy = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self._vx = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self._vx = PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self._vy = -PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self._vy = PLAYER_SPEED

    def move(self, wall_tiles):
        """Move and resolve collisions against *wall_tiles* sprite group."""
        self.rect.x += self._vx
        self._collide(wall_tiles, "x")
        self.rect.y += self._vy
        self._collide(wall_tiles, "y")

    def _collide(self, wall_tiles, direction):
        for tile in pygame.sprite.spritecollide(self, wall_tiles, False):
            if direction == "x":
                if self._vx > 0:
                    self.rect.right = tile.rect.left
                elif self._vx < 0:
                    self.rect.left = tile.rect.right
            else:
                if self._vy > 0:
                    self.rect.bottom = tile.rect.top
                elif self._vy < 0:
                    self.rect.top = tile.rect.bottom

    def update(self, wall_tiles):
        self.handle_input()
        self.move(wall_tiles)
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
=======
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
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
