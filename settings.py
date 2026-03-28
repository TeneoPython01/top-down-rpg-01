"""
settings.py - Global constants and configuration.
"""

import os

# ── Display ──────────────────────────────────────────────────────────────────
NATIVE_WIDTH = 256
NATIVE_HEIGHT = 224
SCALE = 3
SCREEN_WIDTH = NATIVE_WIDTH * SCALE    # 768
SCREEN_HEIGHT = NATIVE_HEIGHT * SCALE  # 672
FPS = 60
TITLE = "Top-Down RPG — Post-Pandemic Fantasy"

# ── Tile grid ─────────────────────────────────────────────────────────────────
TILE_SIZE = 16  # pixels at native resolution

# Tile IDs
TILE_GRASS = 0
TILE_WALL = 1
TILE_WATER = 2
TILE_PATH = 3

# ── Player ────────────────────────────────────────────────────────────────────
PLAYER_SPEED = 80        # pixels per second (native resolution)
PLAYER_SIZE = 16         # sprite size at native resolution
PLAYER_ANIM_FPS = 6.0    # animation playback speed in frames per second

# ── Player direction indices (also used as spritesheet row indices) ────────────
DIR_DOWN = 0
DIR_LEFT = 1
DIR_RIGHT = 2
DIR_UP = 3

# ── Colors (R, G, B) ──────────────────────────────────────────────────────────
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GRAY = (40, 40, 40)
LIGHT_GRAY = (170, 170, 170)
GREEN = (34, 139, 34)
DARK_GREEN = (0, 80, 0)
BROWN = (101, 67, 33)
BLUE = (70, 130, 180)
YELLOW = (255, 215, 0)
RED = (200, 40, 40)
CYAN = (0, 200, 200)
DARK_BLUE = (20, 40, 100)
DARK_BROWN = (60, 40, 20)
WATER_BLUE = (30, 100, 180)
PATH_TAN = (180, 155, 100)

# Tile colours (used until real tilesets are added)
TILE_COLORS = {
    TILE_GRASS: (60, 120, 40),
    TILE_WALL: (80, 60, 50),
    TILE_WATER: (30, 100, 180),
    TILE_PATH: (160, 140, 90),
}

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MAPS_DIR = os.path.join(ASSETS_DIR, "maps")

# ── Battle ────────────────────────────────────────────────────────────────────
BASE_HIT_RATE = 0.90
CRIT_CHANCE_DIVISOR = 256
DAMAGE_VARIANCE = 0.10
BLIND_HIT_PENALTY = 0.50       # hit-rate reduction when attacker is blinded
UNARMED_ATTACK_POWER = 3       # default weapon power when no weapon is equipped

# ── Encounters ────────────────────────────────────────────────────────────────
ENCOUNTER_RATE_VARIANCE = 0.50  # ±50% of encounter_rate for threshold rolling

# ── UI ────────────────────────────────────────────────────────────────────────
DIALOG_BOX_HEIGHT = 56      # native pixels
DIALOG_PADDING = 6
TYPEWRITER_SPEED = 2        # characters per frame

# Font settings
FONT_NAME = "monospace"
FONT_SIZE_LARGE = 14
FONT_SIZE_NORMAL = 8
FONT_SIZE_SMALL = 7

# UI colours
MENU_CURSOR_BG = (60, 60, 80)
TILE_GRID_COLOR = (0, 0, 0, 40)

# Title screen
TITLE_STAR_SEED = 42    # fixed seed for deterministic star field on title screen
TITLE_STAR_COUNT = 40
