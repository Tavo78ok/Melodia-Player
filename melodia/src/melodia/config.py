"""
Melodia — Persistent Configuration
Stores settings in ~/.config/melodia/config.json
"""

import json
import os
from pathlib import Path

CONFIG_DIR  = Path.home() / '.config' / 'melodia'
CONFIG_FILE = CONFIG_DIR / 'config.json'

DEFAULTS = {
    'music_folder': str(Path.home() / 'Music'),
    'volume': 0.8,
    'shuffle': False,
    'repeat': False,
    'accent_color': '#E8725A',
    'show_lyrics': False,
    'last_track_index': -1,
}


def load() -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        save(DEFAULTS.copy())
        return DEFAULTS.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Fill in any missing keys from DEFAULTS
        for k, v in DEFAULTS.items():
            data.setdefault(k, v)
        return data
    except Exception:
        return DEFAULTS.copy()


def save(cfg: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
