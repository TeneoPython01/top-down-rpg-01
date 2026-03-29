"""
src/systems/audio.py - AudioManager: background music and sound effects.

Usage
-----
    game.audio.play_music("title")      # start looping BGM
    game.audio.play_sfx("cursor")       # one-shot sound effect
    game.audio.stop_music()             # fade out current BGM

Music tracks are streamed via pygame.mixer.music (supports WAV/OGG/MP3).
SFX are pre-loaded as pygame.mixer.Sound objects.

If an audio file is missing the call is silently skipped so the game runs
without audio when assets are absent.
"""

from __future__ import annotations

import os
from typing import Dict, Optional

import pygame

from settings import MUSIC_DIR, SFX_DIR, MUSIC_VOLUME, SFX_VOLUME, MUSIC_FADE_MS

# ── Track / SFX manifests ─────────────────────────────────────────────────────

# BGM track-name → filename (searched in MUSIC_DIR; .wav tried first, then .ogg)
MUSIC_TRACKS: Dict[str, str] = {
    "title":       "title",
    "overworld":   "overworld",
    "town":        "town",
    "battle":      "battle",
    "boss_battle": "boss_battle",
    "cutscene":    "cutscene",
    "victory":     "victory",
    "game_over":   "game_over",
}

# SFX name → filename (searched in SFX_DIR)
SFX_FILES: Dict[str, str] = {
    "cursor":       "cursor.wav",
    "confirm":      "confirm.wav",
    "cancel":       "cancel.wav",
    "attack_hit":   "attack_hit.wav",
    "spell_cast":   "spell_cast.wav",
    "item_use":     "item_use.wav",
    "level_up":     "level_up.wav",
    "door_open":    "door_open.wav",
    "dialog_open":  "dialog_open.wav",
    "dialog_close": "dialog_close.wav",
}

_MUSIC_EXTS = (".wav", ".ogg", ".mp3")


class AudioManager:
    """Centralised audio controller for BGM and SFX.

    Instantiated once by ``Game.__init__`` and stored as ``game.audio``.
    All public methods fail silently when audio is unavailable so the rest
    of the game never needs to guard against missing audio.
    """

    def __init__(self) -> None:
        self._enabled = False
        self._current_track: Optional[str] = None
        self._sfx: Dict[str, pygame.mixer.Sound] = {}

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._enabled = True
        except pygame.error:
            return  # audio not available on this platform

        pygame.mixer.music.set_volume(MUSIC_VOLUME)
        self._load_sfx()

    # ── SFX pre-loading ───────────────────────────────────────────────────────

    def _load_sfx(self) -> None:
        for name, filename in SFX_FILES.items():
            path = os.path.join(SFX_DIR, filename)
            if not os.path.exists(path):
                continue
            try:
                snd = pygame.mixer.Sound(path)
                snd.set_volume(SFX_VOLUME)
                self._sfx[name] = snd
            except pygame.error:
                pass

    # ── BGM control ───────────────────────────────────────────────────────────

    def play_music(self, track: str, loops: int = -1) -> None:
        """Start a BGM track, looping by default (loops=-1).

        If *track* is already playing it is not restarted.
        ``loops=0`` plays the track exactly once (used for victory fanfare).
        """
        if not self._enabled:
            return
        if track == self._current_track and pygame.mixer.music.get_busy():
            return

        stem = MUSIC_TRACKS.get(track)
        if stem is None:
            return

        for ext in _MUSIC_EXTS:
            path = os.path.join(MUSIC_DIR, stem + ext)
            if os.path.exists(path):
                try:
                    pygame.mixer.music.fadeout(MUSIC_FADE_MS)
                    pygame.mixer.music.load(path)
                    pygame.mixer.music.set_volume(MUSIC_VOLUME)
                    pygame.mixer.music.play(loops=loops, fade_ms=MUSIC_FADE_MS)
                    self._current_track = track
                    return
                except pygame.error:
                    pass

    def stop_music(self) -> None:
        """Fade out and stop the current BGM track."""
        if self._enabled and pygame.mixer.music.get_busy():
            pygame.mixer.music.fadeout(MUSIC_FADE_MS)
        self._current_track = None

    # ── SFX playback ──────────────────────────────────────────────────────────

    def play_sfx(self, name: str) -> None:
        """Play a one-shot sound effect by name.  Silently ignored if missing."""
        if not self._enabled:
            return
        snd = self._sfx.get(name)
        if snd is not None:
            snd.play()

    # ── Volume helpers ────────────────────────────────────────────────────────

    def set_music_volume(self, volume: float) -> None:
        """Set BGM volume in the range [0.0, 1.0]."""
        if self._enabled:
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))

    def set_sfx_volume(self, volume: float) -> None:
        """Set SFX volume for all loaded sounds in the range [0.0, 1.0]."""
        v = max(0.0, min(1.0, volume))
        for snd in self._sfx.values():
            snd.set_volume(v)
