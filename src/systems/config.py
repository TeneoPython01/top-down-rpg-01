"""
src/systems/config.py - Persistent player-adjustable options (Feature #19).

Settings are stored in ``data/config.json`` and loaded once at game startup.
Any state that reads a setting should call ``get_config()`` (or access
``game.config``) rather than hard-coding constants, so that user choices are
respected at runtime.

Supported keys
--------------
music_volume   : float  0.0 – 1.0   BGM volume
sfx_volume     : float  0.0 – 1.0   SFX volume
battle_speed   : int    0 / 1 / 2   index into BATTLE_SPEED_VALUES
text_speed     : int    0 / 1 / 2   0=Slow, 1=Normal, 2=Fast
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from settings import (
    CONFIG_PATH,
    MUSIC_VOLUME,
    SFX_VOLUME,
)

# Default values used when the config file is absent or a key is missing.
_DEFAULTS: Dict[str, Any] = {
    "music_volume": MUSIC_VOLUME,
    "sfx_volume": SFX_VOLUME,
    "battle_speed": 0,   # 0 = Normal
    "text_speed": 1,     # 1 = Normal
}

# Characters-per-frame for each text-speed index (Slow / Normal / Fast)
TEXT_SPEED_VALUES = [1, 2, 4]
TEXT_SPEED_LABELS = ["Slow", "Normal", "Fast"]


def load_config() -> Dict[str, Any]:
    """Load config from disk, filling missing keys with defaults.

    Never raises — falls back to defaults silently on any read error.
    """
    cfg = dict(_DEFAULTS)
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, encoding="utf-8") as fh:
                data = json.load(fh)
            for key, default in _DEFAULTS.items():
                if key in data:
                    cfg[key] = type(default)(data[key])
        except (OSError, json.JSONDecodeError, ValueError):
            pass
    return cfg


def save_config(cfg: Dict[str, Any]) -> None:
    """Persist *cfg* to disk.  Silently ignores write errors."""
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w", encoding="utf-8") as fh:
            json.dump(cfg, fh, indent=2)
    except OSError:
        pass
