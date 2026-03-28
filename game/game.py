import os
import sys
import pygame
from game.settings import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BLACK
from game.tilemap import TileMap
from game.player import Player
from game.camera import Camera

MAPS_DIR = os.path.join(os.path.dirname(__file__), "maps")


class Game:
    """Main game class: initialises Pygame, owns the game loop."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self._load_map("map_01.txt")

    def _load_map(self, filename):
        path = os.path.join(MAPS_DIR, filename)
        self.tilemap = TileMap(path)
        self.camera = Camera(self.tilemap.pixel_width, self.tilemap.pixel_height)
        self.player = Player(2, 2)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

    def run(self):
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()
        pygame.quit()
        sys.exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def _update(self):
        self.player.update(self.tilemap.wall_tiles)
        self.camera.update(self.player.rect)

    def _draw(self):
        self.screen.fill(BLACK)
        self.tilemap.draw(self.screen, self.camera)
        for sprite in self.all_sprites:
            self.screen.blit(sprite.image, self.camera.apply(sprite.rect))
        pygame.display.flip()
