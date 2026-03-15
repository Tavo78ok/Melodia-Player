"""
Melodia — GStreamer Audio Backend
Wraps a GStreamer playbin pipeline with simple Python callbacks.
"""

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


class Player:
    """
    Simple GStreamer player wrapping a 'playbin' pipeline.

    Callbacks (assign directly):
        on_position_changed(position: float, duration: float)
        on_track_finished()
        on_state_changed(playing: bool)
        on_error(message: str)
    """

    TICK_MS = 300  # position-update interval

    def __init__(self):
        Gst.init(None)

        self._pipeline = Gst.ElementFactory.make('playbin', 'melodia-player')
        if self._pipeline is None:
            raise RuntimeError(
                'GStreamer playbin element not found. '
                'Install gstreamer1.0-plugins-base.'
            )

        self._playing = False
        self._duration = 0.0
        self._volume = 0.8
        self._pipeline.set_property('volume', self._volume)

        # Public callbacks — replace at will
        self.on_position_changed = None   # (pos, dur) -> None
        self.on_track_finished   = None   # () -> None
        self.on_state_changed    = None   # (playing) -> None
        self.on_error            = None   # (msg) -> None

        bus = self._pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message', self._on_bus_message)

        self._tick_id = GLib.timeout_add(self.TICK_MS, self._tick)

    # ──────────────────────────────────────────────
    # Playback control
    # ──────────────────────────────────────────────

    def play_uri(self, uri: str):
        """Play a file:// URI."""
        self._pipeline.set_state(Gst.State.NULL)
        self._pipeline.set_property('uri', uri)
        self._pipeline.set_state(Gst.State.PLAYING)
        self._playing = True
        self._duration = 0.0
        self._emit_state()

    def play_path(self, path: str):
        """Convenience wrapper: play from a filesystem path."""
        import urllib.parse
        uri = 'file://' + urllib.parse.quote(path)
        self.play_uri(uri)

    def play_pause(self) -> bool:
        """Toggle play/pause. Returns True when now playing."""
        if self._playing:
            self._pipeline.set_state(Gst.State.PAUSED)
            self._playing = False
        else:
            self._pipeline.set_state(Gst.State.PLAYING)
            self._playing = True
        self._emit_state()
        return self._playing

    def stop(self):
        self._pipeline.set_state(Gst.State.NULL)
        self._playing = False
        self._emit_state()

    def seek(self, seconds: float):
        """Seek to a position in seconds."""
        ns = int(seconds * Gst.SECOND)
        self._pipeline.seek_simple(
            Gst.Format.TIME,
            Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
            ns,
        )

    # ──────────────────────────────────────────────
    # Properties
    # ──────────────────────────────────────────────

    @property
    def is_playing(self) -> bool:
        return self._playing

    @property
    def position(self) -> float:
        ok, pos = self._pipeline.query_position(Gst.Format.TIME)
        return pos / Gst.SECOND if ok and pos >= 0 else 0.0

    @property
    def duration(self) -> float:
        if self._duration > 0:
            return self._duration
        ok, dur = self._pipeline.query_duration(Gst.Format.TIME)
        if ok and dur > 0:
            self._duration = dur / Gst.SECOND
        return self._duration

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(0.0, min(1.0, value))
        self._pipeline.set_property('volume', self._volume)

    # ──────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────

    def _tick(self) -> bool:
        if self._playing and self.on_position_changed:
            self.on_position_changed(self.position, self.duration)
        return True  # keep repeating

    def _emit_state(self):
        if self.on_state_changed:
            self.on_state_changed(self._playing)

    def _on_bus_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            self._playing = False
            self._emit_state()
            if self.on_track_finished:
                self.on_track_finished()

        elif t == Gst.MessageType.ERROR:
            err, dbg = message.parse_error()
            self._playing = False
            self._pipeline.set_state(Gst.State.NULL)
            self._emit_state()
            if self.on_error:
                self.on_error(str(err))
            else:
                print(f'[Player] GStreamer error: {err}\n{dbg}')

        elif t == Gst.MessageType.DURATION_CHANGED:
            self._duration = 0.0  # force re-query on next tick

    def __del__(self):
        try:
            self._pipeline.set_state(Gst.State.NULL)
            if self._tick_id:
                GLib.source_remove(self._tick_id)
        except Exception:
            pass
