#!/usr/bin/env python3
# LinyGUI - Elegant Image Compression Tool
# Copyright (c) 2026 DevOpsInquisitor
# Licensed under MIT License

import sys
import os
import gi

# Ensure our lib directory is importable (for Flatpak installed layout)
_lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "linygui")
if os.path.isdir(_lib_dir):
    sys.path.insert(0, _lib_dir)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, Gdk, GLib

from window import LinyGuiWindow


class LinyGuiApp(Adw.Application):
    """Main application class for LinyGUI."""

    APP_ID = "org.devopsinquisitor.linygui"
    VERSION = "1.0.0"

    def __init__(self):
        super().__init__(
            application_id=self.APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

    def do_startup(self):
        Adw.Application.do_startup(self)
        GLib.set_prgname(self.APP_ID)

        # Force dark color scheme
        style_mgr = Adw.StyleManager.get_default()
        style_mgr.set_color_scheme(Adw.ColorScheme.FORCE_DARK)

        self._load_css()

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = LinyGuiWindow(application=self)

            # Set window icon from icon.png
            src_dir = os.path.dirname(os.path.abspath(__file__))
            icon_dir = os.path.dirname(src_dir)
            icon_path = os.path.join(icon_dir, "icon.png")
            if os.path.exists(icon_path):
                try:
                    # GTK4 uses IconTheme to resolve window icons by name
                    icon_theme = Gtk.IconTheme.get_for_display(Gdk.Display.get_default())
                    icon_theme.add_search_path(icon_dir)
                    win.set_icon_name("icon")
                except Exception:
                    pass

        win.present()

    def _load_css(self):
        """Load the custom glassmorphism CSS theme."""
        css_provider = Gtk.CssProvider()

        # Try multiple paths (dev vs installed)
        candidates = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "linygui.css"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib", "linygui", "linygui.css"),
        ]

        for css_path in candidates:
            if os.path.exists(css_path):
                css_provider.load_from_path(css_path)
                Gtk.StyleContext.add_provider_for_display(
                    Gdk.Display.get_default(),
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                )
                break


def main():
    app = LinyGuiApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
