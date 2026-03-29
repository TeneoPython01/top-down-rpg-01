"""
src/states/intro.py - Scripted intro cutscene (backstory).

The intro unfolds in two phases:
  Phase 1 — Narration panels on a black background, each auto-advancing after a
             short timer (or immediately when Z / ENTER / SPACE is pressed).
  Phase 2 — The overworld tilemap is revealed; predefined character movement and
             dialog play out in sequence.

Press BACKSLASH at any time to skip the entire intro and jump straight to the
overworld.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

import pygame

from settings import (
    BLACK,
    BLUE,
    FONT_NAME,
    FONT_SIZE_NORMAL,
    FONT_SIZE_SMALL,
    INTRO_ELDER_COLOR,
    INTRO_FADE_SPEED,
    INTRO_HINT_COLOR,
    INTRO_MOVE_SPEED,
    INTRO_OVERLAY_ALPHA,
    INTRO_SPRITE_FOOT_COLOR,
    NATIVE_HEIGHT,
    NATIVE_WIDTH,
    TILE_SIZE,
    WHITE,
    YELLOW,
)
from src.states.base_state import BaseState
from src.systems.camera import Camera
from src.ui.text_box import TextBox
from src.utils.tilemap import TileMap

if TYPE_CHECKING:
    from src.game import Game


# ── Scripted character sprite ──────────────────────────────────────────────────


class _IntroSprite:
    """Minimal sprite used during the intro cutscene.

    Renders as a simple coloured humanoid placeholder and can autonomously
    walk to a target tile position.
    """

    def __init__(self, col: int, row: int, color: tuple) -> None:
        size = TILE_SIZE
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(self.image, color, (3, 4, 10, 10))
        # Head (white)
        pygame.draw.rect(self.image, WHITE, (4, 0, 8, 6))
        # Feet (dark)
        pygame.draw.rect(self.image, INTRO_SPRITE_FOOT_COLOR, (4, 13, 3, 2))
        pygame.draw.rect(self.image, INTRO_SPRITE_FOOT_COLOR, (9, 13, 3, 2))

        self.pos = pygame.Vector2(col * TILE_SIZE, row * TILE_SIZE)
        self.rect = pygame.Rect(int(self.pos.x), int(self.pos.y), size, size)
        self._target: pygame.Vector2 | None = None

    # ── Public API ────────────────────────────────────────────────────────────

    def move_to_tile(self, col: int, row: int) -> None:
        """Set a destination tile; the sprite will walk there in ``update``."""
        self._target = pygame.Vector2(col * TILE_SIZE, row * TILE_SIZE)

    @property
    def at_target(self) -> bool:
        """True when the sprite has reached (or has no) destination."""
        if self._target is None:
            return True
        return self.pos.distance_to(self._target) < 1.5

    def update(self, dt: float) -> None:
        if self._target is None:
            return
        if self.at_target:
            self._target = None
            return
        direction = self._target - self.pos
        if direction.length() > 0:
            direction = direction.normalize()
        self.pos += direction * INTRO_MOVE_SPEED * dt
        self.rect.x = round(self.pos.x)
        self.rect.y = round(self.pos.y)


# ── Intro script ───────────────────────────────────────────────────────────────
# Each entry is a dict with a mandatory "type" key:
#
#   narration   — black background, centred white text; auto-advances after
#                 "wait" seconds (or on Z / ENTER / SPACE).
#                 Keys: "lines" (list[str]), "wait" (float, default 3.0)
#
#   show_scene  — fade the tilemap in over ~1.5 s, then advance.
#
#   move_player — walk the player sprite to ("col", "row"); auto-advances on arrival.
#
#   move_npc    — walk NPC at index "npc_idx" to ("col", "row"); auto-advances on arrival.
#
#   dialog      — display a TextBox with optional "speaker" and "text";
#                 Z / ENTER / SPACE advances (or finishes) the box.
#
#   done        — end the intro and push the overworld.

_INTRO_SCRIPT: List[Dict[str, Any]] = [
    # ── Narration prologue ─────────────────────────────────────────────────────
    {
        "type": "narration",
        "lines": [
            "100 years ago, a devastating pandemic",
            "swept across the entire world...",
        ],
        "wait": 3.5,
    },
    {
        "type": "narration",
        "lines": [
            "Most of humanity fell silent.",
            "Magic faded with the people.",
        ],
        "wait": 3.5,
    },
    {
        "type": "narration",
        "lines": [
            "The survivors scraped together",
            "what remained and rebuilt.",
        ],
        "wait": 3.5,
    },
    {
        "type": "narration",
        "lines": [
            "Now, a century later, the shadows",
            "are beginning to stir once more...",
        ],
        "wait": 3.5,
    },
    # ── Reveal the scene ──────────────────────────────────────────────────────
    {"type": "show_scene"},
    # Elder walks to the player
    {"type": "move_npc", "npc_idx": 0, "col": 5, "row": 9},
    # Dialog exchange
    {
        "type": "dialog",
        "speaker": "Village Elder",
        "text": "White Knight! Strange beast attacks have\nbeen increasing near the village.",
    },
    {
        "type": "dialog",
        "speaker": "Village Elder",
        "text": "The creatures seem almost... driven.\nAs if something is pushing them toward us.",
    },
    {
        "type": "dialog",
        "speaker": "Village Elder",
        "text": "I fear a dark force is awakening —\none not seen in over a century.",
    },
    {
        "type": "dialog",
        "speaker": "White Knight",
        "text": "I will look into it.\nAshenvale will not fall on my watch.",
    },
    {
        "type": "dialog",
        "speaker": "Village Elder",
        "text": "Investigate Silverwood Forest to the north.\nPlease — be careful.",
    },
    # Player walks north toward the forest path
    {"type": "move_player", "col": 4, "row": 2},
    # ── Closing narration over the scene ──────────────────────────────────────
    {
        "type": "narration",
        "lines": ["Your journey begins..."],
        "wait": 2.5,
        "overlay": True,   # draw on top of the visible scene
        "color": YELLOW,
    },
    {"type": "done"},
]


# ── IntroState ────────────────────────────────────────────────────────────────


class IntroState(BaseState):
    """Scripted intro cutscene state.

    Pressing BACKSLASH at any time skips the entire intro and transitions
    directly to the overworld.  Z / ENTER / SPACE advances dialog boxes and
    can also skip individual narration panels early.
    """

    def __init__(self, game: "Game") -> None:
        super().__init__(game)
        self._tilemap = TileMap()
        self._camera = Camera(
            self._tilemap.pixel_width,
            self._tilemap.pixel_height,
        )

        # Player sprite (White Knight) — starts at spawn tile
        spawn_col, spawn_row = self._tilemap.spawn
        self._player = _IntroSprite(spawn_col, spawn_row, BLUE)

        # NPC sprites used in the scene
        # NPC 0 — Village Elder: warm brownish, starts near the path area
        self._npcs: List[_IntroSprite] = [
            _IntroSprite(10, 5, INTRO_ELDER_COLOR),
        ]

        # Script position
        self._step_idx = 0

        # Narration-phase state
        self._narration_lines: List[str] = []
        self._narration_color: tuple = WHITE
        self._narration_wait = 0.0
        self._narration_timer = 0.0
        self._narration_overlay = False   # draw narration over the scene?

        # Dialog state
        self._text_box: TextBox | None = None

        # Scene visibility
        self._scene_visible = False

        # Fade overlay (used for show_scene transition)
        self._fade_surface = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT))
        self._fade_surface.fill(BLACK)
        self._fade_alpha = 0
        self._fading_in = False   # True while fading black→scene

    # ── State lifecycle ───────────────────────────────────────────────────────

    def enter(self) -> None:
        self._step_idx = 0
        self._scene_visible = False
        self._fade_alpha = 0
        self._fading_in = False
        self._text_box = None
        self._narration_lines = []
        self.game.audio.play_music("cutscene")
        self._start_step()

    # ── Step management ───────────────────────────────────────────────────────

    def _start_step(self) -> None:
        """Initialise whatever the current script step requires."""
        if self._step_idx >= len(_INTRO_SCRIPT):
            self._finish()
            return

        step = _INTRO_SCRIPT[self._step_idx]
        t = step["type"]

        if t == "narration":
            self._narration_lines = step["lines"]
            self._narration_wait = step.get("wait", 3.0)
            self._narration_timer = 0.0
            self._narration_color = step.get("color", WHITE)
            self._narration_overlay = step.get("overlay", False)
            self._text_box = None

        elif t == "show_scene":
            self._scene_visible = True
            self._fade_alpha = 255
            self._fading_in = True
            # Advancement happens once the fade completes (in update).

        elif t == "move_player":
            self._player.move_to_tile(step["col"], step["row"])

        elif t == "move_npc":
            self._npcs[step["npc_idx"]].move_to_tile(step["col"], step["row"])

        elif t == "dialog":
            speaker = step.get("speaker", "")
            body = step.get("text", "")
            full_text = f"{speaker}\n{body}" if speaker else body
            self._text_box = TextBox(full_text)

        elif t == "done":
            self._finish()

    def _advance_step(self) -> None:
        self._step_idx += 1
        self._start_step()

    def _finish(self) -> None:
        """Exit to the overworld."""
        from src.states.overworld import OverworldState

        self.game.change_state(OverworldState(self.game))

    # ── Input ─────────────────────────────────────────────────────────────────

    def handle_input(self, event: pygame.event.Event) -> None:
        if event.type != pygame.KEYDOWN:
            return

        # Backslash always skips the whole intro.
        if event.key == pygame.K_BACKSLASH:
            self._finish()
            return

        if event.key not in (pygame.K_RETURN, pygame.K_z, pygame.K_SPACE):
            return

        if self._step_idx >= len(_INTRO_SCRIPT):
            return

        step = _INTRO_SCRIPT[self._step_idx]
        t = step["type"]

        if t == "narration":
            # Skip the current narration early.
            self._advance_step()
        elif t == "dialog":
            if self._text_box and not self._text_box.done:
                self._text_box.advance()
            else:
                self._advance_step()

    # ── Update ────────────────────────────────────────────────────────────────

    def update(self, dt: float) -> None:
        if self._step_idx >= len(_INTRO_SCRIPT):
            return

        # Update all sprites (they move toward their targets).
        self._player.update(dt)
        for npc in self._npcs:
            npc.update(dt)

        # Update text box typewriter.
        if self._text_box:
            self._text_box.update(dt)

        # Update camera to follow player when scene is visible.
        if self._scene_visible:
            self._camera.update(self._player)

        # Handle fade-in for show_scene.
        if self._fading_in:
            self._fade_alpha = max(0, self._fade_alpha - INTRO_FADE_SPEED * dt)
            if self._fade_alpha == 0:
                self._fading_in = False
                self._advance_step()
            return  # Don't process the next step while fading.

        step = _INTRO_SCRIPT[self._step_idx]
        t = step["type"]

        if t == "narration":
            self._narration_timer += dt
            if self._narration_timer >= self._narration_wait:
                self._advance_step()

        elif t == "move_player":
            if self._player.at_target:
                self._advance_step()

        elif t == "move_npc":
            npc = self._npcs[step["npc_idx"]]
            if npc.at_target:
                self._advance_step()

        elif t == "done":
            self._finish()

    # ── Draw ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(BLACK)

        if self._scene_visible:
            self._draw_scene(surface)
        else:
            self._draw_narration(surface)

        # Fade overlay (black wash used during show_scene transition).
        if self._fade_alpha > 0:
            self._fade_surface.set_alpha(int(self._fade_alpha))
            surface.blit(self._fade_surface, (0, 0))

        self._draw_skip_hint(surface)

    # ── Private draw helpers ──────────────────────────────────────────────────

    def _draw_scene(self, surface: pygame.Surface) -> None:
        """Draw the tilemap, sprites, and any active dialog."""
        self._tilemap.draw(surface, self._camera.offset)

        for npc in self._npcs:
            surface.blit(npc.image, npc.rect.move(self._camera.offset))
        surface.blit(self._player.image, self._player.rect.move(self._camera.offset))

        # Check if the current step is a post-scene narration overlay.
        if (
            self._step_idx < len(_INTRO_SCRIPT)
            and _INTRO_SCRIPT[self._step_idx]["type"] == "narration"
            and _INTRO_SCRIPT[self._step_idx].get("overlay", False)
        ):
            overlay = pygame.Surface((NATIVE_WIDTH, NATIVE_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, INTRO_OVERLAY_ALPHA))
            surface.blit(overlay, (0, 0))
            self._draw_narration_text(surface)
        elif self._text_box:
            self._text_box.draw(surface)

    def _draw_narration(self, surface: pygame.Surface) -> None:
        """Draw a centred narration panel on the black background."""
        self._draw_narration_text(surface)

    def _draw_narration_text(self, surface: pygame.Surface) -> None:
        """Render the current narration lines centred on *surface*.

        Uses FONT_SIZE_NORMAL (8 native px → 24 px at 3× scale) to ensure
        even long lines fit within the 256 px native width.
        """
        if not self._narration_lines:
            return
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_NORMAL)
        line_h = 12
        total_h = len(self._narration_lines) * line_h
        cy = NATIVE_HEIGHT // 2 - total_h // 2
        for line in self._narration_lines:
            surf = font.render(line, True, self._narration_color)
            surface.blit(surf, surf.get_rect(centerx=NATIVE_WIDTH // 2, centery=cy))
            cy += line_h

    def _draw_skip_hint(self, surface: pygame.Surface) -> None:
        font = pygame.font.SysFont(FONT_NAME, FONT_SIZE_SMALL)
        hint = font.render("[\\] Skip intro", True, INTRO_HINT_COLOR)
        surface.blit(hint, hint.get_rect(right=NATIVE_WIDTH - 4, bottom=NATIVE_HEIGHT - 4))
