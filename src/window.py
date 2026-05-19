# LinyGUI - Elegant Image Compression Tool
# Copyright (c) 2026 DevOpsInquisitor
# Licensed under MIT License

import gi
import os
import threading
import subprocess

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gdk, Gio, GLib, GdkPixbuf

try:
    gi.require_version('Secret', '1')
    from gi.repository import Secret
    SECRET_AVAILABLE = True
except ValueError:
    SECRET_AVAILABLE = False

# Check tinify availability at import time
try:
    import tinify
    TINIFY_AVAILABLE = True
except ImportError:
    TINIFY_AVAILABLE = False


class LinyGuiWindow(Adw.ApplicationWindow):
    """Main application window for LinyGUI."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinyGUI")
        self.set_default_size(460, 740)
        self.set_resizable(True)
        self.add_css_class("linygui-window")

        # Resolve icon path
        src_dir = os.path.dirname(os.path.abspath(__file__))
        self._icon_path = os.path.join(os.path.dirname(src_dir), "icon.png")

        self._settings = self._load_settings()
        self._build_ui()

    # ── Settings ──────────────────────────────────────────────────

    def _get_settings_path(self):
        config = os.path.join(GLib.get_user_config_dir(), "linygui")
        os.makedirs(config, exist_ok=True)
        return os.path.join(config, "settings.json")

    def _get_secret_schema(self):
        if not SECRET_AVAILABLE:
            return None
        return Secret.Schema.new("org.devopsinquisitor.linygui",
            Secret.SchemaFlags.NONE,
            {
                "account": Secret.SchemaAttributeType.STRING,
            }
        )

    def _load_settings(self):
        import json
        defaults = {
            "api_key": "",
            "replace_original": False,
            "preserve_copyright": False,
            "preserve_location": False,
            "preserve_creation": False,
        }
        path = self._get_settings_path()
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    stored = json.load(f)
                defaults.update(stored)
            except Exception:
                pass

        # Load API key securely
        schema = self._get_secret_schema()
        if schema:
            try:
                val = Secret.password_lookup_sync(schema, {"account": "tinypng"}, None)
                if val:
                    defaults["api_key"] = val
            except Exception:
                pass

        return defaults

    def _save_settings(self):
        import json
        
        # Save API key securely
        key = self._settings.get("api_key", "")
        schema = self._get_secret_schema()
        if schema:
            try:
                if key:
                    Secret.password_store_sync(schema, {"account": "tinypng"}, Secret.COLLECTION_DEFAULT, "TinyPNG API Key", key, None)
                else:
                    Secret.password_clear_sync(schema, {"account": "tinypng"}, None)
            except Exception:
                pass

        # Save other preferences
        to_save = {k: v for k, v in self._settings.items() if k != "api_key" or not schema}
        try:
            with open(self._get_settings_path(), "w") as f:
                json.dump(to_save, f, indent=2)
        except Exception:
            pass

    # ── UI ────────────────────────────────────────────────────────

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        main_box.add_css_class("main-container")

        # Header bar
        hb = Adw.HeaderBar()
        hb.add_css_class("header-bar-glass")
        hb.set_decoration_layout("icon:minimize,maximize,close")
        title_w = Gtk.Label(label="LinyGUI")
        title_w.add_css_class("headerbar-title")
        hb.set_title_widget(title_w)
        main_box.append(hb)

        # Clamp container to restrict max width when maximized
        clamp = Adw.Clamp()
        clamp.set_maximum_size(700)
        clamp.set_tightening_threshold(500)

        inner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        clamp.set_child(inner_box)
        main_box.append(clamp)

        # Branding
        brand = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        brand.set_margin_top(16)
        brand.set_margin_start(24)
        brand.set_margin_end(24)
        t = Gtk.Label(label="LinyGUI")
        t.add_css_class("app-title")
        brand.append(t)
        s = Gtk.Label(label="Elegant Image Compression")
        s.add_css_class("app-subtitle")
        brand.append(s)
        inner_box.append(brand)

        # Tabs
        tab_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        tab_box.set_halign(Gtk.Align.CENTER)
        tab_box.set_margin_top(16)
        tab_box.set_margin_bottom(12)
        tab_box.add_css_class("tab-switcher")

        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self._stack.set_transition_duration(200)
        self._stack.set_vexpand(True)
        self._stack.set_vhomogeneous(True)
        self._stack.set_hhomogeneous(True)
        self._stack.set_margin_start(24)
        self._stack.set_margin_end(24)
        self._stack.set_margin_bottom(16)

        tabs = [
            ("compress", "Compress", self._build_compress_tab),
            ("resize", "Smart Resize", self._build_resize_tab),
            ("settings", "Settings", self._build_settings_tab),
        ]

        self._tab_buttons = []
        for tid, label, builder in tabs:
            btn = Gtk.ToggleButton(label=label)
            btn.add_css_class("tab-button")
            btn.set_hexpand(True)
            btn.connect("toggled", self._on_tab, tid)
            tab_box.append(btn)
            self._tab_buttons.append((btn, tid))
            self._stack.add_named(builder(), tid)

        for i in range(1, len(self._tab_buttons)):
            self._tab_buttons[i][0].set_group(self._tab_buttons[0][0])

        inner_box.append(tab_box)
        inner_box.append(self._stack)

        # Footer
        ft = Gtk.Label(label="v1.0.0 · DevOpsInquisitor")
        ft.add_css_class("footer-text")
        ft.set_margin_bottom(12)
        inner_box.append(ft)

        self.set_content(main_box)
        self._tab_buttons[0][0].set_active(True)

        # Show settings if no API key
        if not self._settings.get("api_key"):
            GLib.idle_add(lambda: self._tab_buttons[2][0].set_active(True))

    def _on_tab(self, btn, tid):
        if btn.get_active():
            self._stack.set_visible_child_name(tid)

    # ── Compress Tab ──────────────────────────────────────────────

    def _build_compress_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Drop zone
        drop = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        drop.set_valign(Gtk.Align.CENTER)
        drop.set_halign(Gtk.Align.FILL)
        drop.set_vexpand(True)
        drop.add_css_class("drop-zone")
        drop.set_size_request(-1, 240)

        # Icon
        if os.path.exists(self._icon_path):
            pb = GdkPixbuf.Pixbuf.new_from_file_at_scale(self._icon_path, 80, 80, True)
            tex = Gdk.Texture.new_for_pixbuf(pb)
            img = Gtk.Image.new_from_paintable(tex)
            img.set_pixel_size(80)
            img.add_css_class("drop-zone-icon-img")
            drop.append(img)
        else:
            ic = Gtk.Label(label="⬦")
            ic.add_css_class("drop-zone-icon")
            drop.append(ic)

        lbl = Gtk.Label(label="Drop Images Here")
        lbl.add_css_class("drop-zone-text")
        drop.append(lbl)

        hint = Gtk.Label(label="PNG · JPEG · WebP  —  or click to browse")
        hint.add_css_class("drop-zone-hint")
        drop.append(hint)

        # DnD — use DropTargetAsync for maximum compatibility
        dt = Gtk.DropTarget.new(Gdk.FileList, Gdk.DragAction.COPY)
        dt.connect("drop", self._on_dnd_drop)
        dt.connect("enter", self._on_dnd_enter)
        dt.connect("leave", self._on_dnd_leave)
        drop.add_controller(dt)
        self._drop_zone = drop

        # Click to browse
        click = Gtk.GestureClick.new()
        click.connect("released", lambda g, n, x, y: self._open_chooser())
        drop.add_controller(click)

        box.append(drop)

        # Button
        btn = Gtk.Button(label="Choose Image Files")
        btn.add_css_class("accent-button")
        btn.connect("clicked", lambda b: self._open_chooser())
        box.append(btn)

        # Progress
        self._progress = Gtk.ProgressBar()
        self._progress.set_visible(False)
        box.append(self._progress)

        # Status
        self._status = Gtk.Label(label="")
        self._status.add_css_class("placeholder-sub")
        self._status.set_visible(False)
        self._status.set_wrap(True)
        box.append(self._status)

        return box

    def _on_dnd_enter(self, target, x, y):
        self._drop_zone.add_css_class("drop-zone-active")
        return Gdk.DragAction.COPY

    def _on_dnd_leave(self, target):
        self._drop_zone.remove_css_class("drop-zone-active")

    def _on_dnd_drop(self, target, value, x, y):
        self._drop_zone.remove_css_class("drop-zone-active")
        paths = []
        if isinstance(value, Gdk.FileList):
            for gf in value.get_files():
                p = gf.get_path()
                if p:
                    paths.append(p)
        if paths:
            images = self._scan_for_images(paths)
            if images:
                self._compress_files(images)
            return True
        return False

    # ── File Chooser ──────────────────────────────────────────────

    def _open_chooser(self, resize_opts=None):
        dlg = Gtk.FileChooserNative.new(
            "Choose Images", self, Gtk.FileChooserAction.OPEN, "_Open", "_Cancel"
        )
        dlg.set_select_multiple(True)
        f = Gtk.FileFilter()
        f.set_name("Images (PNG, JPEG, WebP)")
        for mt in ("image/png", "image/jpeg", "image/webp"):
            f.add_mime_type(mt)
        for pat in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
            f.add_pattern(pat)
        dlg.add_filter(f)
        dlg.set_filter(f)
        dlg._resize_opts = resize_opts
        dlg.connect("response", self._on_chooser_done)
        dlg.show()

    def _on_chooser_done(self, dlg, resp):
        if resp == Gtk.ResponseType.ACCEPT:
            paths = []
            files = dlg.get_files()
            for i in range(files.get_n_items()):
                p = files.get_item(i).get_path()
                if p:
                    paths.append(p)
            if paths:
                images = self._scan_for_images(paths)
                if images:
                    opts = getattr(dlg, '_resize_opts', None)
                    self._compress_files(images, resize_opts=opts)
        dlg.destroy()

    # ── Compression Engine ────────────────────────────────────────

    def _is_image(self, path):
        return os.path.splitext(path)[1].lower() in (".png", ".jpg", ".jpeg", ".webp")

    def _scan_for_images(self, paths):
        images = []
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        if self._is_image(f):
                            images.append(os.path.join(root, f))
            elif self._is_image(p):
                images.append(p)
        return images

    def _compress_files(self, paths, resize_opts=None):
        if not TINIFY_AVAILABLE:
            self._show_status(
                "✗ tinify not installed. Run: pip install tinify", True
            )
            return

        key = self._settings.get("api_key", "")
        if not key:
            self._show_status("⚠ Set your API key in Settings first", True)
            return

        self._progress.set_visible(True)
        self._progress.set_fraction(0)
        self._status.set_visible(True)
        self._status.set_label(f"Compressing {len(paths)} image(s)…")
        self._status.remove_css_class("error-text")
        self._status.remove_css_class("result-text")
        self._status.add_css_class("placeholder-sub")

        thread = threading.Thread(
            target=self._worker, args=(paths, key, resize_opts), daemon=True
        )
        thread.start()

    def _worker(self, paths, key, resize_opts):
        try:
            tinify.key = key

            total = len(paths)
            saved_total = 0
            for i, path in enumerate(paths):
                orig_size = os.path.getsize(path)
                source = tinify.from_file(path)

                # Metadata
                metas = []
                if self._settings.get("preserve_copyright"):
                    metas.append("copyright")
                if self._settings.get("preserve_location"):
                    metas.append("location")
                if self._settings.get("preserve_creation"):
                    metas.append("creation")
                if metas:
                    source = source.preserve(*metas)

                # Resize
                if resize_opts:
                    source = source.resize(**resize_opts)

                # Output path
                if self._settings.get("replace_original"):
                    out = path
                else:
                    base, ext = os.path.splitext(path)
                    out = f"{base}-min{ext}"

                source.to_file(out)
                new_size = os.path.getsize(out)
                saved_total += orig_size - new_size

                frac = (i + 1) / total
                GLib.idle_add(self._on_progress, frac, i + 1, total)

            saved_kb = saved_total / 1024
            msg = f"✓ {total} image(s) compressed · Saved {saved_kb:.1f} KB"
            GLib.idle_add(self._show_status, msg, False)

        except tinify.AccountError as e:
            GLib.idle_add(self._show_status, f"✗ API key error: {e}", True)
        except tinify.ClientError as e:
            GLib.idle_add(self._show_status, f"✗ Bad request: {e}", True)
        except tinify.ServerError as e:
            GLib.idle_add(self._show_status, f"✗ Server error: {e}", True)
        except tinify.ConnectionError as e:
            GLib.idle_add(self._show_status, f"✗ Network error: {e}", True)
        except Exception as e:
            GLib.idle_add(self._show_status, f"✗ {e}", True)

    def _on_progress(self, frac, done, total):
        self._progress.set_fraction(frac)
        self._status.set_label(f"Compressing… {done}/{total}")

    def _show_status(self, msg, is_error=False):
        self._progress.set_visible(False)
        self._status.set_visible(True)
        self._status.set_label(msg)
        self._status.remove_css_class("result-text")
        self._status.remove_css_class("error-text")
        self._status.remove_css_class("placeholder-sub")
        self._status.add_css_class("error-text" if is_error else "result-text")

    # ── Smart Resize Tab ──────────────────────────────────────────

    def _build_resize_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)

        # Mode selector
        mb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        mb.set_halign(Gtk.Align.START)
        mb.add_css_class("tab-switcher")

        self._resize_mode = "scale"
        self._mode_btns = []
        for mid, mlabel in [("scale","Scale"),("fit","Fit"),("cover","Cover"),("thumb","Thumb")]:
            b = Gtk.ToggleButton(label=mlabel)
            b.add_css_class("mode-button")
            b.connect("toggled", self._on_mode, mid)
            mb.append(b)
            self._mode_btns.append((b, mid))
        for i in range(1, len(self._mode_btns)):
            self._mode_btns[i][0].set_group(self._mode_btns[0][0])
        box.append(mb)

        # Dimensions
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(8)

        for col, label, attr in [(0, "Width:", "_w_entry"), (2, "Height:", "_h_entry")]:
            l = Gtk.Label(label=label)
            l.add_css_class("settings-label")
            l.set_halign(Gtk.Align.START)
            grid.attach(l, col, 0, 1, 1)
            e = Gtk.Entry()
            e.set_placeholder_text("px")
            e.add_css_class("glass-entry")
            e.set_hexpand(True)
            grid.attach(e, col + 1, 0, 1, 1)
            setattr(self, attr, e)
        box.append(grid)

        # Description
        self._rdesc = Gtk.Label()
        self._rdesc.set_wrap(True)
        self._rdesc.set_max_width_chars(50)
        self._rdesc.add_css_class("settings-description")
        self._rdesc.set_halign(Gtk.Align.START)
        self._rdesc.set_margin_top(4)
        box.append(self._rdesc)

        # Button
        rb = Gtk.Button(label="Choose Files & Resize")
        rb.add_css_class("accent-button")
        rb.connect("clicked", self._on_resize)
        box.append(rb)

        self._mode_btns[0][0].set_active(True)
        return box

    def _on_mode(self, btn, mid):
        if btn.get_active():
            self._resize_mode = mid
            descs = {
                "scale": "Proportionally scale down. Provide width OR height.",
                "fit": "Scale to fit within dimensions. Provide both.",
                "cover": "Crop to exact dimensions. Smart area detection.",
                "thumb": "Intelligent thumbnail. Detects main subject.",
            }
            self._rdesc.set_label(descs.get(mid, ""))

    def _on_resize(self, btn):
        w = self._w_entry.get_text().strip()
        h = self._h_entry.get_text().strip()
        wi = int(w) if w.isdigit() else 0
        hi = int(h) if h.isdigit() else 0
        m = self._resize_mode

        if m == "scale" and wi == 0 and hi == 0:
            self._show_status("Enter width or height", True)
            return
        if m in ("fit", "cover", "thumb") and (wi == 0 or hi == 0):
            self._show_status("Enter both width and height", True)
            return

        opts = {"method": m}
        if m == "scale":
            opts["width" if wi > 0 else "height"] = wi or hi
        else:
            opts["width"] = wi
            opts["height"] = hi

        self._open_chooser(resize_opts=opts)

    # ── Settings Tab ──────────────────────────────────────────────

    def _build_settings_tab(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        # Tinify status banner
        if not TINIFY_AVAILABLE:
            warn = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            warn.add_css_class("settings-row")
            wl = Gtk.Label(label="⚠ tinify module not installed")
            wl.add_css_class("error-text")
            wl.set_halign(Gtk.Align.START)
            warn.append(wl)
            cmd = Gtk.Label(label="Run: pip install tinify")
            cmd.add_css_class("settings-description")
            cmd.set_halign(Gtk.Align.START)
            warn.append(cmd)
            box.append(warn)

        # API Key
        kr = self._row("API Key", "Free at tinypng.com/developers")
        self._key_entry = Gtk.PasswordEntry()
        self._key_entry.set_show_peek_icon(True)
        self._key_entry.set_hexpand(True)
        self._key_entry.add_css_class("glass-entry")
        self._key_entry.set_text(self._settings.get("api_key", ""))
        self._key_entry.connect("changed", lambda e: self._set("api_key", e.get_text()))
        kr.append(self._key_entry)
        box.append(kr)

        # Replace original
        rr = self._row("Replace Original", "Overwrite source files")
        sw = Gtk.Switch()
        sw.set_active(self._settings.get("replace_original", False))
        sw.set_valign(Gtk.Align.CENTER)
        sw.connect("state-set", lambda w, s: self._set("replace_original", s))
        rr.append(sw)
        box.append(rr)

        # Metadata header
        ml = Gtk.Label(label="Preserve Metadata")
        ml.set_halign(Gtk.Align.START)
        ml.add_css_class("settings-label")
        ml.set_margin_top(8)
        box.append(ml)

        for key, title, desc in [
            ("preserve_copyright", "Copyright", "EXIF/XMP copyright"),
            ("preserve_location", "Location", "GPS coordinates"),
            ("preserve_creation", "Creation Date", "Capture timestamp"),
        ]:
            r = self._row(title, desc)
            sw = Gtk.Switch()
            sw.set_active(self._settings.get(key, False))
            sw.set_valign(Gtk.Align.CENTER)
            sw.connect("state-set", lambda w, s, k=key: self._set(k, s))
            r.append(sw)
            box.append(r)

        return box

    def _row(self, title, desc):
        r = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        r.add_css_class("settings-row")
        tb = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        tb.set_hexpand(True)
        t = Gtk.Label(label=title)
        t.set_halign(Gtk.Align.START)
        t.add_css_class("settings-label")
        tb.append(t)
        d = Gtk.Label(label=desc)
        d.set_halign(Gtk.Align.START)
        d.add_css_class("settings-description")
        tb.append(d)
        r.append(tb)
        return r

    def _set(self, key, val):
        self._settings[key] = val
        self._save_settings()
