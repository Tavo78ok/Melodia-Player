"""
Melodia — Application Entry Point
"""

import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gio, GLib

from .window import MelodiaWindow


class MelodiaApplication(Adw.Application):

    def __init__(self):
        super().__init__(
            application_id='com.github.melodia',
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        GLib.set_application_name('Melodia')
        GLib.set_prgname('melodia')

        self.connect('activate', self._on_activate)
        self._add_actions()

    def _add_actions(self):
        about = Gio.SimpleAction.new('about', None)
        about.connect('activate', self._on_about)
        self.add_action(about)

    def _on_activate(self, app):
        win = self.props.active_window
        if not win:
            win = MelodiaWindow(application=app)
        win.present()

    def _on_about(self, *_):
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name='Melodia',
            application_icon='audio-x-generic',
            version='1.0.0',
            developer_name='Your Name',
            website='https://github.com/yourname/melodia',
            issue_url='https://github.com/yourname/melodia/issues',
            license_type=Gtk.License.GPL_3_0,
            comments='A beautiful music player for Linux',
        )
        about.present()


def main():
    app = MelodiaApplication()
    return app.run(sys.argv)
