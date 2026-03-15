"""
Melodia — Lyrics Fetcher
Uses lrclib.net (free, no API key required).
Returns plain lyrics or time-synced LRC lines.
"""

import re
import urllib.request
import urllib.parse
import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class LrcLine:
    time: float   # seconds
    text: str


class LyricsResult:
    def __init__(self, plain: str = '', synced: list[LrcLine] = None):
        self.plain  = plain
        self.synced: list[LrcLine] = synced or []

    @property
    def has_synced(self) -> bool:
        return bool(self.synced)

    @property
    def has_lyrics(self) -> bool:
        return bool(self.plain or self.synced)

    def line_at(self, position: float) -> int:
        """Return index of the current synced line for a given position."""
        if not self.synced:
            return -1
        idx = 0
        for i, line in enumerate(self.synced):
            if line.time <= position:
                idx = i
            else:
                break
        return idx


def _parse_lrc(lrc: str) -> list[LrcLine]:
    pattern = re.compile(r'\[(\d+):(\d+)\.(\d+)\](.*)')
    lines = []
    for raw in lrc.splitlines():
        m = pattern.match(raw.strip())
        if m:
            mins  = int(m.group(1))
            secs  = int(m.group(2))
            cents = int(m.group(3))
            text  = m.group(4).strip()
            t = mins * 60 + secs + cents / 100.0
            lines.append(LrcLine(time=t, text=text))
    lines.sort(key=lambda l: l.time)
    return lines


def fetch(title: str, artist: str, album: str = '',
          duration: float = 0) -> Optional[LyricsResult]:
    """
    Fetch lyrics from lrclib.net.
    Returns LyricsResult or None if not found / network error.
    """
    params = {
        'track_name':  title,
        'artist_name': artist,
    }
    if album:
        params['album_name'] = album
    if duration > 0:
        params['duration'] = int(duration)

    url = 'https://lrclib.net/api/get?' + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Melodia/1.2 (Linux; +https://github.com/yourname/melodia)'},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status != 200:
                return None
            data = json.loads(resp.read().decode('utf-8'))
    except Exception:
        return None

    plain  = data.get('plainLyrics') or ''
    synced_raw = data.get('syncedLyrics') or ''
    synced = _parse_lrc(synced_raw) if synced_raw else []

    if not plain and not synced:
        return None

    return LyricsResult(plain=plain, synced=synced)
