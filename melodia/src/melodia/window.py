"""
Melodia v1.2 — Main Application Window
GTK4 + libadwaita, dark luxury aesthetic.
New in 1.2: persistent config, working Settings, synced lyrics panel.
"""

import math
import random
import time
import threading
from pathlib import Path
from typing import Optional

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('GdkPixbuf', '2.0')
gi.require_version('Pango', '1.0')
gi.require_version('Gdk', '4.0')

from gi.repository import Gtk, Adw, GLib, Gio, GdkPixbuf, Gdk, Pango
import cairo

from .player  import Player
from .library import MusicLibrary, Track
from .config  import load as cfg_load, save as cfg_save
from .lyrics  import fetch as lyrics_fetch, LyricsResult

# ──────────────────────────────────────────────────────────────────────────────
# Colour palette & CSS
# ──────────────────────────────────────────────────────────────────────────────

ACCENT    = '#E8725A'
ACCENT_HV = '#F08878'
ACCENT_PR = '#D05040'

PLACEHOLDER_PALETTES = [
    ('#E8725A', '#C04030'),
    ('#6B9FD4', '#3A6090'),
    ('#7BC47F', '#4A9050'),
    ('#C47BC4', '#904090'),
    ('#D4AC6B', '#A07830'),
    ('#5BBCBC', '#308080'),
    ('#E8A85A', '#C07830'),
    ('#9B7BC4', '#604090'),
]

CSS = """
.melodia-window { background-color: #0d0d0d; }

headerbar.melodia-header {
    background-color: #111111;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    box-shadow: none;
}
headerbar.melodia-header .title {
    font-weight: 700; font-size: 15px; letter-spacing: 0.04em;
}

.sidebar {
    background-color: #111111;
    border-right: 1px solid rgba(255,255,255,0.06);
}
.logo-label { font-weight: 800; font-size: 17px; letter-spacing: 0.08em; color: #f0f0f0; }
.logo-icon  { color: #E8725A; }
.sidebar-sep { margin: 0 0 4px 0; opacity: 0.15; }
.nav-section-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; color: #555555; }
.nav-item {
    background: none; border: none; border-radius: 8px;
    padding: 9px 12px; color: #aaaaaa;
    transition: background-color 120ms ease, color 120ms ease;
}
.nav-item:hover { background-color: rgba(255,255,255,0.06); color: #e0e0e0; box-shadow: none; }
.nav-item.active { background-color: rgba(232,114,90,0.18); color: #E8725A; }
.nav-item-label { font-size: 13px; font-weight: 500; }

.main-area { background-color: #0d0d0d; }
.page-title { font-size: 26px; font-weight: 800; color: #f0f0f0; letter-spacing: -0.02em; }
.track-count { font-size: 12px; color: #555555; font-weight: 400; }
.col-header-label { font-size: 10px; font-weight: 700; letter-spacing: 0.1em; color: #444444; }

.track-list-box { background: transparent; }
.track-list-box > row { background: transparent; padding: 0; }
.track-list-box > row:hover > .track-row { background-color: rgba(255,255,255,0.04); }
.track-list-box > row:selected > .track-row { background-color: rgba(232,114,90,0.10); }
.track-row { padding: 7px 24px; border-radius: 0; transition: background-color 100ms ease; }
.track-num-label { font-size: 13px; color: #555555; font-variant-numeric: tabular-nums; min-width: 32px; }
.track-title-text { font-size: 13px; font-weight: 500; color: #eeeeee; }
.track-artist-text { font-size: 11px; color: #777777; }
.track-album-text { font-size: 12px; color: #666666; }
.track-dur-text { font-size: 12px; color: #555555; font-variant-numeric: tabular-nums; }
.track-row.playing .track-title-text { color: #E8725A; font-weight: 600; }
.track-row.playing .track-num-label  { color: #E8725A; }

.player-bar {
    background-color: #141414;
    border-top: 1px solid rgba(255,255,255,0.08);
    min-height: 82px;
}
.now-playing-title  { font-size: 13px; font-weight: 600; color: #f0f0f0; }
.now-playing-artist { font-size: 11px; color: #888888; }
.time-label { font-size: 11px; color: #555555; font-variant-numeric: tabular-nums; min-width: 34px; }

.ctrl-btn {
    background: none; border: none; border-radius: 50%;
    min-width: 34px; min-height: 34px; padding: 6px; color: #aaaaaa;
    transition: background-color 120ms ease, color 120ms ease;
}
.ctrl-btn:hover { background-color: rgba(255,255,255,0.08); color: #f0f0f0; box-shadow: none; }
.ctrl-btn:active { background-color: rgba(255,255,255,0.12); }
.play-btn {
    background-color: #E8725A; border: none; border-radius: 50%;
    min-width: 44px; min-height: 44px; padding: 8px; color: white;
    transition: background-color 120ms ease, box-shadow 120ms ease;
}
.play-btn:hover { background-color: #F08878; box-shadow: 0 4px 18px rgba(232,114,90,0.45); }
.play-btn:active { background-color: #D05040; }

scale.seek-bar trough { background-color: rgba(255,255,255,0.10); border-radius: 3px; min-height: 4px; }
scale.seek-bar trough highlight { background-color: #E8725A; border-radius: 3px; }
scale.seek-bar slider { background-color: #ffffff; border-radius: 50%; min-width: 12px; min-height: 12px; border: none; box-shadow: 0 1px 4px rgba(0,0,0,0.5); }
scale.volume-bar trough { background-color: rgba(255,255,255,0.10); border-radius: 2px; min-height: 3px; }
scale.volume-bar trough highlight { background-color: rgba(255,255,255,0.35); border-radius: 2px; }
scale.volume-bar slider { background-color: #ffffff; border-radius: 50%; min-width: 10px; min-height: 10px; border: none; }

.lyrics-panel {
    background-color: #0f0f0f;
    border-left: 1px solid rgba(255,255,255,0.07);
}
.lyrics-title-label { font-size: 10px; font-weight: 700; letter-spacing: 0.12em; color: #444444; }
.lyrics-line { font-size: 15px; font-weight: 400; color: #444444; padding: 3px 0; }
.lyrics-line-active { font-size: 16px; font-weight: 700; color: #f0f0f0; padding: 3px 0; }
.lyrics-line-plain { font-size: 14px; color: #777777; }
.lyrics-status { font-size: 13px; color: #3a3a3a; font-style: italic; }

.settings-folder-label { font-size: 11px; color: #888888; font-family: monospace; }
"""


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _palette_for(text: str):
    idx = sum(ord(c) for c in text) % len(PLACEHOLDER_PALETTES)
    return PLACEHOLDER_PALETTES[idx]


def _hex_to_rgb(h: str):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


class AlbumArtWidget(Gtk.DrawingArea):
    def __init__(self, size=52, radius=6.0):
        super().__init__()
        self.art_size = size
        self.radius   = radius
        self._pixbuf  = None
        self._seed    = '?'
        self.set_size_request(size, size)
        self.set_draw_func(self._draw)

    def set_cover_bytes(self, data: Optional[bytes]):
        if data:
            try:
                loader = GdkPixbuf.PixbufLoader()
                loader.write(data)
                loader.close()
                pb = loader.get_pixbuf()
                s  = self.art_size
                self._pixbuf = pb.scale_simple(s, s, GdkPixbuf.InterpType.BILINEAR)
            except Exception:
                self._pixbuf = None
        else:
            self._pixbuf = None
        self.queue_draw()

    def set_placeholder(self, seed='?'):
        self._seed   = seed
        self._pixbuf = None
        self.queue_draw()

    def _rounded_rect(self, cr, w, h):
        r = self.radius
        cr.new_path()
        cr.arc(r, r, r, math.pi, 1.5*math.pi)
        cr.arc(w-r, r, r, -0.5*math.pi, 0)
        cr.arc(w-r, h-r, r, 0, 0.5*math.pi)
        cr.arc(r, h-r, r, 0.5*math.pi, math.pi)
        cr.close_path()

    def _draw(self, area, cr, w, h):
        self._rounded_rect(cr, w, h)
        cr.clip()
        if self._pixbuf:
            Gdk.cairo_set_source_pixbuf(cr, self._pixbuf, 0, 0)
            cr.paint()
        else:
            c1, c2 = _palette_for(self._seed)
            r1,g1,b1 = _hex_to_rgb(c1)
            r2,g2,b2 = _hex_to_rgb(c2)
            grad = cairo.LinearGradient(0, 0, w, h)
            grad.add_color_stop_rgb(0, r1,g1,b1)
            grad.add_color_stop_rgb(1, r2,g2,b2)
            cr.set_source(grad)
            cr.paint()
            cr.set_source_rgba(1, 1, 1, 0.55)
            cr.set_font_size(h * 0.38)
            note = chr(9834)
            te = cr.text_extents(note)
            cr.move_to((w-te.width)/2 - te.x_bearing,
                       (h-te.height)/2 - te.y_bearing)
            cr.show_text(note)


class EqualizerWidget(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self._active  = False
        self._tick_id = None
        self.set_size_request(18, 16)
        self.set_draw_func(self._draw)

    def start(self):
        self._active = True
        if not self._tick_id:
            self._tick_id = GLib.timeout_add(60, self._tick)

    def stop(self):
        self._active = False
        if self._tick_id:
            GLib.source_remove(self._tick_id)
            self._tick_id = None
        self.queue_draw()

    def _tick(self):
        self.queue_draw()
        return self._active

    def _draw(self, area, cr, w, h):
        r,g,b = _hex_to_rgb(ACCENT)
        if not self._active:
            cr.set_source_rgba(r, g, b, 0.45)
            for i in range(3):
                bh = h * 0.35
                cr.rectangle(i*5, h-bh, 3, bh)
                cr.fill()
            return
        t = time.time()
        cr.set_source_rgba(r, g, b, 0.85)
        for i in range(3):
            bh = (0.25 + 0.75*abs(math.sin(t*(1.8+i*0.9) + i*1.1))) * (h-2)
            cr.rectangle(i*5, h-bh, 3, bh)
            cr.fill()


class TrackRow(Gtk.Box):
    def __init__(self, track: Track, index: int):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.track = track
        self.add_css_class('track-row')

        num_stack = Gtk.Stack()
        num_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        num_stack.set_transition_duration(150)
        num_stack.set_size_request(32, -1)

        self._num_label = Gtk.Label(label=str(index + 1))
        self._num_label.add_css_class('track-num-label')
        self._num_label.set_halign(Gtk.Align.END)
        num_stack.add_named(self._num_label, 'num')

        self._eq = EqualizerWidget()
        self._eq.set_halign(Gtk.Align.CENTER)
        self._eq.set_valign(Gtk.Align.CENTER)
        num_stack.add_named(self._eq, 'eq')
        self._num_stack = num_stack

        self._art = AlbumArtWidget(size=38, radius=4)
        self._art.set_placeholder(track.display_title)
        self._art.set_margin_end(10)
        self._art.set_margin_start(8)
        self._art.set_valign(Gtk.Align.CENTER)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        info.set_valign(Gtk.Align.CENTER)
        info.set_hexpand(True)

        self._title_lbl = Gtk.Label(label=track.display_title)
        self._title_lbl.add_css_class('track-title-text')
        self._title_lbl.set_halign(Gtk.Align.START)
        self._title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._title_lbl.set_max_width_chars(40)

        self._artist_lbl = Gtk.Label(label=track.display_artist)
        self._artist_lbl.add_css_class('track-artist-text')
        self._artist_lbl.set_halign(Gtk.Align.START)
        self._artist_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        self._artist_lbl.set_max_width_chars(40)

        info.append(self._title_lbl)
        info.append(self._artist_lbl)

        album_lbl = Gtk.Label(label=track.display_album)
        album_lbl.add_css_class('track-album-text')
        album_lbl.set_halign(Gtk.Align.START)
        album_lbl.set_ellipsize(Pango.EllipsizeMode.END)
        album_lbl.set_max_width_chars(24)
        album_lbl.set_size_request(190, -1)
        album_lbl.set_margin_end(16)

        dur_lbl = Gtk.Label(label=track.duration_str())
        dur_lbl.add_css_class('track-dur-text')
        dur_lbl.set_halign(Gtk.Align.END)
        dur_lbl.set_size_request(52, -1)
        dur_lbl.set_margin_end(8)

        self.append(num_stack)
        self.append(self._art)
        self.append(info)
        self.append(album_lbl)
        self.append(dur_lbl)

    def set_playing(self, playing: bool, paused=False):
        if playing:
            self.add_css_class('playing')
            self._num_stack.set_visible_child_name('eq')
            self._eq.stop() if paused else self._eq.start()
        else:
            self.remove_css_class('playing')
            self._num_stack.set_visible_child_name('num')
            self._eq.stop()

    def load_art(self, cover_bytes: Optional[bytes]):
        if cover_bytes:
            self._art.set_cover_bytes(cover_bytes)


# ──────────────────────────────────────────────────────────────────────────────
# Lyrics panel
# ──────────────────────────────────────────────────────────────────────────────

class LyricsPanel(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add_css_class('lyrics-panel')
        self.set_size_request(300, -1)

        self._result: Optional[LyricsResult] = None
        self._current_line = -1
        self._line_labels: list[Gtk.Label] = []

        header = Gtk.Box()
        header.set_margin_start(20)
        header.set_margin_end(20)
        header.set_margin_top(18)
        header.set_margin_bottom(12)
        title = Gtk.Label(label='LYRICS')
        title.add_css_class('lyrics-title-label')
        title.set_halign(Gtk.Align.START)
        header.append(title)
        self.append(header)

        sep = Gtk.Separator()
        sep.set_opacity(0.1)
        self.append(sep)

        self._scroll = Gtk.ScrolledWindow()
        self._scroll.set_vexpand(True)
        self._scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self._content.set_margin_start(20)
        self._content.set_margin_end(20)
        self._content.set_margin_top(16)
        self._content.set_margin_bottom(40)
        self._scroll.set_child(self._content)
        self.append(self._scroll)

        self._show_status('Play a song to see lyrics')

    def _clear_content(self):
        self._line_labels.clear()
        child = self._content.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self._content.remove(child)
            child = nxt

    def _show_status(self, msg: str):
        self._clear_content()
        lbl = Gtk.Label(label=msg)
        lbl.add_css_class('lyrics-status')
        lbl.set_halign(Gtk.Align.START)
        lbl.set_valign(Gtk.Align.START)
        lbl.set_margin_top(20)
        self._content.append(lbl)

    def show_loading(self):
        GLib.idle_add(self._show_status, 'Searching for lyrics...')

    def show_result(self, result: Optional[LyricsResult]):
        def _do():
            self._result = result
            self._current_line = -1
            self._clear_content()

            if not result or not result.has_lyrics:
                self._show_status('No lyrics found')
                return

            if result.has_synced:
                for line in result.synced:
                    lbl = Gtk.Label(label=line.text or '')
                    lbl.add_css_class('lyrics-line')
                    lbl.set_halign(Gtk.Align.START)
                    lbl.set_wrap(True)
                    lbl.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
                    lbl.set_xalign(0)
                    self._line_labels.append(lbl)
                    self._content.append(lbl)
            else:
                for line in result.plain.splitlines():
                    lbl = Gtk.Label(label=line)
                    lbl.add_css_class('lyrics-line-plain')
                    lbl.set_halign(Gtk.Align.START)
                    lbl.set_xalign(0)
                    self._content.append(lbl)
        GLib.idle_add(_do)

    def update_position(self, position: float):
        if not self._result or not self._result.has_synced:
            return
        idx = self._result.line_at(position)
        if idx == self._current_line:
            return
        self._current_line = idx

        def _do():
            for i, lbl in enumerate(self._line_labels):
                if i == idx:
                    lbl.remove_css_class('lyrics-line')
                    lbl.add_css_class('lyrics-line-active')
                else:
                    lbl.remove_css_class('lyrics-line-active')
                    lbl.add_css_class('lyrics-line')
            if 0 <= idx < len(self._line_labels):
                active_lbl = self._line_labels[idx]
                def scroll_to():
                    adj    = self._scroll.get_vadjustment()
                    alloc  = active_lbl.get_allocation()
                    if alloc.height > 0:
                        target = alloc.y - (self._scroll.get_height() / 2)
                        adj.set_value(max(0, target))
                GLib.timeout_add(60, scroll_to)
        GLib.idle_add(_do)

    def reset(self):
        self._result = None
        self._current_line = -1
        GLib.idle_add(self._show_status, 'Play a song to see lyrics')


# ──────────────────────────────────────────────────────────────────────────────
# Settings dialog
# ──────────────────────────────────────────────────────────────────────────────

class SettingsDialog(Adw.PreferencesDialog):
    def __init__(self, parent_window, cfg: dict, on_folder_changed):
        super().__init__()
        self.set_title('Settings')
        self._cfg = cfg
        self._on_folder_changed = on_folder_changed
        self._parent = parent_window

        page = Adw.PreferencesPage()
        page.set_title('General')
        page.set_icon_name('preferences-system-symbolic')

        # Music Library
        lib_group = Adw.PreferencesGroup()
        lib_group.set_title('Music Library')
        lib_group.set_description('Folder scanned at startup')

        folder_row = Adw.ActionRow()
        folder_row.set_title('Music Folder')

        folder_path = cfg.get('music_folder', str(Path.home() / 'Music'))
        self._folder_lbl = Gtk.Label(label=folder_path)
        self._folder_lbl.add_css_class('settings-folder-label')
        self._folder_lbl.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        self._folder_lbl.set_max_width_chars(28)
        folder_row.add_suffix(self._folder_lbl)

        browse_btn = Gtk.Button(label='Browse...')
        browse_btn.add_css_class('flat')
        browse_btn.set_valign(Gtk.Align.CENTER)
        browse_btn.connect('clicked', self._on_browse)
        folder_row.add_suffix(browse_btn)

        lib_group.add(folder_row)
        page.add(lib_group)

        # Playback
        pb_group = Adw.PreferencesGroup()
        pb_group.set_title('Playback')

        shuffle_row = Adw.SwitchRow()
        shuffle_row.set_title('Shuffle')
        shuffle_row.set_subtitle('Play songs in random order')
        shuffle_row.set_active(cfg.get('shuffle', False))
        shuffle_row.connect('notify::active',
                            lambda r, _: self._set('shuffle', r.get_active()))

        repeat_row = Adw.SwitchRow()
        repeat_row.set_title('Repeat')
        repeat_row.set_subtitle('Loop the playlist when it ends')
        repeat_row.set_active(cfg.get('repeat', False))
        repeat_row.connect('notify::active',
                           lambda r, _: self._set('repeat', r.get_active()))

        pb_group.add(shuffle_row)
        pb_group.add(repeat_row)
        page.add(pb_group)

        # Lyrics
        lyr_group = Adw.PreferencesGroup()
        lyr_group.set_title('Lyrics')

        lyrics_row = Adw.SwitchRow()
        lyrics_row.set_title('Show Lyrics Panel')
        lyrics_row.set_subtitle('Fetches synced lyrics from lrclib.net')
        lyrics_row.set_active(cfg.get('show_lyrics', False))
        lyrics_row.connect('notify::active',
                           lambda r, _: self._set('show_lyrics', r.get_active()))
        lyr_group.add(lyrics_row)
        page.add(lyr_group)

        # About
        about_group = Adw.PreferencesGroup()
        about_group.set_title('About')

        ver_row = Adw.ActionRow()
        ver_row.set_title('Version')
        ver_lbl = Gtk.Label(label='1.2.0')
        ver_lbl.set_opacity(0.5)
        ver_row.add_suffix(ver_lbl)

        src_row = Adw.ActionRow()
        src_row.set_title('Lyrics source')
        src_lbl = Gtk.Label(label='lrclib.net (free, no key)')
        src_lbl.set_opacity(0.5)
        src_row.add_suffix(src_lbl)

        about_group.add(ver_row)
        about_group.add(src_row)
        page.add(about_group)

        self.add(page)

    def _set(self, key: str, value):
        self._cfg[key] = value
        cfg_save(self._cfg)

    def _on_browse(self, _btn):
        dialog = Gtk.FileDialog()
        dialog.set_title('Select Music Folder')
        dialog.select_folder(self._parent, None, self._folder_result)

    def _folder_result(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self._folder_lbl.set_text(path)
                self._cfg['music_folder'] = path
                cfg_save(self._cfg)
                if self._on_folder_changed:
                    self._on_folder_changed(path)
        except GLib.Error:
            pass


# ──────────────────────────────────────────────────────────────────────────────
# Main window
# ──────────────────────────────────────────────────────────────────────────────

class MelodiaWindow(Adw.ApplicationWindow):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._cfg = cfg_load()
        self.library   = MusicLibrary()
        self.player    = Player()
        self.playlist: list[Track] = []
        self.current_index = -1
        self._seeking  = False
        self._rows: list[TrackRow] = []
        self._nav_key  = 'songs'
        self._lyrics_result: Optional[LyricsResult] = None

        self.player.on_position_changed = self._on_pos_changed
        self.player.on_track_finished   = self._on_track_finished
        self.player.on_state_changed    = self._on_state_changed
        self.player.on_error            = self._on_player_error

        self.player.volume = self._cfg.get('volume', 0.8)

        self._apply_css()
        self._build_ui()

        # Restore saved states
        self._shuffle_btn.set_active(self._cfg.get('shuffle', False))
        self._repeat_btn.set_active(self._cfg.get('repeat', False))
        self._vol.set_value(self._cfg.get('volume', 0.8))

        show_lyrics = self._cfg.get('show_lyrics', False)
        self._lyrics_btn.set_active(show_lyrics)
        self._lyrics_panel.set_visible(show_lyrics)

        # Auto-load saved music folder
        folder = self._cfg.get('music_folder', '')
        if folder and Path(folder).exists():
            self._load_directory(folder)

        self.connect('close-request', self._on_close)

    # ──────────────────────────────────────────────
    def _apply_css(self):
        provider = Gtk.CssProvider()
        provider.load_from_string(CSS)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    # ──────────────────────────────────────────────
    def _build_ui(self):
        self.set_title('Melodia')
        self.set_default_size(1280, 780)
        self.add_css_class('melodia-window')

        toolbar = Adw.ToolbarView()
        self.set_content(toolbar)
        toolbar.add_top_bar(self._build_headerbar())
        toolbar.add_bottom_bar(self._build_player_bar())
        toolbar.set_content(self._build_body())

    def _build_headerbar(self):
        hb = Adw.HeaderBar()
        hb.add_css_class('melodia-header')

        self._search_btn = Gtk.ToggleButton(icon_name='system-search-symbolic')
        self._search_btn.set_tooltip_text('Search')
        self._search_btn.connect('toggled', self._on_search_toggled)
        hb.pack_end(self._search_btn)

        self._lyrics_btn = Gtk.ToggleButton(icon_name='format-justify-left-symbolic')
        self._lyrics_btn.set_tooltip_text('Show Lyrics')
        self._lyrics_btn.connect('toggled', self._on_lyrics_toggled)
        hb.pack_end(self._lyrics_btn)

        menu = Gio.Menu()
        menu.append('Open Folder...', 'win.open-folder')
        menu.append('Settings', 'win.settings')
        menu.append('About Melodia', 'app.about')
        menu_btn = Gtk.MenuButton(icon_name='open-menu-symbolic', menu_model=menu)
        hb.pack_end(menu_btn)

        self._search_entry = Gtk.SearchEntry()
        self._search_entry.set_placeholder_text('Search songs, artists, albums...')
        self._search_entry.set_hexpand(True)
        self._search_entry.set_visible(False)
        self._search_entry.connect('search-changed', self._on_search_changed)
        hb.set_title_widget(self._search_entry)

        act = Gio.SimpleAction.new('open-folder', None)
        act.connect('activate', self._on_open_folder)
        self.add_action(act)

        settings_act = Gio.SimpleAction.new('settings', None)
        settings_act.connect('activate', self._on_settings)
        self.add_action(settings_act)

        return hb

    def _build_player_bar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bar.add_css_class('player-bar')

        left = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        left.set_size_request(290, -1)
        left.set_margin_start(16)
        left.set_margin_top(14)
        left.set_margin_bottom(14)
        left.set_valign(Gtk.Align.CENTER)

        self._player_art = AlbumArtWidget(size=52, radius=7)
        left.append(self._player_art)

        info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        info.set_valign(Gtk.Align.CENTER)

        self._pl_title = Gtk.Label(label='No track playing')
        self._pl_title.add_css_class('now-playing-title')
        self._pl_title.set_halign(Gtk.Align.START)
        self._pl_title.set_ellipsize(Pango.EllipsizeMode.END)
        self._pl_title.set_max_width_chars(26)

        self._pl_artist = Gtk.Label(label='')
        self._pl_artist.add_css_class('now-playing-artist')
        self._pl_artist.set_halign(Gtk.Align.START)
        self._pl_artist.set_ellipsize(Pango.EllipsizeMode.END)
        self._pl_artist.set_max_width_chars(26)

        info.append(self._pl_title)
        info.append(self._pl_artist)
        left.append(info)
        bar.append(left)

        centre = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        centre.set_hexpand(True)
        centre.set_halign(Gtk.Align.CENTER)
        centre.set_valign(Gtk.Align.CENTER)
        centre.set_margin_top(14)
        centre.set_margin_bottom(14)

        btns = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        btns.set_halign(Gtk.Align.CENTER)

        self._shuffle_btn = Gtk.ToggleButton(icon_name='media-playlist-shuffle-symbolic')
        self._shuffle_btn.add_css_class('ctrl-btn')
        self._shuffle_btn.connect('toggled', lambda b: self._save_cfg())

        prev_btn = Gtk.Button(icon_name='media-skip-backward-symbolic')
        prev_btn.add_css_class('ctrl-btn')
        prev_btn.connect('clicked', lambda _: self._prev_track())

        self._play_btn = Gtk.Button(icon_name='media-playback-start-symbolic')
        self._play_btn.add_css_class('play-btn')
        self._play_btn.connect('clicked', self._on_play_pause)

        next_btn = Gtk.Button(icon_name='media-skip-forward-symbolic')
        next_btn.add_css_class('ctrl-btn')
        next_btn.connect('clicked', lambda _: self._next_track())

        self._repeat_btn = Gtk.ToggleButton(icon_name='media-playlist-repeat-symbolic')
        self._repeat_btn.add_css_class('ctrl-btn')
        self._repeat_btn.connect('toggled', lambda b: self._save_cfg())

        for w in (self._shuffle_btn, prev_btn, self._play_btn, next_btn, self._repeat_btn):
            btns.append(w)

        seek_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        seek_row.set_size_request(440, -1)
        seek_row.set_halign(Gtk.Align.CENTER)

        self._time_lbl = Gtk.Label(label='0:00')
        self._time_lbl.add_css_class('time-label')
        self._time_lbl.set_halign(Gtk.Align.END)

        self._seek = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self._seek.set_hexpand(True)
        self._seek.add_css_class('seek-bar')
        self._seek.set_range(0, 1)
        self._seek.set_value(0)
        self._seek.set_draw_value(False)

        gc = Gtk.GestureClick()
        gc.connect('pressed',  self._on_seek_press)
        gc.connect('released', self._on_seek_release)
        self._seek.add_controller(gc)

        self._dur_lbl = Gtk.Label(label='0:00')
        self._dur_lbl.add_css_class('time-label')
        self._dur_lbl.set_halign(Gtk.Align.START)

        seek_row.append(self._time_lbl)
        seek_row.append(self._seek)
        seek_row.append(self._dur_lbl)

        centre.append(btns)
        centre.append(seek_row)
        bar.append(centre)

        right = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        right.set_size_request(220, -1)
        right.set_halign(Gtk.Align.END)
        right.set_valign(Gtk.Align.CENTER)
        right.set_margin_end(20)

        vol_icon = Gtk.Image.new_from_icon_name('audio-volume-medium-symbolic')
        vol_icon.set_pixel_size(16)
        vol_icon.set_opacity(0.5)

        self._vol = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self._vol.add_css_class('volume-bar')
        self._vol.set_range(0, 1)
        self._vol.set_value(0.8)
        self._vol.set_size_request(96, -1)
        self._vol.set_draw_value(False)
        self._vol.connect('value-changed', self._on_vol_changed)

        right.append(vol_icon)
        right.append(self._vol)
        bar.append(right)
        return bar

    def _build_body(self):
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.append(self._build_sidebar())

        content_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        content_row.set_hexpand(True)
        content_row.append(self._build_content_area())

        self._lyrics_panel = LyricsPanel()
        self._lyrics_panel.set_visible(False)
        content_row.append(self._lyrics_panel)

        body.append(content_row)
        return body

    def _build_sidebar(self):
        sb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        sb.add_css_class('sidebar')
        sb.set_size_request(215, -1)

        logo = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        logo.set_margin_start(16)
        logo.set_margin_top(18)
        logo.set_margin_bottom(10)
        logo_ic = Gtk.Image.new_from_icon_name('audio-x-generic')
        logo_ic.set_pixel_size(22)
        logo_ic.add_css_class('logo-icon')
        logo_lbl = Gtk.Label(label='MELODIA')
        logo_lbl.add_css_class('logo-label')
        logo.append(logo_ic)
        logo.append(logo_lbl)
        sb.append(logo)

        sep = Gtk.Separator()
        sep.add_css_class('sidebar-sep')
        sb.append(sep)

        sec = Gtk.Label(label='LIBRARY')
        sec.add_css_class('nav-section-label')
        sec.set_halign(Gtk.Align.START)
        sec.set_margin_start(16)
        sec.set_margin_top(14)
        sec.set_margin_bottom(6)
        sb.append(sec)

        nav_items = [
            ('songs',     'audio-x-generic-symbolic',  'Songs'),
            ('artists',   'avatar-default-symbolic',   'Artists'),
            ('albums',    'media-optical-symbolic',     'Albums'),
            ('favorites', 'starred-symbolic',          'Favorites'),
        ]
        self._nav_btns: dict[str, Gtk.Button] = {}
        nav_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        nav_box.set_margin_start(8)
        nav_box.set_margin_end(8)

        for key, icon, label in nav_items:
            btn = Gtk.Button()
            btn.add_css_class('nav-item')
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
            ic  = Gtk.Image.new_from_icon_name(icon)
            ic.set_pixel_size(15)
            lbl = Gtk.Label(label=label)
            lbl.add_css_class('nav-item-label')
            lbl.set_halign(Gtk.Align.START)
            row.append(ic)
            row.append(lbl)
            btn.set_child(row)
            btn.connect('clicked', self._on_nav, key)
            self._nav_btns[key] = btn
            nav_box.append(btn)

        self._nav_btns['songs'].add_css_class('active')
        sb.append(nav_box)

        sp = Gtk.Box()
        sp.set_vexpand(True)
        sb.append(sp)

        settings_btn = Gtk.Button()
        settings_btn.add_css_class('nav-item')
        sr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        si = Gtk.Image.new_from_icon_name('preferences-system-symbolic')
        si.set_pixel_size(15)
        sl = Gtk.Label(label='Settings')
        sl.add_css_class('nav-item-label')
        sl.set_halign(Gtk.Align.START)
        sr.append(si)
        sr.append(sl)
        settings_btn.set_child(sr)
        settings_btn.set_margin_start(8)
        settings_btn.set_margin_end(8)
        settings_btn.set_margin_bottom(14)
        settings_btn.connect('clicked', self._on_settings)
        sb.append(settings_btn)
        return sb

    def _build_content_area(self):
        area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        area.add_css_class('main-area')
        area.set_hexpand(True)

        ph = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        ph.set_margin_start(28)
        ph.set_margin_end(28)
        ph.set_margin_top(22)
        ph.set_margin_bottom(10)

        self._page_title = Gtk.Label(label='Songs')
        self._page_title.add_css_class('page-title')
        self._page_title.set_halign(Gtk.Align.START)

        self._count_lbl = Gtk.Label(label='')
        self._count_lbl.add_css_class('track-count')
        self._count_lbl.set_halign(Gtk.Align.START)
        self._count_lbl.set_valign(Gtk.Align.END)
        self._count_lbl.set_margin_bottom(3)

        ph.append(self._page_title)
        ph.append(self._count_lbl)
        area.append(ph)
        area.append(self._build_col_headers())

        self._stack = Gtk.Stack()
        self._stack.set_vexpand(True)
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)

        empty = Adw.StatusPage()
        empty.set_icon_name('audio-x-generic-symbolic')
        empty.set_title('No Music Found')
        empty.set_description('Open a folder containing your music files.')
        ob = Gtk.Button(label='Open Music Folder')
        ob.add_css_class('suggested-action')
        ob.add_css_class('pill')
        ob.connect('clicked', self._on_open_folder)
        empty.set_child(ob)
        self._stack.add_named(empty, 'empty')

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._list = Gtk.ListBox()
        self._list.add_css_class('track-list-box')
        self._list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self._list.connect('row-activated', self._on_row_activated)
        scroll.set_child(self._list)
        self._stack.add_named(scroll, 'list')

        area.append(self._stack)
        return area

    def _build_col_headers(self):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        row.set_margin_start(28)
        row.set_margin_end(28)
        row.set_margin_bottom(2)

        def lbl(text, width=-1, align=Gtk.Align.START):
            l = Gtk.Label(label=text)
            l.add_css_class('col-header-label')
            l.set_halign(align)
            if width > 0:
                l.set_size_request(width, -1)
            return l

        row.append(lbl('#', width=32, align=Gtk.Align.END))
        sp = Gtk.Box(); sp.set_size_request(56, -1)
        row.append(sp)
        tl = lbl('TITLE'); tl.set_hexpand(True)
        row.append(tl)
        row.append(lbl('ALBUM', width=200))
        row.append(lbl('TIME', width=52, align=Gtk.Align.END))

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        vbox.append(row)
        sep = Gtk.Separator()
        sep.set_margin_start(28)
        sep.set_margin_end(28)
        sep.set_opacity(0.12)
        vbox.append(sep)
        return vbox

    # ──────────────────────────────────────────────
    def _load_directory(self, path: str):
        def worker():
            tracks = self.library.scan_directory(path)
            GLib.idle_add(self._populate_list, tracks)
        threading.Thread(target=worker, daemon=True).start()

    def _populate_list(self, tracks: list[Track]):
        self.playlist = tracks
        while True:
            row = self._list.get_row_at_index(0)
            if row is None:
                break
            self._list.remove(row)
        self._rows.clear()

        for i, track in enumerate(tracks):
            tr = TrackRow(track, i)
            self._rows.append(tr)
            lbr = Gtk.ListBoxRow()
            lbr.set_child(tr)
            self._list.append(lbr)

        n = len(tracks)
        self._count_lbl.set_text(f'{n} song{"s" if n != 1 else ""}')
        self._stack.set_visible_child_name('list' if tracks else 'empty')

        threading.Thread(
            target=self._preload_art,
            args=(list(tracks), list(self._rows)),
            daemon=True,
        ).start()
        return False

    def _preload_art(self, tracks, rows):
        for track, row in zip(tracks, rows):
            if track.has_cover:
                data = self.library.get_cover_bytes(track.path)
                if data:
                    GLib.idle_add(row.load_art, data)

    # ──────────────────────────────────────────────
    def _play_index(self, idx: int):
        if not self.playlist or idx < 0 or idx >= len(self.playlist):
            return
        if 0 <= self.current_index < len(self._rows):
            self._rows[self.current_index].set_playing(False)

        self.current_index = idx
        track = self.playlist[idx]
        self.player.play_path(track.path)

        self._pl_title.set_text(track.display_title)
        self._pl_artist.set_text(track.display_artist)
        self._player_art.set_placeholder(track.display_title)

        if track.has_cover:
            def _load():
                data = self.library.get_cover_bytes(track.path)
                GLib.idle_add(self._player_art.set_cover_bytes, data)
            threading.Thread(target=_load, daemon=True).start()
        else:
            self._player_art.set_cover_bytes(None)

        if 0 <= idx < len(self._rows):
            self._rows[idx].set_playing(True, paused=False)

        self._seek.set_value(0)
        self._time_lbl.set_text('0:00')
        self._dur_lbl.set_text(track.duration_str())
        self._play_btn.set_icon_name('media-playback-pause-symbolic')

        self._lyrics_result = None
        if self._cfg.get('show_lyrics', False):
            self._fetch_lyrics(track)

        self._cfg['last_track_index'] = idx
        self._save_cfg()

    def _fetch_lyrics(self, track: Track):
        self._lyrics_panel.show_loading()
        def worker():
            result = lyrics_fetch(
                title=track.display_title,
                artist=track.display_artist,
                album=track.display_album,
                duration=track.duration,
            )
            self._lyrics_result = result
            self._lyrics_panel.show_result(result)
        threading.Thread(target=worker, daemon=True).start()

    def _next_track(self):
        if self._shuffle_btn.get_active() and self.playlist:
            idx = random.randint(0, len(self.playlist) - 1)
        else:
            idx = self.current_index + 1
            if idx >= len(self.playlist):
                idx = 0 if self._repeat_btn.get_active() else -1
        if idx >= 0:
            self._play_index(idx)

    def _prev_track(self):
        if self.player.position > 3.0:
            self.player.seek(0)
            return
        idx = self.current_index - 1
        if idx < 0:
            idx = len(self.playlist) - 1
        if idx >= 0:
            self._play_index(idx)

    # ──────────────────────────────────────────────
    def _on_pos_changed(self, pos: float, dur: float):
        if self._seeking:
            return
        if self._lyrics_result:
            self._lyrics_panel.update_position(pos)
        def update():
            if dur > 0:
                self._seek.set_value(pos / dur)
            self._time_lbl.set_text(self._fmt(pos))
            if dur > 0:
                self._dur_lbl.set_text(self._fmt(dur))
            return False
        GLib.idle_add(update)

    def _on_track_finished(self):
        GLib.idle_add(self._next_track)

    def _on_state_changed(self, playing: bool):
        def update():
            icon = 'media-playback-pause-symbolic' if playing else 'media-playback-start-symbolic'
            self._play_btn.set_icon_name(icon)
            if 0 <= self.current_index < len(self._rows):
                self._rows[self.current_index].set_playing(True, paused=not playing)
            return False
        GLib.idle_add(update)

    def _on_player_error(self, msg: str):
        print(f'[Melodia] Player error: {msg}')

    def _on_row_activated(self, listbox, row):
        self._play_index(row.get_index())

    def _on_play_pause(self, _btn):
        if self.current_index < 0 and self.playlist:
            self._play_index(0)
        else:
            self.player.play_pause()

    def _on_seek_press(self, gesture, n, x, y):
        self._seeking = True

    def _on_seek_release(self, gesture, n, x, y):
        val = self._seek.get_value()
        dur = self.player.duration
        if dur > 0:
            self.player.seek(val * dur)
        self._seeking = False

    def _on_vol_changed(self, scale):
        self.player.volume = scale.get_value()
        self._cfg['volume'] = scale.get_value()

    def _on_search_toggled(self, btn):
        visible = btn.get_active()
        self._search_entry.set_visible(visible)
        if visible:
            self._search_entry.grab_focus()
        else:
            self._search_entry.set_text('')
            self._populate_list(self.library.tracks)

    def _on_search_changed(self, entry):
        q = entry.get_text().strip()
        results = self.library.search(q) if q else self.library.tracks
        self._populate_list(results)

    def _on_nav(self, _btn, key: str):
        for k, b in self._nav_btns.items():
            b.remove_css_class('active')
        self._nav_btns[key].add_css_class('active')
        self._nav_key = key
        titles = {'songs': 'Songs', 'artists': 'Artists',
                  'albums': 'Albums', 'favorites': 'Favorites'}
        self._page_title.set_text(titles.get(key, key.title()))
        if key == 'songs':
            self._populate_list(self.library.tracks)

    def _on_open_folder(self, *_):
        dialog = Gtk.FileDialog()
        dialog.set_title('Open Music Folder')
        dialog.select_folder(self, None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self._cfg['music_folder'] = path
                self._save_cfg()
                self._load_directory(path)
        except GLib.Error:
            pass

    def _on_settings(self, *_):
        dlg = SettingsDialog(
            parent_window=self,
            cfg=self._cfg,
            on_folder_changed=self._load_directory,
        )
        dlg.present(self)

    def _on_lyrics_toggled(self, btn):
        visible = btn.get_active()
        self._lyrics_panel.set_visible(visible)
        self._cfg['show_lyrics'] = visible
        self._save_cfg()
        if visible and self.current_index >= 0:
            self._fetch_lyrics(self.playlist[self.current_index])
        elif not visible:
            self._lyrics_result = None

    def _on_close(self, *_):
        self._save_cfg()
        return False

    # ──────────────────────────────────────────────
    def _save_cfg(self):
        self._cfg['shuffle'] = self._shuffle_btn.get_active()
        self._cfg['repeat']  = self._repeat_btn.get_active()
        cfg_save(self._cfg)

    @staticmethod
    def _fmt(seconds: float) -> str:
        s = int(seconds)
        return f'{s // 60}:{s % 60:02d}'
