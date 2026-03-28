import pygame
from game.settings import TILE_SIZE, PLAYER_SPEED, WHITE


class Player(pygame.sprite.Sprite):
    """Player character controlled by the keyboard."""

    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE - 4, TILE_SIZE - 4))
        self.image.fill(WHITE)
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
