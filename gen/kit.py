"""The drawing kit every image shares.

The rules come from where these SVGs end up, inside an <img> on GitHub:

  * No fonts, scripts, links, hover or external files. Text is drawn from gen/data/glyphs.json and anything
    clickable is its own image in the README.
  * An animated SVG in an <img> repaints whole on any change, so motion has to earn it. Everything that runs
    forever shares a 10 fps grid (steps(), never linear), so the browser paints ten times a second and not
    sixty. Between moves a value must not change at all, even out of sight. No filters, no group opacity.
  * The CSS without animations is the finished picture. Animations only borrow from it, so a visitor who asked
    for reduced motion gets the whole thing as a still, and nothing depends on when an image scrolled into view.
  * Everything hangs off one dot grid, the way Oblivion's interfaces did, and every number shown is real.
"""
import json
import pathlib

DATA = pathlib.Path(__file__).resolve().parent / "data"
FONTS = json.loads((DATA / "glyphs.json").read_text(encoding="utf-8"))

VOID = "#08090b"        # the panel
LINE = "#1e2326"        # hairlines
FAINT = "#2c3235"       # what has to be seen, but not noticed
DIM = "#7f8783"         # labels
INK = "#e8ebe6"         # values
SIG = "#c6ff3d"         # the one signal colour

WIDTH = 1000            # every panel; GitHub's column shows it at about 830 px
CUT = 18                # the chamfer on every panel's top right corner
GRID = 50
FPS = 10


def num(v):
    """Shortest honest spelling of a number: 12, 3.5, -.25."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        return "0"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


def px(v):
    return num(v) + "px"


class Svg:
    def __init__(self, h, title, desc="", w=WIDTH):
        self.w, self.h, self.title, self.desc = w, h, title, desc
        self.css, self.defs, self.parts = [], [], []
        self.glyphs = {}
        self.ids = 0

    def add(self, *parts):
        self.parts.extend(parts)

    def uid(self):
        self.ids += 1
        return f"i{self.ids}"

    def _glyph(self, face, ch):
        key = (face, ch)
        if key not in self.glyphs:
            self.glyphs[key] = f"g{len(self.glyphs)}"
            self.defs.append(f'<path id="{self.glyphs[key]}" d="{FONTS[face]["d"][ch]}"/>')
        return self.glyphs[key]

    def text(self, s, x, y, size, fill=INK, face="m400", anchor="start", track=0, attrs=""):
        """One line of outlined text, its baseline at y. track is extra space in px per letter."""
        font = FONTS[face]
        k = size / 1000
        pen, uses = 0, []
        for ch in s:
            if ch in font["d"]:
                uses.append(f'<use href="#{self._glyph(face, ch)}" x="{round(pen)}"/>')
            pen += font["adv"][ch] + track / k
        if anchor != "start":
            x -= (pen - track / k) * k * (.5 if anchor == "middle" else 1)
        return f'<g fill="{fill}" transform="translate({num(x)} {num(y)}) scale({k:.4f})"{attrs}>{"".join(uses)}</g>'

    def label(self, s, x, y, fill=DIM, size=11, anchor="start", attrs=""):
        """The panel's voice: small, tracked capitals."""
        return self.text(s, x, y, size, fill, anchor=anchor, track=size * .13, attrs=attrs)

    def linear(self, stops, x1=0, y1=0, x2=0, y2=1):
        return self._gradient("linearGradient", f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"', stops)

    def radial(self, stops):
        return self._gradient("radialGradient", 'cx=".5" cy=".5" r=".5"', stops)

    def _gradient(self, tag, geometry, stops):
        i = self.uid()
        body = "".join(f'<stop offset="{num(o)}" stop-color="{c}"' + (f' stop-opacity="{num(a[0])}"' if a else "") + "/>"
                       for o, c, *a in stops)
        self.defs.append(f"<{tag} id=\"{i}\" {geometry}>{body}</{tag}>")
        return i

    def render(self):
        css = "".join(self.css) + "@media(prefers-reduced-motion:reduce){*{animation:none!important}}"
        desc = f"<desc>{self.desc}</desc>" if self.desc else ""
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" role="img" aria-label="{self.title}"><title>{self.title}</title>{desc}'
                f"<style>{css}</style><defs>{''.join(self.defs)}</defs>{''.join(self.parts)}</svg>\n")


def dots(x1, y1, x2, y2, colour=LINE, step=GRID):
    """The grid everything hangs off. Small squares, filled: round dots are a third of what Firefox spends here."""
    d = "".join(f"M{x} {y}h1.4v1.4h-1.4z" for y in range(y1, y2 + 1, step) for x in range(x1, x2 + 1, step))
    return f'<path d="{d}" fill="{colour}"/>'


def plate(s, code=None, title=None, note=None):
    """Every panel's body: the void, a hairline and a cut corner, then its address and name on the top line."""
    w, h = s.w, s.h
    s.add(f'<path d="M.5 .5H{w - CUT}L{w - .5} {CUT}V{h - .5}H.5Z" fill="{VOID}" stroke="{LINE}"/>')
    if code:
        s.add(s.label(code, 24, 33, SIG), s.label(title, 74, 33, INK))
    if note:
        s.add(s.label(note, w - 30, 33, DIM, anchor="end"))


def arrow(x, y, colour=DIM, size=7):
    """Top right corner at x, y: this panel opens something."""
    return (f'<path d="M{num(x - size)} {num(y + size)}L{num(x)} {num(y)}M{num(x - size + 1)} {num(y)}H{num(x)}V{num(y + size - 1)}" '
            f'fill="none" stroke="{colour}" stroke-width="1.2"/>')


def sigil(x, y, h=14):
    """42 in binary, 101010, as six bars: the mark on every panel."""
    out = ""
    for i in range(6):
        bit = not i % 2
        top = y if bit else y + h * .55
        out += (f'<rect x="{num(x + i * h * .36)}" y="{num(top)}" width="{num(h * .2)}" '
                f'height="{num(y + h - top)}" fill="{SIG if bit else FAINT}"/>')
    return out
