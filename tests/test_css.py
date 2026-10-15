import os
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

from deepwick_spec.check_port import check_port
from deepwick_spec.palette import load_palette

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = PALETTE.colors
LIBADWAITA = Path("/usr/lib64/libadwaita-1.so.0")
NOT_SET = {"--border-color"}
SHADE = re.compile(r"rgb\(0 0 0 / \d{1,2}%\)")
EXPECTED = {
    "--accent-bg-color": "blue", "--accent-fg-color": "background", "--accent-color": "blue",
    "--destructive-bg-color": "red", "--destructive-fg-color": "background", "--destructive-color": "red",
    "--success-bg-color": "green", "--success-fg-color": "background", "--success-color": "green",
    "--warning-bg-color": "yellow", "--warning-fg-color": "background", "--warning-color": "yellow",
    "--error-bg-color": "red", "--error-fg-color": "background", "--error-color": "red",
    "--window-bg-color": "background", "--window-fg-color": "foreground",
    "--view-bg-color": "background", "--view-fg-color": "foreground",
    "--headerbar-bg-color": "surface", "--headerbar-fg-color": "foreground",
    "--headerbar-border-color": "overlay", "--headerbar-backdrop-color": "surface",
    "--sidebar-bg-color": "surface", "--sidebar-fg-color": "foreground",
    "--sidebar-backdrop-color": "surface", "--sidebar-border-color": "overlay",
    "--secondary-sidebar-bg-color": "surface", "--secondary-sidebar-fg-color": "foreground",
    "--secondary-sidebar-backdrop-color": "surface", "--secondary-sidebar-border-color": "overlay",
    "--card-bg-color": "surface", "--card-fg-color": "foreground",
    "--thumbnail-bg-color": "surface", "--thumbnail-fg-color": "foreground",
    "--overview-bg-color": "surface", "--overview-fg-color": "foreground",
    "--active-toggle-bg-color": "overlay", "--active-toggle-fg-color": "foreground",
    "--dialog-bg-color": "surface", "--dialog-fg-color": "foreground",
    "--popover-bg-color": "surface", "--popover-fg-color": "foreground",
    "--scrollbar-outline-color": "background", "--banner-color": "blue",
}
SHADES = {
    "--shade-color", "--headerbar-shade-color", "--headerbar-darker-shade-color",
    "--sidebar-shade-color", "--secondary-sidebar-shade-color", "--card-shade-color",
    "--popover-shade-color",
}


def variables():
    text = (REPO / "deepwick.css").read_text(encoding="utf-8")
    root = re.search(r":root\s*\{(.*?)\}", text, re.S)
    assert root, "no :root block"
    return dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", root.group(1)))


def test_named_variables():
    v = variables()
    for name, color in EXPECTED.items():
        assert v.get(name, "").lower() == C[color].lower(), f"{name}: {v.get(name)} != {color}"


def test_shades_are_translucent_black():
    v = variables()
    for name in SHADES:
        assert SHADE.fullmatch(v.get(name, "")), f"{name}: {v.get(name)}"


def test_no_unexpected_variables():
    assert set(variables()) == set(EXPECTED) | SHADES


@pytest.mark.skipif(not (LIBADWAITA.exists() and shutil.which("gresource")), reason="needs libadwaita and gresource")
def test_variables_match_libadwaita():
    css = subprocess.run(
        ["gresource", "extract", str(LIBADWAITA), "/org/gnome/Adwaita/styles/gtk.css"],
        capture_output=True, text=True, check=True,
    ).stdout
    live = set(re.findall(r"(?<![\w-])(--[a-z][a-z0-9-]*-color)\s*:", css)) - NOT_SET
    assert live == set(variables()), f"missing {live - set(variables())}, stale {set(variables()) - live}"


def test_selection_rule():
    text = (REPO / "deepwick.css").read_text(encoding="utf-8")
    assert re.search(r"selection\s*\{[^}]*background-color:\s*" + re.escape(C["selection"]), text, re.I)


def test_readme_appends_import():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert re.search(r">>\s*\"?\$\{XDG_CONFIG_HOME:-\$HOME/\.config\}/gtk-4\.0/gtk\.css", readme)
    assert not re.search(r"(?<!>)>\s*\"?\$\{XDG_CONFIG_HOME:-\$HOME/\.config\}/gtk-4\.0/gtk\.css", readme)


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []


VSHOT = REPO.parent / "tools" / "vshot"
needs_vshot = pytest.mark.skipif(
    not (VSHOT.is_file() and shutil.which("kwin_wayland") and shutil.which("spectacle") and shutil.which("magick")),
    reason="needs tools/vshot, kwin_wayland, spectacle and ImageMagick",
)


def vshot(base, *cmd, **env):
    """Run cmd off-screen with SHOT_XDG=base; return the screenshot's color histogram."""
    out = base / "shot.png"
    subprocess.run(
        [str(VSHOT), str(out), "--", *cmd],
        env={**os.environ, "SHOT_XDG": str(base), **env},
        check=True,
        timeout=120,
    )
    hist = subprocess.run(
        ["magick", str(out), "-alpha", "off", "-format", "%c", "histogram:info:-"],
        capture_output=True, text=True, check=True,
    ).stdout
    counts = Counter()
    for m in re.finditer(r"^\s*(\d+):.*?#([0-9A-Fa-f]{6})", hist, re.M):
        counts["#" + m.group(2).lower()] += int(m.group(1))
    return counts


def px(counts, name):
    return counts[PALETTE.colors[name].lower()]


def demo(base, install, scheme="prefer-dark"):
    gtk = base / "config" / "gtk-4.0"
    gtk.mkdir(parents=True)
    if install:
        shutil.copy(REPO / "deepwick.css", gtk)
        (gtk / "gtk.css").write_text("@import 'deepwick.css';\n")
    return vshot(
        base, "adwaita-1-demo",
        GSETTINGS_BACKEND="memory", ADW_DEBUG_COLOR_SCHEME=scheme, ADW_DEBUG_ACCENT_COLOR="blue",
    )


needs_demo = pytest.mark.skipif(not shutil.which("adwaita-1-demo"), reason="needs adwaita-1-demo")


@needs_vshot
@needs_demo
def test_render(tmp_path):
    counts = demo(tmp_path, install=True)
    assert px(counts, "background") > 20000
    assert px(counts, "surface") > 5000


@needs_vshot
@needs_demo
def test_render_in_light_mode(tmp_path):
    counts = demo(tmp_path, install=True, scheme="prefer-light")
    assert px(counts, "background") > 20000
    assert px(counts, "surface") > 5000


@needs_vshot
@needs_demo
def test_render_without_css_is_not_deepwick(tmp_path):
    counts = demo(tmp_path, install=False)
    assert px(counts, "background") < 500
