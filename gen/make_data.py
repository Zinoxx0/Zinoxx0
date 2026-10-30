#!/usr/bin/env python3
"""Rebuilds gen/data/ on this machine. Never runs in CI: the daily build only reads what this writes.

    fonts     Inter and JetBrains Mono (the rice's two fonts) as outlines, because an SVG inside an
              <img> can't count on loading a font
    icons     the dock's tech icons, the contact icons and the 42 mark
    palettes  every knot of the day through Atom Plasma's own palette engine (needs dist/hero.svg)
    libt      a real `libt all` run of the tester against the real libft

Usage: python3 gen/make_data.py fonts icons palettes libt
"""
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data"
INTER = "/usr/share/fonts/inter/InterVariable.ttf"
MONO = "/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-{}.ttf"
RICE = pathlib.Path.home() / ".config/plasma-rice"
TESTER = pathlib.Path.home() / "Projects/42/Libft_Tester"
LIBFT = pathlib.Path.home() / "Projects/42/Libft/src"
CHARS = "".join(map(chr, range(32, 127))) + "·—–→✓✗°…↗"

# name: (file, variable axes). The d* faces are Inter's display cut, the t* faces its text cut.
FACES = {
    "d300": (INTER, {"opsz": 32, "wght": 300}),
    "d800": (INTER, {"opsz": 32, "wght": 800}),
    "t400": (INTER, {"opsz": 14, "wght": 400}),
    "t500": (INTER, {"opsz": 14, "wght": 500}),
    "t600": (INTER, {"opsz": 14, "wght": 600}),
    "m400": (MONO.format("Regular"), None),
    "m700": (MONO.format("Bold"), None),
}


def fonts():
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    out = {}
    for name, (path, axes) in FACES.items():
        font = TTFont(path)
        if axes:
            font = instancer.instantiateVariableFont(font, axes)
        k = 1000 / font["head"].unitsPerEm
        cmap, glyphs, hmtx = font.getBestCmap(), font.getGlyphSet(), font["hmtx"]
        adv, outline = {}, {}
        for ch in CHARS:
            g = cmap[ord(ch)]
            adv[ch] = round(hmtx[g][0] * k)
            pen = SVGPathPen(glyphs, ntos=lambda v: str(round(v)))
            glyphs[g].draw(TransformPen(pen, (k, 0, 0, -k, 0, 0)))     # y down, like SVG
            if pen.getCommands():
                outline[ch] = _relative(pen.getCommands())
        out[name] = {"adv": adv, "d": outline, "kern": _kerning(font, cmap, k),
                     "cap": round(font["OS/2"].sCapHeight * k), "x": round(font["OS/2"].sxHeight * k)}
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


def _kerning(font, cmap, k):
    """Non-zero pair kerning over CHARS, read from the font's GPOS 'kern' lookups."""
    if "GPOS" not in font:
        return {}
    gpos = font["GPOS"].table
    lookups = sorted({i for r in gpos.FeatureList.FeatureRecord if r.FeatureTag == "kern"
                      for i in r.Feature.LookupListIndex})
    names = {c: cmap[ord(c)] for c in CHARS if c != " "}
    pairs = {}
    for i in lookups:
        for st in gpos.LookupList.Lookup[i].SubTable:
            st = getattr(st, "ExtSubTable", st)
            if st.LookupType != 2:
                continue
            cov = st.Coverage.glyphs
            for a, an in names.items():
                if an not in cov:
                    continue
                for b, bn in names.items():
                    if a + b in pairs:
                        continue
                    v = _pair(st, cov.index(an), an, bn)
                    if v is not None:
                        pairs[a + b] = v            # first subtable that knows the pair wins, as in shaping
    return {p: round(v * k) for p, v in pairs.items() if round(v * k)}


def _pair(st, index, an, bn):
    if st.Format == 1:
        for rec in st.PairSet[index].PairValueRecord:
            if rec.SecondGlyph == bn:
                return getattr(rec.Value1, "XAdvance", 0) or 0
        return None
    c1 = st.ClassDef1.classDefs.get(an, 0)
    c2 = st.ClassDef2.classDefs.get(bn, 0)
    return getattr(st.Class1Record[c1].Class2Record[c2].Value1, "XAdvance", 0) or 0


# the dock's icons, by file name in tandpfun/skill-icons (MIT)
SKILLS = {"c": "C", "cpp": "CPP", "py": "Python-Dark", "qt": "QT-Dark", "js": "JavaScript", "bash": "Bash-Dark",
          "linux": "Linux-Dark", "git": "Git", "ps": "Photoshop", "ae": "AfterEffects"}
BRANDS = ("instagram", "steam")          # from simple-icons (CC0)


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode()


def icons():
    out = {"skills": {}, "brands": {}}
    for key, name in SKILLS.items():
        svg = _get(f"https://raw.githubusercontent.com/tandpfun/skill-icons/main/icons/{name}.svg")
        body = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", svg, flags=re.S).strip()
        # ids must stay unique once the icons share one file
        for i in set(re.findall(r'id="([^"]+)"', body)):
            body = re.sub(rf'(id="|#){re.escape(i)}\b', lambda m: f"{m.group(1)}{key}-{i}", body)
        out["skills"][key] = body
    for name in BRANDS:
        svg = _get(f"https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons/{name}.svg")
        out["brands"][name] = re.search(r'<path d="([^"]+)"', svg).group(1)
    logo = _get("https://upload.wikimedia.org/wikipedia/commons/8/8d/42_Logo.svg")
    # the official mark's polygons, in its own 960 box
    out["mark42"] = [" ".join(p.split()) for p in re.findall(r'<polygon[^>]*points="([^"]+)"', logo)]
    (DATA / "icons.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print("icons.json", (DATA / "icons.json").stat().st_size // 1024, "KB")
    for key, body in out["skills"].items():
        print(key, len(body))


def palettes():
    """The hero's wallpaper at every knot of the day, through Atom Plasma's own palette engine."""
    sys.path.insert(0, str(HERE))
    import importlib.util
    import draw
    import scene
    spec = importlib.util.spec_from_file_location("palette", RICE / "atom/palette.py")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    svg = scene.hero(("07:00", "19:00"), {"phase": .3, "name": ""}, desktop=False)
    out = {"primary": [], "secondary": [], "tertiary": [], "mood": []}
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        for knot in range(draw.KNOTS):
            t = knot * draw.CYCLE / draw.KNOTS
            page, png = tmp / f"{knot}.html", tmp / f"{knot}.png"
            page.write_text(f"<!doctype html><style>*{{animation-play-state:paused!important;"
                            f"animation-delay:-{t}s!important}}</style><body style=margin:0>{svg}")
            subprocess.run(["firefox", "--headless", "--no-remote", "--profile", str(tmp), "--window-size=1280,540",
                            "--screenshot", str(png), f"file://{page}"], capture_output=True, timeout=60, check=True,
                           env={**os.environ, "MOZ_CRASHREPORTER_DISABLE": "1"})
            analysis = engine.analyse(str(png))
            colours = engine.build_v2(analysis)
            for key in ("primary", "secondary", "tertiary"):
                out[key].append(colours[key])
            out["mood"].append(colours["_mood"])
    (DATA / "palettes.json").write_text(json.dumps(out, indent=0))
    print(*zip(out["mood"], out["primary"], out["secondary"], out["tertiary"]), sep="\n")


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
