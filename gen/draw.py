"""The drawing kit every image shares: text as outlines, the day clock and obsidian glass.

The rules come from where these SVGs end up, inside an <img> on GitHub:

  * No fonts, scripts, links, hover or embedded images. Text is drawn from gen/data/glyphs.json and
    anything clickable is its own image in the README.
  * Nothing costly per frame. An animated SVG in an <img> can be redrawn whole on every change, and on a
    phone or a laptop on battery that's what you feel. So there are no filters, glows are gradients, and
    fades use inherited fill-opacity and stroke-opacity, because group opacity needs an offscreen layer.
  * Colours that change over the day are custom properties, animated once on the root. Fills, strokes
    and gradient stops only read them. Animating stop-color itself makes Chrome redraw the whole image
    on every display frame, even between steps, which costs twenty times what this does.
  * Everything moves on one 8 fps clock, which is anime "on threes", and colours step slower than that.
    A day is 96 s, cut into 16 knots of 6 s, so all the images tick together.
  * The resting value of anything animated is its value at knot 0, golden hour. That's what a visitor
    who asked for reduced motion gets, as a still.
"""
import json
import pathlib

DATA = pathlib.Path(__file__).resolve().parent / "data"
FONTS = json.loads((DATA / "glyphs.json").read_text(encoding="utf-8"))
ICONS = json.loads((DATA / "icons.json").read_text(encoding="utf-8"))

CYCLE = 96          # seconds in a day
KNOTS = 16          # a day's keyed moments
FPS = 8
PACE = 12           # how many colour steps a knot gets in a card; the hero sets its own


def num(v):
    """Shortest honest spelling of a number: 12, 3.5, -.25."""
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        return "0"
    return s.replace("0.", ".", 1) if s.startswith(("0.", "-0.")) else s


# ---- colour

def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexa(r, g, b):
    return "#" + "".join(f"{max(0, min(255, round(c))):02x}" for c in (r, g, b))


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    c = max(0.0, c)
    return 255 * (12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055)


def _lab(h):
    r, g, b = map(_lin, rgb(h))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def _hex(L, a, b):
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return hexa(_gam(4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s),
                _gam(-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s),
                _gam(-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s))


def mix(a, b, t):
    """a to b in OKLab, so colours between two keys stay clean."""
    return _hex(*(x + (y - x) * t for x, y in zip(_lab(a), _lab(b))))


def timeline(anchors):
    """{knot: value} to a value per knot, easing linearly (and around midnight's wrap) between keys."""
    keys = sorted(anchors)
    out = []
    for k in range(KNOTS):
        a = max((q for q in keys if q <= k), default=keys[-1] - KNOTS)
        b = min((q for q in keys if q > k), default=keys[0] + KNOTS)
        va, vb = anchors[a % KNOTS if a < 0 else a], anchors[b % KNOTS if b >= KNOTS else b]
        t = (k - a) / (b - a)
        if isinstance(va, str):
            out.append(mix(va, vb, t))
        else:
            out.append(va + (vb - va) * t)
    return out


def _palette():
    """Accent colours per knot, as Atom Plasma's palette engine computed them from the hero's frames."""
    path = DATA / "palettes.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {k: [v] * KNOTS for k, v in (("primary", "#90c5e8"), ("secondary", "#a0d1f8"), ("tertiary", "#77b5d0"))}


PALETTE = _palette()


# the classes that follow the page's accents, in whichever image uses them
ACCENTS = {"ap": ("fill", "primary"), "aq": ("fill", "secondary"), "ar": ("fill", "tertiary"),
           "hp": ("stop-color", "primary"), "hr": ("stop-color", "tertiary"), "kp": ("stroke", "primary")}


# ---- one SVG

class Svg:
    def __init__(self, w, h, title, desc="", pace=PACE):
        self.w, self.h, self.title, self.desc, self.pace = w, h, title, desc, pace
        self.css, self.defs, self.parts = [], [], []
        self.colours = {}
        self.glyphs = {}
        self.ids = 0

    def add(self, *parts):
        self.parts.extend(parts)

    def uid(self):
        self.ids += 1
        return f"i{self.ids}"

    def colour(self, cls, prop, name, values):
        """Makes class `cls` paint `prop` with a colour that follows the day, given per knot."""
        if name not in self.colours or f".{cls}{{" not in "".join(self.css):
            self.colours[name] = values
            self.css.append(f".{cls}{{{prop}:var(--{name})}}")

    def clock(self, name, seconds, keys):
        """A looping animation on the clock. keys: [(percent, 'css')], ending at 100."""
        body = ""
        for (p, css), (q, _) in zip(keys, keys[1:]):
            body += f"{num(p)}%{{{css};animation-timing-function:steps({max(1, round((q - p) * seconds * FPS / 100))})}}"
        self.css.append(f"@keyframes {name}{{{body}100%{{{keys[-1][1]}}}}}")
        self.css.append(f".{name}{{animation:{name} {seconds}s infinite}}")

    def day(self, name, props):
        """Class `name` runs css properties {prop: [one value per knot]} over the day."""
        blocks = [";".join(f"{p}:{v[k]}" for p, v in props.items()) for k in range(KNOTS)] + [None]
        blocks[-1] = blocks[0]
        kept = [i for i in range(KNOTS + 1)
                if i in (0, KNOTS) or not blocks[i - 1] == blocks[i] == blocks[i + 1]]
        groups = {}
        for i in kept:
            groups.setdefault(blocks[i], []).append(num(i * 100 / KNOTS) + "%")
        self.css.append(f"@keyframes {name}{{" + "".join(f"{','.join(p)}{{{c}}}" for c, p in groups.items()) + "}")
        self.css.append(f".{name}{{animation:{name} {CYCLE}s steps({self.pace}) infinite}}")

    def linear(self, stops, x1=0, y1=0, x2=0, y2=1, user=False):
        """stops: [(offset, colour[, opacity[, class]])]. Returns the gradient's id."""
        return self._gradient("linearGradient", f'x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"', stops, user)

    def radial(self, stops, cx=.5, cy=.5, r=.5, user=False):
        return self._gradient("radialGradient", f'cx="{cx}" cy="{cy}" r="{r}"', stops, user)

    def _gradient(self, tag, geo, stops, user):
        i = self.uid()
        units = ' gradientUnits="userSpaceOnUse"' if user else ""
        body = ""
        for s in stops:
            offset, colour, opacity, cls = (*s, None, None)[:4]
            a = f' stop-opacity="{num(opacity)}"' if opacity is not None else ""
            c = f' class="{cls}"' if cls else ""
            body += f'<stop offset="{num(offset)}" stop-color="{colour}"{a}{c}/>'
        self.defs.append(f'<{tag} id="{i}" {geo}{units}>{body}</{tag}>')
        return i

    def text(self, s, x, y, size, face="t400", fill="#fff", anchor="start", track=0, cls=None, opacity=None):
        """A line of outlined text with its baseline at y. track is extra space in px per letter."""
        font = FONTS[face]
        k = size / 1000
        pen, uses = 0, []
        for ch, nxt in zip(s, s[1:] + " "):
            if ch in font["d"]:
                key = (face, ch)
                if key not in self.glyphs:
                    gid = f"g{len(self.glyphs)}"
                    self.glyphs[key] = gid
                    self.defs.append(f'<path id="{gid}" d="{font["d"][ch]}"/>')
                uses.append(f'<use href="#{self.glyphs[key]}" x="{round(pen)}"/>')
            pen += font["adv"][ch] + font["kern"].get(ch + nxt, 0) + track / k
        if anchor != "start":
            x -= (pen - track / k) * k * (0.5 if anchor == "middle" else 1)
        attrs = "".join((f' fill="{fill}"' if fill else "",
                         f' class="{cls}"' if cls else "",
                         f' opacity="{num(opacity)}"' if opacity is not None else ""))
        return f'<g{attrs} transform="translate({num(x)} {num(y)}) scale({k:.4f})">{"".join(uses)}</g>'

    def _sky_of_colours(self):
        """The one animation that moves every colour in this image."""
        if not self.colours:
            return ""
        names = list(self.colours)
        head = "".join(f'@property --{n}{{syntax:"&lt;color&gt;";inherits:true;initial-value:{self.colours[n][0]}}}' for n in names)
        rest = ";".join(f"--{n}:{self.colours[n][0]}" for n in names)
        frames = ""
        for k in range(KNOTS + 1):
            at = ";".join(f"--{n}:{self.colours[n][k % KNOTS]}" for n in names)
            frames += f"{num(k * 100 / KNOTS)}%{{{at}}}"
        return f"{head}svg{{{rest};animation:day {CYCLE}s steps({self.pace}) infinite}}@keyframes day{{{frames}}}"

    def render(self):
        markup = "".join(self.defs + self.parts)
        for cls, (prop, key) in ACCENTS.items():
            if f'class="{cls}"' in markup:
                self.colour(cls, prop, key, PALETTE[key])
        css = self._sky_of_colours() + "".join(self.css)
        css += "@media(prefers-reduced-motion:reduce){*{animation:none!important}}"
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" width="{self.w}" '
                f'height="{self.h}" role="img" aria-label="{self.title}"><title>{self.title}</title>'
                + (f"<desc>{self.desc}</desc>" if self.desc else "")
                + f"<style>{css}</style><defs>{''.join(self.defs)}</defs>{''.join(self.parts)}</svg>\n")


def width(s, size, face="t400", track=0):
    font = FONTS[face]
    total = sum(font["adv"][c] + font["kern"].get(c + n, 0) for c, n in zip(s, s[1:] + " "))
    return total * size / 1000 + track * (len(s) - 1)


def rrect(x, y, w, h, r):
    """A rounded rectangle as a path, for shapes that share one path."""
    return (f"M{num(x + r)} {num(y)}h{num(w - 2 * r)}a{num(r)} {num(r)} 0 0 1 {num(r)} {num(r)}v{num(h - 2 * r)}"
            f"a{num(r)} {num(r)} 0 0 1 {num(-r)} {num(r)}h{num(2 * r - w)}a{num(r)} {num(r)} 0 0 1 {num(-r)} {num(-r)}"
            f"v{num(2 * r - h)}a{num(r)} {num(r)} 0 0 1 {num(r)} {num(-r)}z")


def circle(x, y, r):
    return f"M{num(x - r)} {num(y)}a{num(r)} {num(r)} 0 1 0 {num(2 * r)} 0a{num(r)} {num(r)} 0 1 0 {num(-2 * r)} 0z"


# ---- pieces of the rice

def hairline(s, x1, x2):
    """The bar's outline colour: primary to tertiary, right across."""
    return s.linear([(0, PALETTE["primary"][0], 1, "hp"), (1, PALETTE["tertiary"][0], 1, "hr")],
                    user=True, x1=x1, x2=x2, y2=0)


def glass(s, x, y, w, h, r, hair):
    """An obsidian island: dark glass, a white sheen along the top, a neutral shadow and a hairline."""
    sheen = getattr(s, "sheen", None)
    if sheen is None:
        sheen = s.sheen = s.linear([(0, "#fff", .16), (.45, "#fff", .03), (1, "#fff", 0)])
    return (f'<path d="{rrect(x - 3, y + 2, w + 6, h + 6, r + 3)}" fill="#04040c" opacity=".2"/>'
            f'<path d="{rrect(x - 1, y + 2, w + 2, h + 2, r + 1)}" fill="#04040c" opacity=".3"/>'
            f'<path d="{rrect(x, y, w, h, r)}" fill="#0b0c14" opacity=".8"/>'
            f'<path d="{rrect(x, y, w, h, r)}" fill="url(#{sheen})"/>'
            f'<path d="{rrect(x + .5, y + .5, w - 1, h - 1, r - .5)}" fill="none" stroke="url(#{hair})"/>')


def mark42(fill, x, y, size):
    """The 42 mark, size px wide, its top left at x, y."""
    k = size / 896
    polys = "".join(f'<polygon points="{p}"/>' for p in ICONS["mark42"])
    return f'<g fill="{fill}" transform="translate({num(x)} {num(y)}) scale({k:.4f}) translate(-32 51.1)">{polys}</g>'


def strip(s, name, seq, labels, x, y, size, face="t400", anchor="start", fill="#fff", seconds=CYCLE):
    """Text that changes over time: every label stacked in a column, slid behind a one-line slot.
    seq says which label shows in each equal slice of `seconds`."""
    line = round(size * 1.5)
    keys = []
    for i, v in enumerate(seq):
        if i == 0 or v != seq[i - 1]:
            keys.append((i * 100 / len(seq), f"transform:translateY({-v * line}px)"))
    s.css.append(f"@keyframes {name}{{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + f"100%{{{keys[0][1]}}}}}")
    s.css.append(f".{name}{{animation:{name} {seconds}s step-end infinite}}")
    rows = "".join(s.text(label, x, y + i * line, size, face, fill, anchor) for i, label in enumerate(labels))
    slot = s.uid()
    wide = max(width(label, size, face) for label in labels) + 8
    left = {"start": x - 4, "middle": x - wide / 2, "end": x - wide + 4}[anchor]
    s.defs.append(f'<clipPath id="{slot}"><rect x="{num(left)}" y="{num(y - size)}" width="{num(wide)}" height="{num(size * 1.32)}"/></clipPath>')
    return f'<g clip-path="url(#{slot})"><g class="{name}" transform="translate(0 {-seq[0] * line})">{rows}</g></g>'
