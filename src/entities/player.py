"""
src/entities/player.py - Player entity with 4-directional movement and animation.

Art placeholder: the sprite is a colored rectangle until real walk-cycle
sprites are added in a later phase.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import pygame

from settings import (
    DATA_DIR,
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
from src.systems.inventory import Inventory

# Levels data loaded once at module level (lazily).
_LEVELS_DATA: List[Dict] | None = None


def _get_levels_data() -> List[Dict]:
    global _LEVELS_DATA
    if _LEVELS_DATA is None:
        path = os.path.join(DATA_DIR, "levels.json")
        with open(path) as f:
            _LEVELS_DATA = json.load(f)
    return _LEVELS_DATA


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
    name:
        Character name.
    level / exp:
        Current level and accumulated experience points.
    hp / max_hp:
        Current and maximum HP.
    mp / max_mp:
        Current and maximum MP.
    base_stats:
        Core stats before equipment bonuses (str, def, mag, mdf, spd, lck).
    stats:
        Effective stats after equipment bonuses.
    status:
        Active status effects: mapping effect_name → turns_remaining (int).
    buffs:
        Active combat buffs/debuffs: mapping stat_key → (multiplier, turns_remaining).
    inventory:
        The player's Inventory instance.
    known_spells:
        List of spell IDs the player has learned.
    gold:
        Convenience alias for inventory.gold.
    """

    def __init__(self, spawn_col: int, spawn_row: int) -> None:
        super().__init__()
        self.direction = DIR_DOWN
        self._moving = False

        # ── RPG stats ─────────────────────────────────────────────────────────
        self.name = "White Knight"
        self.level = 1
        self.exp = 0

        self.max_hp = 120
        self.hp = self.max_hp
        self.max_mp = 30
        self.mp = self.max_mp

        # Base stats (before equipment)
        self.base_stats: Dict[str, int] = {
            "str": 10,
            "def": 5,
            "mag": 6,
            "mdf": 4,
            "spd": 8,
            "lck": 5,
        }
        # Effective stats (recalculated when equipment changes)
        self.stats: Dict[str, int] = dict(self.base_stats)

        # Status effects: name → turns remaining
        self.status: Dict[str, int] = {}
        # Combat buffs/debuffs: stat → (multiplier, turns remaining)
        self.buffs: Dict[str, list] = {}

        # Cheat-mode flags (persistent across saves)
        self.cheat_unlocked: bool = False
        self.always_crit: bool = False

        # Zones the player has visited (used by the mini-map / world map)
        self.visited_zones: set = {"verdant_plains"}

        # Lore entries the player has collected (set of lore entry IDs)
        self.collected_lore: set = set()

        # Inventory and equipment
        self.inventory = Inventory()
        # Start with a couple of potions
        self.inventory.add("potion", 3)

        # Spells known at level 1
        self.known_spells: List[str] = ["cure", "scan"]

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
        self._margin = (TILE_SIZE - PLAYER_SIZE) // 2
        px = spawn_col * TILE_SIZE + self._margin
        py = spawn_row * TILE_SIZE + self._margin
        self.rect = self.image.get_rect(topleft=(px, py))
        self.pos = pygame.Vector2(self.rect.topleft)
        self.velocity = pygame.Vector2(0, 0)

        # Grid-based movement state
        self._tile_col: int = spawn_col
        self._tile_row: int = spawn_row
        self._target_col: int = spawn_col
        self._target_row: int = spawn_row
        self._grid_moving: bool = False

    # ── RPG stat helpers ──────────────────────────────────────────────────────

    @property
    def gold(self) -> int:
        return self.inventory.gold

    @gold.setter
    def gold(self, value: int) -> None:
        self.inventory.gold = value

    def recalculate_stats(self) -> None:
        """Recompute effective stats from base stats + equipped gear bonuses."""
        from src.systems.inventory import load_items
        all_items = load_items()

        self.stats = dict(self.base_stats)
        for slot, item_id in self.inventory.equipment.items():
            if item_id is None:
                continue
            item_data = all_items.get(item_id)
            if item_data is None:
                continue
            for key in ("str", "def", "mag", "mdf", "spd", "lck"):
                self.stats[key] = self.stats.get(key, 0) + item_data.get(key, 0)

    def is_alive(self) -> bool:
        return self.hp > 0

    # ── Serialization ─────────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the player to a JSON-compatible dict for saving."""
        return {
            "name": self.name,
            "level": self.level,
            "exp": self.exp,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "mp": self.mp,
            "max_mp": self.max_mp,
            "base_stats": dict(self.base_stats),
            "status": dict(self.status),
            "buffs": {k: list(v) for k, v in self.buffs.items()},
            "known_spells": list(self.known_spells),
            "gold": self.inventory.gold,
            "inventory_items": dict(self.inventory.items),
            "equipment": {k: v for k, v in self.inventory.equipment.items()},
            "pos_x": float(self.pos.x),
            "pos_y": float(self.pos.y),
            "direction": self.direction,
            "cheat_unlocked": self.cheat_unlocked,
            "always_crit": self.always_crit,
            "visited_zones": list(self.visited_zones),
            "collected_lore": list(self.collected_lore),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Restore a ``Player`` from a save-data dict produced by :meth:`to_dict`."""
        pos_x = float(data.get("pos_x", 0.0))
        pos_y = float(data.get("pos_y", 0.0))
        spawn_col = max(0, int(pos_x / TILE_SIZE))
        spawn_row = max(0, int(pos_y / TILE_SIZE))

        player = cls(spawn_col, spawn_row)
        player.name = data.get("name", "White Knight")
        player.level = data.get("level", 1)
        player.exp = data.get("exp", 0)
        player.max_hp = data.get("max_hp", 120)
        player.hp = min(data.get("hp", player.max_hp), player.max_hp)
        player.max_mp = data.get("max_mp", 30)
        player.mp = min(data.get("mp", player.max_mp), player.max_mp)
        player.base_stats = dict(data.get("base_stats", player.base_stats))
        player.status = dict(data.get("status", {}))
        player.buffs = {k: list(v) for k, v in data.get("buffs", {}).items()}
        player.known_spells = list(data.get("known_spells", ["cure", "scan"]))

        # Restore inventory
        player.inventory = Inventory()
        player.inventory.gold = data.get("gold", 0)
        for item_id, count in data.get("inventory_items", {}).items():
            player.inventory.add(item_id, int(count))
        for slot, item_id in data.get("equipment", {}).items():
            if slot in Inventory.SLOTS:
                player.inventory.equipment[slot] = item_id

        player.recalculate_stats()

        # Restore grid-aligned position (grid movement requires tile alignment).
        player.pos = pygame.Vector2(
            spawn_col * TILE_SIZE + player._margin,
            spawn_row * TILE_SIZE + player._margin,
        )
        player.rect.topleft = (round(player.pos.x), round(player.pos.y))
        player._tile_col = spawn_col
        player._tile_row = spawn_row
        player._target_col = spawn_col
        player._target_row = spawn_row
        player.direction = data.get("direction", DIR_DOWN)
        player.cheat_unlocked = bool(data.get("cheat_unlocked", False))
        player.always_crit = bool(data.get("always_crit", False))
        player.visited_zones = set(data.get("visited_zones", ["verdant_plains"]))
        player.collected_lore = set(data.get("collected_lore", []))

        return player

    def take_damage(self, amount: int) -> int:
        """Apply damage and return actual HP lost."""
        actual = min(amount, self.hp)
        self.hp -= actual
        return actual

    def heal(self, amount: int) -> int:
        """Restore HP up to max_hp; return actual amount healed."""
        before = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - before

    def restore_mp(self, amount: int) -> int:
        """Restore MP up to max_mp; return actual amount restored."""
        before = self.mp
        self.mp = min(self.max_mp, self.mp + amount)
        return self.mp - before

    def gain_exp(self, amount: int, levels_data: List[Dict]) -> List[str]:
        """Add exp, level up if threshold met; return list of level-up messages.

        levels_data entries have keys: level, xp_required, hp, mp, str, def,
        mag, mdf, spd, lck (absolute values for that level).
        """
        messages: List[str] = []
        self.exp += amount
        from src.systems.magic import load_spells
        all_spells = load_spells()

        for entry in sorted(levels_data, key=lambda e: e["level"]):
            lv = entry["level"]
            if lv <= self.level:
                continue
            if self.exp >= entry.get("xp_required", 9_999_999):
                old_max_hp = self.max_hp
                old_max_mp = self.max_mp

                self.level = lv
                # Set stats to absolute values from the levels table
                for k in ("str", "def", "mag", "mdf", "spd", "lck"):
                    if k in entry:
                        self.base_stats[k] = entry[k]
                self.max_hp = entry.get("hp", self.max_hp)
                self.max_mp = entry.get("mp", self.max_mp)
                hp_gain = self.max_hp - old_max_hp
                mp_gain = self.max_mp - old_max_mp
                self.hp = self.max_hp
                self.mp = self.max_mp
                self.recalculate_stats()
                messages.append(
                    f"Level up! Now Lv {self.level}. "
                    f"HP+{hp_gain} MP+{mp_gain}"
                )
                # Learn new spells at this level
                for sid, sdata in all_spells.items():
                    if sdata.get("learn_level", 99) == lv and sid not in self.known_spells:
                        self.known_spells.append(sid)
                        messages.append(f"Learned {sdata['name']}!")
        return messages

    # ── Private helpers ───────────────────────────────────────────────────────

    def _handle_input(self) -> tuple:
        """Read keyboard state, update facing direction, return (dx, dy) for next step."""
        keys = pygame.key.get_pressed()
        dx = dy = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
            self.direction = DIR_LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
            self.direction = DIR_RIGHT
        elif keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
            self.direction = DIR_UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
            self.direction = DIR_DOWN

        return dx, dy

    def _is_tile_blocked(
        self, col: int, row: int, blocked_rects: List[pygame.Rect]
    ) -> bool:
        """Return True if the tile at (col, row) overlaps any blocked rect."""
        target_rect = pygame.Rect(
            col * TILE_SIZE + self._margin,
            row * TILE_SIZE + self._margin,
            PLAYER_SIZE,
            PLAYER_SIZE,
        )
        return any(target_rect.colliderect(wall) for wall in blocked_rects)

    def _try_start_step(
        self, dx: int, dy: int, blocked_rects: List[pygame.Rect]
    ) -> None:
        """Begin a one-tile step in direction (dx, dy) if the target tile is free."""
        if dx == 0 and dy == 0:
            return
        next_col = self._tile_col + dx
        next_row = self._tile_row + dy
        if not self._is_tile_blocked(next_col, next_row, blocked_rects):
            self._target_col = next_col
            self._target_row = next_row
            self._grid_moving = True

    # ── Public API ────────────────────────────────────────────────────────────

    def gain_xp(self, amount: int) -> List[str]:
        """Add *amount* XP and process any level-ups.

        Returns a list of level-up message strings (one per level gained).
        """
        self.exp += amount
        messages: List[str] = []
        levels = _get_levels_data()
        while self.level < len(levels):
            # levels is 0-indexed: level 1 data is at index 0, level 2 at index 1, …
            # To check if the player should advance to level N+1, read index N.
            next_data = levels[self.level]
            if self.exp >= next_data["xp_required"]:
                self.level = next_data["level"]
                self.max_hp = next_data["hp"]
                self.max_mp = next_data["mp"]
                # Full restore on level up
                self.hp = self.max_hp
                self.mp = self.max_mp
                for stat in ("str", "def", "mag", "mdf", "spd", "lck"):
                    self.base_stats[stat] = next_data[stat]
                self.recalculate_stats()
                messages.append(f"Level up!  Lv {self.level}!")
            else:
                break
        return messages

    def update(self, dt: float, blocked_rects: List[pygame.Rect]) -> None:
        """Update position and animation for this frame (grid-based movement)."""
        dx, dy = self._handle_input()

        if self._grid_moving:
            # Advance toward the target tile.
            target_x = float(self._target_col * TILE_SIZE + self._margin)
            target_y = float(self._target_row * TILE_SIZE + self._margin)
            diff_x = target_x - self.pos.x
            diff_y = target_y - self.pos.y
            dist_sq = diff_x ** 2 + diff_y ** 2
            step = PLAYER_SPEED * dt

            if dist_sq <= step ** 2:
                # Arrived — snap exactly to the target tile.
                self.pos.x = target_x
                self.pos.y = target_y
                self._tile_col = self._target_col
                self._tile_row = self._target_row
                self._grid_moving = False
                # Immediately continue if a direction key is still held.
                self._try_start_step(dx, dy, blocked_rects)
            else:
                dist = dist_sq ** 0.5
                if dist > 0:
                    self.pos.x += (diff_x / dist) * step
                    self.pos.y += (diff_y / dist) * step

            self.rect.x = round(self.pos.x)
            self.rect.y = round(self.pos.y)
        else:
            self._try_start_step(dx, dy, blocked_rects)

        # Keep velocity in sync for any external code that reads it.
        self.velocity = (
            pygame.Vector2(
                self._target_col - self._tile_col,
                self._target_row - self._tile_row,
            ) * PLAYER_SPEED
            if self._grid_moving
            else pygame.Vector2(0, 0)
        )

        self._moving = self._grid_moving

        # Animate
        anim = self._animations[self.direction]
        if self._moving:
            anim.update(dt)
            self.image = anim.current_frame
        else:
            anim.reset()
            self.image = self._idle[self.direction]
