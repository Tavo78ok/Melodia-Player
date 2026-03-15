"""
Melodia — Music Library Scanner
Scans directories, reads metadata via mutagen, caches album art.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import mutagen
    from mutagen import File as MutagenFile
    HAS_MUTAGEN = True
except ImportError:
    HAS_MUTAGEN = False

SUPPORTED_FORMATS = (
    '.mp3', '.flac', '.ogg', '.m4a', '.aac',
    '.wav', '.opus', '.wma', '.ape', '.mp4',
)


@dataclass
class Track:
    path: str
    title: str = ''
    artist: str = ''
    album: str = ''
    track_number: int = 0
    duration: float = 0.0
    year: str = ''
    genre: str = ''
    has_cover: bool = False

    @property
    def display_title(self) -> str:
        return self.title or Path(self.path).stem

    @property
    def display_artist(self) -> str:
        return self.artist or 'Unknown Artist'

    @property
    def display_album(self) -> str:
        return self.album or 'Unknown Album'

    def duration_str(self) -> str:
        total = int(self.duration)
        mins, secs = divmod(total, 60)
        return f'{mins}:{secs:02d}'

    def placeholder_key(self) -> str:
        return self.display_title


class MusicLibrary:
    def __init__(self):
        self.tracks: list[Track] = []
        self._cover_cache: dict[str, Optional[bytes]] = {}

    # ──────────────────────────────────────────────
    # Scanning
    # ──────────────────────────────────────────────

    def scan_directory(self, directory: str, progress_cb=None) -> list[Track]:
        root = Path(directory).expanduser().resolve()
        if not root.exists():
            return []

        files: list[Path] = []
        for fmt in SUPPORTED_FORMATS:
            files.extend(root.rglob(f'*{fmt}'))
            files.extend(root.rglob(f'*{fmt.upper()}'))

        files = sorted(set(files), key=lambda p: str(p).lower())
        tracks: list[Track] = []

        for i, fp in enumerate(files):
            track = self._read_track(str(fp))
            tracks.append(track)
            if progress_cb:
                progress_cb(i + 1, len(files), track)

        self.tracks = tracks
        return tracks

    def _read_track(self, path: str) -> Track:
        track = Track(path=path)

        if not HAS_MUTAGEN:
            track.title = Path(path).stem
            return track

        try:
            easy = MutagenFile(path, easy=True)
            if easy is None:
                raise ValueError('unreadable')

            def g(key, fallback=''):
                vals = easy.get(key, [fallback])
                return str(vals[0]) if vals else fallback

            track.title  = g('title',  Path(path).stem)
            track.artist = g('artist', '')
            track.album  = g('album',  '')
            track.genre  = g('genre',  '')
            track.year   = g('date',   '')

            tn = g('tracknumber', '0')
            try:
                track.track_number = int(tn.split('/')[0])
            except (ValueError, IndexError):
                track.track_number = 0

            if hasattr(easy, 'info') and easy.info:
                track.duration = getattr(easy.info, 'length', 0.0)

            track.has_cover = self._probe_cover(path)

        except Exception:
            track.title = Path(path).stem

        return track

    # ──────────────────────────────────────────────
    # Cover art
    # ──────────────────────────────────────────────

    def _probe_cover(self, path: str) -> bool:
        try:
            raw = MutagenFile(path)
            if raw is None:
                return False
            if hasattr(raw, 'tags') and raw.tags:
                for key in raw.tags.keys():
                    if 'APIC' in key or 'covr' in key or 'COVR' in key:
                        return True
            if hasattr(raw, 'pictures') and raw.pictures:
                return True
        except Exception:
            pass
        return False

    def get_cover_bytes(self, path: str) -> Optional[bytes]:
        if path in self._cover_cache:
            return self._cover_cache[path]

        data: Optional[bytes] = None
        try:
            raw = MutagenFile(path)
            if raw is None:
                raise ValueError

            # ID3 (MP3, AIFF …)
            if hasattr(raw, 'tags') and raw.tags:
                for key in list(raw.tags.keys()):
                    if key.startswith('APIC'):
                        data = raw.tags[key].data
                        break

            # FLAC / OGG pictures
            if data is None and hasattr(raw, 'pictures') and raw.pictures:
                data = raw.pictures[0].data

            # M4A / AAC
            if data is None and 'covr' in raw:
                data = bytes(raw['covr'][0])

        except Exception:
            pass

        self._cover_cache[path] = data
        return data

    # ──────────────────────────────────────────────
    # Filtering helpers
    # ──────────────────────────────────────────────

    def search(self, query: str) -> list[Track]:
        q = query.lower()
        return [
            t for t in self.tracks
            if q in t.display_title.lower()
            or q in t.display_artist.lower()
            or q in t.display_album.lower()
        ]

    def get_artists(self) -> list[str]:
        return sorted({t.display_artist for t in self.tracks})

    def get_albums(self) -> list[str]:
        return sorted({t.display_album for t in self.tracks})

    def by_artist(self, artist: str) -> list[Track]:
        return [t for t in self.tracks if t.display_artist == artist]

    def by_album(self, album: str) -> list[Track]:
        return [t for t in self.tracks if t.display_album == album]
