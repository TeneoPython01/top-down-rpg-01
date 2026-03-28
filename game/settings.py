<<<<<<< HEAD
<<<<<<< HEAD
# Game settings / constants

# Display
TITLE = "Top-Down RPG"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Tile settings
=======
"""
game/settings.py - Game constants and configuration.
"""

# Display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Top-Down RPG"

# Tiles
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
TILE_SIZE = 32

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
<<<<<<< HEAD
RED = (220, 50, 50)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BLUE = (30, 144, 255)
BROWN = (101, 67, 33)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
YELLOW = (255, 220, 0)

# Player settings
PLAYER_SPEED = 3
PLAYER_SIZE = 24  # sprite width/height in pixels

# Tile IDs
TILE_EMPTY = -1
TILE_GRASS = 0
TILE_WALL = 1
TILE_WATER = 2
TILE_PATH = 3

# Tile properties: maps tile ID -> (color, walkable)
TILE_PROPERTIES = {
    TILE_GRASS: (GREEN,      True),
    TILE_WALL:  (GRAY,       False),
    TILE_WATER: (BLUE,       False),
    TILE_PATH:  (BROWN,      True),
=======
# Screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Top-Down RPG"
FPS = 60

# Tiles
TILE_SIZE = 32

# Player
PLAYER_SPEED = 4

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
BLUE = (70, 130, 180)

# Tile types
TILE_GRASS = "."
TILE_WALL = "#"
TILE_WATER = "~"

# Tile colors
TILE_COLORS = {
    TILE_GRASS: GREEN,
    TILE_WALL: DARK_GRAY,
    TILE_WATER: BLUE,
>>>>>>> 1a56f8a7b0d6d654abe6ca6160113bb2029dbade
}
=======
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
>>>>>>> b7662c8ece33af2e7f642e242f5b74f5ad2a04df
