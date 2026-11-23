#!/usr/bin/env python3
"""Rebuilds gen/data/ on this machine. Never runs in CI: the daily build only reads what this writes.

    fonts     Geist Mono as outlines, because an SVG inside an <img> can't count on loading a font
    shots     the four screenshots, cut down to what the Atom panel can show
    palettes  their wallpapers through Atom Plasma's own palette engine (as the desktop computed them)
    libt      a real `libt all` run of the tester against the real libft

Usage: python3 gen/make_data.py fonts shots palettes libt
"""
import importlib.util
import io
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
ASSETS = HERE.parent / "assets"
RICE = pathlib.Path.home() / ".config/plasma-rice"
TESTER = pathlib.Path.home() / "Projects/42/Libft_Tester"
LIBFT = pathlib.Path.home() / "Projects/42/Libft/src"

GEIST = "https://cdn.jsdelivr.net/fontsource/fonts/geist-mono@5.3.0/latin-{}-normal.ttf"
FACES = {"m400": 400, "m500": 500}
CHARS = "".join(map(chr, range(32, 127))) + "·—°"

SHOTS = ("desktop", "home", "theme", "stats")
SHOT_WIDTH = 1024       # ~2x the ~515 px rendered width on GitHub; keeps all four shots well under 500 KB
SHOT_QUALITY = 74
# what each screenshot was taken on: the three monitors of my "prof" theme (main 1440p Torii gates, laptop neon
# waves, 4K Mt. Fuji), taken in a nested Plasma (Atom Plasma's tools/nested/) with nothing of mine on them:
# desktop + Claude usage widget, Atom's orbital launcher, the redesigned Theme page and the live System meters
WALLPAPERS = {
    "desktop": pathlib.Path.home() / "Pictures/Wallpapers/wallhaven-k88z5m.jpg",
    "home": pathlib.Path.home() / "Pictures/Wallpapers/wallhaven-3z91ey.jpg",
    "theme": pathlib.Path.home() / "Pictures/Wallpapers/wallhaven-5ymyz7.jpg",
    "stats": pathlib.Path.home() / "Pictures/Wallpapers/wallhaven-3z91ey.jpg",
}
# per-screen colour overrides from "prof" (~/.local/state/rice/overrides.json) so palettes() matches what's on screen
OVERRIDES = {
    "desktop": {"intensity": 1.0, "primary": "#a62323", "secondary": "#8fa033", "tertiary": "#828282", "mood": "soft"},
}
# what the panel prints as a palette, darkest to lightest, by the engine's names
RAMP = ("background", "surface_high", "primary_dim", "tertiary", "primary", "secondary")


def fonts():
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont

    out = {}
    for name, weight in FACES.items():
        request = urllib.request.Request(GEIST.format(weight), headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=30) as reply:
            font = TTFont(io.BytesIO(reply.read()))
        k = 1000 / font["head"].unitsPerEm
        cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
        adv, outline = {}, {}
        for ch in CHARS:
            g = cmap[ord(ch)]
            adv[ch] = round(hmtx[g][0] * k)
            pen = SVGPathPen(glyphs, ntos=lambda v: str(round(v)))
            glyphs[g].draw(TransformPen(pen, (k, 0, 0, -k, 0, 0)))      # y down, like SVG
            if pen.getCommands():
                outline[ch] = _relative(pen.getCommands())
        out[name] = {"adv": adv, "d": outline}
    DATA.mkdir(exist_ok=True)
    (DATA / "glyphs.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("glyphs.json", (DATA / "glyphs.json").stat().st_size // 1024, "KB")


def _relative(d):
    """An absolute path rewritten in relative commands, which is about a third shorter."""
    arity = {"M": 2, "L": 2, "H": 1, "V": 1, "Q": 4, "C": 6}
    out, x, y, sx, sy = "", 0, 0, 0, 0
    for cmd, args in re.findall(r"([MLHVQCZ])([^MLHVQCZ]*)", d):
        nums = [int(n) for n in re.findall(r"-?\d+", args)]
        if cmd == "Z":
            out += "z"
            x, y = sx, sy
            continue
        for i in range(0, len(nums), arity[cmd]):
            part = nums[i:i + arity[cmd]]
            if cmd == "H":
                rel, x = [part[0] - x], part[0]
            elif cmd == "V":
                rel, y = [part[0] - y], part[0]
            else:
                rel = [v - (y if j % 2 else x) for j, v in enumerate(part)]
                x, y = part[-2], part[-1]
            if cmd == "M" and i:
                out += "l" + _join(rel)                  # pairs after a move are implied lines
            elif cmd == "M" and not out:
                out += "M" + _join(part)                 # the outline's start stays absolute
            else:
                out += cmd.lower() + _join(rel)
            if cmd == "M" and not i:
                sx, sy = x, y
    return out


def _join(nums):
    text = str(nums[0])
    for n in nums[1:]:
        text += (" " if n >= 0 else "") + str(n)
    return text


def shots():
    from PIL import Image
    for name in SHOTS:
        path = ASSETS / f"atom-{name}.webp"
        with Image.open(path) as image:
            if image.width > SHOT_WIDTH:
                image = image.convert("RGB").resize((SHOT_WIDTH, image.height * SHOT_WIDTH // image.width), Image.LANCZOS)
                image.save(path, "WEBP", quality=SHOT_QUALITY, method=6)
        print(path.name, path.stat().st_size // 1024, "KB")


def palettes():
    """Each screenshot's wallpaper through the very function that coloured the desktop in it (Atom Plasma's
    palette_for, with my settings), so the swatches are the colours on screen. Without the wallpaper on this
    machine, the screenshot itself goes through the engine instead."""
    sys.path.insert(0, str(RICE))
    from atom import util
    from atom.walls import palette_for
    out = {}
    for name in SHOTS:
        source = WALLPAPERS.get(name)
        if not source or not source.is_file():
            print(f"{name}: no {source}, using the screenshot")
            source = ASSETS / f"atom-{name}.webp"
        colours = palette_for(source, util.settings(), OVERRIDES.get(name))
        out[name] = [colours[key] for key in RAMP]
    (DATA / "palettes.json").write_text(json.dumps(out, indent=1))
    print(out)


def libt():
    """A real run of the tester on the real libft, from a clean copy so the tester's own folder stays as it is."""
    with tempfile.TemporaryDirectory() as tmp:
        files = subprocess.run(["git", "ls-files", "-z"], cwd=TESTER, capture_output=True, text=True, check=True)
        for name in filter(None, files.stdout.split("\0")):
            target = pathlib.Path(tmp, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(TESTER / name, target)
        run = subprocess.run([f"{tmp}/libt.sh", "all"], cwd=LIBFT, capture_output=True, text=True, timeout=300)
    if run.returncode:
        sys.exit(f"libt failed:\n{run.stdout}{run.stderr}")
    text = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", run.stdout).replace(str(LIBFT), "~/libft")
    (DATA / "libt-run.txt").write_text(text)
    print(text.splitlines()[-1])


if __name__ == "__main__":
    for step in sys.argv[1:]:
        globals()[step]()
