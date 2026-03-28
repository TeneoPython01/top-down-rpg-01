# Game settings / constants

# Display
TITLE = "Top-Down RPG"
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Tile settings
TILE_SIZE = 32

# Colors (R, G, B)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
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
}
