"""A small libadwaita widget gallery for the Deepwick screenshot. Run: /usr/bin/python3 -I gallery.py"""
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402


def build(app):
    win = Adw.ApplicationWindow(application=app, title="Deepwick", default_width=1000, default_height=640)
    sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
    for name in ("Overview", "Appearance", "Notifications", "About"):
        sidebar.append(Gtk.Label(label=name, xalign=0, margin_start=6, margin_top=6, margin_bottom=6))
    sidebar.select_row(sidebar.get_row_at_index(1))
    page = Adw.PreferencesPage()
    group = Adw.PreferencesGroup(title="Appearance", description="Deep navy, Visual Studio 2022 syntax colors")
    switch = Adw.SwitchRow(title="Dark style", active=True)
    actions = Adw.ActionRow(title="Theme", subtitle="Deepwick")
    actions.add_suffix(Gtk.Button(label="Apply", css_classes=["suggested-action"], valign=Gtk.Align.CENTER))
    actions.add_suffix(Gtk.Button(label="Remove", css_classes=["destructive-action"], valign=Gtk.Align.CENTER))
    entry = Adw.EntryRow(title="Name", text="deepwick")
    progress = Adw.ActionRow(title="Progress")
    progress.add_suffix(Gtk.ProgressBar(fraction=0.6, valign=Gtk.Align.CENTER, width_request=240))
    for row in (switch, actions, entry, progress):
        group.add(row)
    page.add(group)
    split = Adw.NavigationSplitView(
        sidebar=Adw.NavigationPage(title="Deepwick", child=Adw.ToolbarView(content=sidebar)),
        content=Adw.NavigationPage(title="Appearance", child=Adw.ToolbarView(content=page)),
    )
    split.get_sidebar().get_child().add_top_bar(Adw.HeaderBar())
    split.get_content().get_child().add_top_bar(Adw.HeaderBar())
    win.set_content(split)
    win.present()


app = Adw.Application(application_id="dev.deepwick.Gallery")
app.connect("activate", build)
app.run()
