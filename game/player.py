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

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity.x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity.x = PLAYER_SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity.y = -PLAYER_SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity.y = PLAYER_SPEED

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
