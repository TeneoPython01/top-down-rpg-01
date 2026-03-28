"""
game/settings.py - Game constants and configuration.
"""

# Display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Top-Down RPG"

# Tiles
TILE_SIZE = 32

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (180, 180, 180)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (101, 67, 33)
BLUE = (70, 130, 180)

# Player
PLAYER_SPEED = 150  # pixels per second
PLAYER_COLOR = BLUE
PLAYER_SIZE = TILE_SIZE - 4  # slightly smaller than a tile

# Map tile codes
TILE_WALL = "W"
TILE_FLOOR = "."
TILE_PLAYER_SPAWN = "P"
