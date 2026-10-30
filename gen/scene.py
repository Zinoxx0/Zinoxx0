"""The hero: one day over Lisbon, looking across the Tagus from a miradouro.

It works like Atom Plasma: this is the wallpaper, and the rest of the page takes its colours from it.
The day starts at golden hour, so in the first twenty seconds the sun sets and the city lights up.
PAINT is the colour script, one row per painted thing and one column per key moment, the way an anime
background team plans a sequence. Everything below it only says what is where.
"""
import math
import random

from draw import CYCLE, FPS, KNOTS, PALETTE, Svg, circle, glass, hairline, mark42, num, rrect, strip, timeline, width

W, H = 1280, 540
SEA = 338                       # the horizon, where the river meets the far bank
ARC = (430, 545, 480)           # the sun and moon ride this circle: centre x, centre y, radius

KEYS = (0, 1, 2, 3, 4, 5, 9, 10, 11, 12, 13, 14, 15)
#         golden   low      sunset   dusk     blue     night    late     predawn  dawn     sunrise  morning  noon     afternoon
PAINT = {
    "sky0": "#2b3a7a #25306f #1f2764 #161c52 #0e1440 #070a22 #070a22 #0f1539 #223066 #2f4f98 #2f6cc0 #2a6ac8 #2f5fb0",
    "sky1": "#5a5aa6 #524a9c #4a3a92 #33287c #1c2264 #0c1130 #0c1130 #1d2560 #4c4a98 #5f7fc6 #4f92de #4a96e6 #5490d8",
    "sky2": "#a96a9e #a85a98 #984a90 #6a3a86 #33307c #131a45 #131a45 #3a3680 #8e6aa6 #a3a6d8 #86bbec #7cbcf0 #86b4e6",
    "sky3": "#ee9a7c #f0866c #e8685f #b24a78 #5a3f88 #1a2258 #1a2258 #6a4a90 #e08f90 #f2c2b0 #bcdcf2 #b4dcf6 #c4d4e8",
    "sky4": "#ffd08a #ffb870 #ff9860 #e87c68 #8a5a96 #26306c #26306c #b06f92 #ffc08f #ffe2b0 #f2e8d6 #e4f2f4 #f6e2c0",
    "cloudhi": "#fff0d0 #ffd2a0 #ffa478 #e07a92 #5e5696 #2a3068 #2a3068 #5e5090 #ffc0a8 #ffeedd #ffffff #ffffff #fff6e4",
    "cloudlo": "#c9758f #a95a8a #7e4688 #4a3380 #232662 #12173f #12173f #2c2a66 #92709f #a9b8dc #a9c8ea #a6ccee #bcc4dc",
    "haze": "#ffc898 #ffae80 #f58a70 #b0608c #5a4a90 #222a64 #222a64 #8a6090 #ffb898 #ffe0c0 #e4eef2 #e0f0f6 #f0e2cc",
    "far": "#a07aa6 #8c6a9e #76558f #4e3c82 #2c2c6a #151b46 #151b46 #30306c #8474a4 #a2aece #9abad4 #98c0da #a8b8ca",
    "near": "#5a4478 #4e3c72 #413268 #2c245a #1a1a48 #0d1030 #0d1030 #1c1c4c #4f4878 #5f7088 #4f7f70 #4a846a #5c7c6a",
    "cliff": "#7a5878 #6c4e72 #573f68 #34295a #1e1c4c #0f1234 #0f1234 #211f50 #5e5078 #84808a #7d9476 #7c9c74 #8e9674",
    "bank": "#7e6080 #705678 #5a466e #372c5e #1f1d4e #0f1234 #0f1234 #222052 #62567e #8a8894 #93a4ac #94a8b0 #a2a6a8",
    "bridge": "#d0533c #b04444 #843448 #4e2c4e #2c2248 #1a1636 #1a1636 #2c2248 #8a3f48 #c8503c #de553a #e2583c #d8553a",
    "water0": "#f7c090 #f6a274 #ec8468 #c05e7c #60488c #1c2458 #1c2458 #704c8e #e8a08e #f2cdb8 #a8d0e8 #98cdea #c0cfdc",
    "water1": "#94709f #7c5a98 #684c90 #4a3a84 #2a2a6c #101640 #101640 #2a2a68 #6a5e9e #6f8fc0 #4f8fc8 #3f8ad0 #5488c0",
    "water2": "#2e3070 #282a60 #222458 #1a1c4c #101440 #080b28 #080b28 #121640 #2a2f68 #2a4a88 #1f5aa0 #1a5ea8 #265a98",
    "ripple": "#ffd8a8 #ffc48c #ffa880 #d07c98 #6a5a9c #2c3672 #2c3672 #7c5c9c #ffc0a8 #fff0dc #d8ecf8 #d0ecfa #e8e8e4",
    "pine": "#27324a #1f2840 #1a2039 #141832 #0d1028 #080a22 #080a22 #10122c #1d2640 #223f3e #255238 #235a3c #2c5438",
    "pinehi": "#7c5a64 #644860 #513a58 #2a2648 #181a3a #0f1230 #0f1230 #1d1e40 #6a5070 #4a7a5c #3f8a58 #3f9460 #5a8f50",
    "trunk": "#2a2238 #241d32 #1e182c #161426 #0e0e20 #08091a #08091a #101022 #221c30 #3a2c2e #4a3428 #4c3628 #48342a",
    "shade": "#8a4a68 #6e3a6a #4a2c6a #281e5c #181a50 #0a0e2c #0a0e2c #1c1c50 #4a3070 #805a70 #ffffff #ffffff #b06a4a",
    "road": "#7a6474 #6c5a70 #554a66 #342e58 #1e1e44 #10122a #10122a #201f48 #51496c #77767e #8e8e90 #929292 #8e887e",
    "kerb": "#b09a9e #9c8a94 #7c6f86 #4a4270 #2a2a54 #181a38 #181a38 #2e2c58 #746a88 #a9a7ac #cfcfca #d4d4ce #c8c2b4",
    "ground": "#8a5a5a #7c5058 #624454 #3a2e50 #20203e #10122a #10122a #222040 #5a4658 #8a6a5e #a8765c #ac785c #a4745a",
}
PAINT = {k: timeline(dict(zip(KEYS, v.split()))) for k, v in PAINT.items()}

# how far each thing is switched on, per knot
STARS = timeline({0: 0, 3: 0, 4: .35, 5: 1, 9: 1, 10: .55, 11: .05, 12: 0, 15: 0})
SHADE = timeline({0: .14, 1: .28, 2: .48, 3: .68, 4: .8, 5: .88, 9: .88, 10: .78, 11: .45, 12: .2, 13: 0, 14: 0, 15: .05})
LIT = (timeline({0: 0, 2: 0, 3: .9, 4: 1, 9: 1, 10: .8, 11: .15, 12: 0, 15: 0}),
       timeline({0: 0, 2: .15, 3: 1, 9: 1, 10: .6, 11: 0, 15: 0}),
       timeline({0: 0, 3: .1, 4: 1, 9: 1, 10: .9, 11: .35, 12: 0, 15: 0}))
NIGHT = timeline({0: 0, 2: 0, 3: 1, 10: 1, 11: 0, 15: 0})
DAY = timeline({0: 1, 2: 1, 3: 0, 11: 0, 12: 1, 15: 1})
SUN = timeline({0: 50, 1: 57, 2: 66, 3: 80, 4: 90, 9: 90, 10: -90, 11: -72, 12: -58, 13: -36, 14: 0, 15: 28})
SUN_ON = timeline({0: 1, 3: 1, 4: 0, 10: 0, 11: 1, 15: 1})
MOON = timeline({3: -90, 4: -70, 5: -50, 6: -34, 7: -18, 8: 0, 9: 18, 10: 36, 11: 52, 12: 68, 13: 80, 14: 90})
MOON_ON = timeline({3: 0, 4: .7, 5: 1, 11: .9, 12: .4, 13: 0, 15: 0})
GLINT = timeline({0: 1, 1: 1, 2: .85, 3: .25, 4: 0, 10: 0, 11: .4, 12: .9, 13: .7, 14: .45, 15: .7})
MOONGLINT = timeline({3: 0, 4: 0, 5: .5, 6: .9, 9: .9, 10: .5, 11: .1, 12: 0, 15: 0})
# the bar's clock in hours, running past midnight, at each knot and at the loop's end
CLOCK = (17.5, 18.33, 18.83, 19.33, 19.83, 21, 23, 24.5, 26, 27.5, 29.5, 30.67, 31.67, 33.5, 36.5, 39.5, 41.5)


def on_arc(angle):
    a = math.radians(angle)
    return ARC[0] + ARC[2] * math.sin(a), ARC[1] - ARC[2] * math.cos(a)


def values(seq):
    return [num(v) for v in seq]


class Paint:
    """Hooks elements to the colour script, adding each animated class the first time it's used."""

    def __init__(self, svg):
        self.svg = svg
        self.done = set()

    def _class(self, prefix, prop, name):
        cls = prefix + name
        if cls not in self.done:
            self.done.add(cls)
            self.svg.colour(cls, prop, name, PAINT[name])
        return cls

    def fill(self, name):
        return f'fill="{PAINT[name][0]}" class="{self._class("f", "fill", name)}"'

    def stroke(self, name):
        return f'stroke="{PAINT[name][0]}" class="{self._class("k", "stroke", name)}"'

    def stop(self, offset, name, opacity=None):
        return (offset, PAINT[name][0], opacity, self._class("s", "stop-color", name))


def hero(sun, moon, seed=42, desktop=True):
    """sun: today's sunrise and sunset as 'HH:MM'; moon: sky.moon() for tonight. desktop=False leaves only
    the wallpaper, which is what the palette engine gets to see."""
    s = Svg(W, H, "Samir Mercado", "One day over Lisbon: the sun sets behind the 25 de Abril bridge, the city "
            "lights up, the stars and moon come out, and a dolphin leaps in the Tagus.", pace=24)
    p = Paint(s)
    rng = random.Random(seed)
    for i, v in enumerate(LIT):
        s.day(f"lit{i}", {"opacity": values(v)})
    s.day("night", {"opacity": values(NIGHT)})
    s.day("daytime", {"opacity": values(DAY)})
    s.clock("rip1", 2, [(0, "opacity:.9"), (50, "opacity:.25"), (100, "opacity:.9")])
    s.clock("rip2", 2, [(0, "opacity:.25"), (50, "opacity:.9"), (100, "opacity:.25")])
    banks = _banks(s, p, rng)
    s.add(_sky(s, p), _stars(s, rng), _sun(s), _moon(s, moon), _high_clouds(s, p, rng), _clouds(s, p, rng),
          _haze(s, p), banks, _water(s, p, rng), _bridge(s, p), _boats(s, p), _dolphins(s), _gulls(s),
          _city(s, p, rng), _pine(s, p, rng), _lamp(s, p))
    if desktop:
        s.add(_lockup(s, sun, moon), _bar(s, p))
    return s.render()


def _sky(s, p):
    g = s.linear([p.stop(0, "sky0"), p.stop(.3, "sky1"), p.stop(.58, "sky2"), p.stop(.82, "sky3"), p.stop(1, "sky4")],
                 user=True, y2=SEA + 6)
    return f'<rect width="{W}" height="{SEA + 8}" fill="url(#{g})"/>'


def _stars(s, rng):
    groups = [[], [], []]
    for _ in range(170):
        x, y = rng.uniform(0, W), SEA * rng.random() ** 1.5 - 8
        groups[rng.choice((0, 0, 0, 1, 1, 2))].append(f"M{x:.0f} {y:.0f}h0")
    s.day("stars", {"opacity": values(STARS)})
    s.clock("tw1", 4, [(0, "stroke-opacity:1"), (50, "stroke-opacity:.45"), (100, "stroke-opacity:1")])
    s.clock("tw2", 6, [(0, "stroke-opacity:.5"), (50, "stroke-opacity:1"), (100, "stroke-opacity:.5")])
    band = s.radial([(0, "#b8c4ff", .17), (.5, "#a6a8ee", .07), (1, "#a6a8ee", 0)])
    dots = (f'<path class="stars" opacity="0" d="{"".join(groups[0])}" stroke="#fff" stroke-width="1.4" stroke-linecap="round"/>'
            f'<g class="tw1"><path class="stars" opacity="0" d="{"".join(groups[1])}" stroke="#dfe6ff" stroke-width="2" stroke-linecap="round"/></g>'
            f'<g class="tw2"><path class="stars" opacity="0" d="{"".join(groups[2])}" stroke="#ffe9cf" stroke-width="2.6" stroke-linecap="round"/></g>')
    # one shooting star a night
    s.clock("shoot", 96, [(0, "transform:translate(0,0);opacity:0"), (43, "transform:translate(0,0);opacity:0"),
                                (43.1, "transform:translate(0,0);opacity:1"),
                                (44.2, "transform:translate(-300px,120px);opacity:0"),
                                (100, "transform:translate(-300px,120px);opacity:0")])
    tail = s.linear([(0, "#fff", 1), (1, "#fff", 0)], x2=1, y2=-.4)
    meteor = f'<path class="shoot" d="M620 60l96 -38" stroke="url(#{tail})" stroke-width="1.8" fill="none" opacity="0"/>'
    return (f'<ellipse class="stars" opacity="0" cx="760" cy="150" rx="640" ry="84" fill="url(#{band})" '
            f'transform="rotate(-17 760 150)"/>{dots}{meteor}')


def _travel(s, name, angles, opacity):
    """Moves a group along the arc. Translated, not rotated, so the moon's face stays upright."""
    s.day(name, {"transform": ["translate({}px,{}px)".format(*map(num, on_arc(a))) for a in angles],
                 "opacity": values(opacity)})
    x, y = on_arc(angles[0])
    return f'class="{name}" transform="translate({num(x)} {num(y)})" opacity="{num(opacity[0])}"'


def _sun(s):
    halo = s.radial([(0, "#fff0c8", .95), (.1, "#ffe0a0", .62), (.3, "#ffc080", .26), (1, "#ff9060", 0)])
    disc = s.radial([(0, "#fffdf2"), (.72, "#fff2cc"), (1, "#ffe0a0")])
    return (f'<g {_travel(s, "sunw", SUN, SUN_ON)}><circle r="340" fill="url(#{halo})"/>'
            f'<circle r="30" fill="url(#{disc})"/></g>')


def moon_path(r, phase):
    """The lit part of a moon of radius r at phase 0..1 (0 new, .5 full), lit from the right while waxing."""
    waxing = phase < .5
    k = math.cos(2 * math.pi * phase)           # 1 at new moon, -1 at full
    limb = 1 if waxing else 0
    bulge = k < 0
    term = (1 if bulge else 0) if waxing else (0 if bulge else 1)
    return f"M0 {-r}A{r} {r} 0 0 {limb} 0 {r}A{num(abs(k) * r)} {r} 0 0 {term} 0 {-r}z"


def _moon(s, moon):
    r = 25
    halo = s.radial([(0, "#c8d4ff", .36), (.3, "#aab8ff", .13), (1, "#8fa0ff", 0)])
    lit = s.radial([(0, "#ffffff"), (.8, "#eef0ff"), (1, "#c8d0f0")])
    craters = circle(-7, -8, 5) + circle(8, 5, 4) + circle(-3, 10, 3.2) + circle(10, -11, 2.6)
    # tilted to about how it hangs seen from Lisbon's latitude
    return (f'<g {_travel(s, "moonw", MOON, MOON_ON)}><circle r="180" fill="url(#{halo})"/>'
            f'<g transform="rotate(-22)"><circle r="{r}" fill="#b4bee8" opacity=".07"/>'
            f'<path d="{moon_path(r, moon["phase"])}" fill="url(#{lit})"/></g>'
            f'<path d="{craters}" fill="#9aa4d4" opacity=".14"/></g>')


def _puff(rng, x0, x1, base, height):
    """One billow as a single outline: a flat base, then a bumpy dome walked in arcs of random size."""
    span = x1 - x0
    d = f"M{x0:.0f} {base:.0f}"
    x, y = x0, base
    while x < x1 - 1:
        nx = min(x + max(11, rng.uniform(.07, .19) * span), x1)
        u = (nx - x0) / span
        ny = base if nx >= x1 else base - height * math.sin(math.pi * u) ** .62 * rng.uniform(.84, 1.06)
        r = math.hypot(nx - x, ny - y) * rng.uniform(.52, .64)
        d += f"A{r:.0f} {r:.0f} 0 0 1 {nx:.0f} {ny:.0f}"
        x, y = nx, ny
    return d + "z"


def _cumulus(rng, cx, w, base, h, layers=6):
    """Billows stacked back to front. Each has its own light-to-shadow gradient, which gives the volume."""
    out = []
    for i in range(layers):
        f = i / (layers - 1)
        ww = w * rng.uniform(.5, .72) * (1 - .15 * f)
        xc = cx + rng.uniform(-.27, .27) * w
        out.append(_puff(rng, xc - ww / 2, xc + ww / 2, base, h * (1 - .66 * f) * rng.uniform(.84, 1.04)))
    return out


def _clouds(s, p, rng):
    """Two bands that tile every 1280 px, each drifting one tile per loop. The far band leaves the sun clear
    at the opening; the near one stays below the name."""
    grad = s.linear([p.stop(0, "cloudhi"), p.stop(.34, "cloudhi"), p.stop(1, "cloudlo")])
    bands = {
        ("drift1", 192): [(170, 330, SEA + 10, 128), (548, 330, SEA + 10, 170), (1125, 300, SEA + 10, 96)],
        ("drift2", 96): [(90, 230, 262, 62), (640, 190, 250, 52), (1020, 210, 268, 66)],
    }
    out = ""
    for (cls, secs), clouds in bands.items():
        tile = "".join(f'<path d="{d}" fill="url(#{grad})"/>' for c in clouds for d in _cumulus(rng, *c))
        i = s.uid()
        s.defs.append(f'<g id="{i}">{tile}</g>')
        s.clock(cls, secs, [(0, "transform:translateX(0)"), (100, "transform:translateX(-1280px)")])
        out += f'<g class="{cls}"><use href="#{i}"/><use href="#{i}" x="1280"/></g>'
    return out


def _high_clouds(s, p, rng):
    """Thin streaks of cirrus, the first thing to catch the light and the last to lose it."""
    d = ""
    for _ in range(11):
        x, y, w = rng.uniform(0, 1280), rng.uniform(16, 176), rng.uniform(120, 340)
        h = rng.uniform(1.4, 3.6)
        d += f"M{x:.0f} {y:.0f}q{w / 2:.0f} {-h:.1f} {w:.0f} 0q{-w / 2:.0f} {h * 1.6:.1f} {-w:.0f} 0z"
    i = s.uid()
    s.defs.append(f'<path id="{i}" d="{d}"/>')
    s.clock("drift3", 288, [(0, "transform:translateX(0)"), (100, "transform:translateX(-1280px)")])
    return f'<g class="drift3" fill-opacity=".34"><g {p.fill("cloudhi")}><use href="#{i}"/><use href="#{i}" x="1280"/></g></g>'


def _haze(s, p):
    g = s.linear([p.stop(0, "haze", 0), p.stop(.7, "haze", .5), p.stop(1, "haze", .8)])
    return f'<rect y="{SEA - 74}" width="{W}" height="80" fill="url(#{g})"/>'


def _smooth(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)


def _noise(rng, amp):
    phases = [rng.uniform(0, 6.3) for _ in range(4)]
    def f(x):
        return amp * (.5 * math.sin(x / 190 + phases[0]) + .3 * math.sin(x / 83 + phases[1])
                      + .14 * math.sin(x / 37 + phases[2]) + .06 * math.sin(x / 17 + phases[3]))
    return f


def _land(points, bottom):
    d = f"M{points[0][0]:.0f} {bottom}" + "".join(f"L{x:.0f} {y:.1f}" for x, y in points)
    return d + f"L{points[-1][0]:.0f} {bottom}z"


def _banks(s, p, rng):
    """Both shores. Kept as one group so the river can mirror them."""
    fn = _noise(rng, 11)
    far = [(x, SEA - 15 - fn(x)) for x in range(-10, W + 30, 14)]
    # Almada: the cliff the bridge lands on and Cristo Rei stands on, falling to the river
    fc = _noise(rng, 5)
    cliff = [(x, SEA - 52 + 60 * _smooth((x - 236) / 360) + fc(x)) for x in range(-10, 640, 10)]
    ground = next(y for x, y in cliff if x >= 150)
    cristo = (f"M136 {ground + 3}L139 {ground - 44}H161L164 {ground + 3}z"          # the portal pedestal
              f"M135 {ground - 45}h30v3.4h-30z"
              f"M147.7 {ground - 46}l-.6 -16q0 -2 -5.6 -2.6l-9.6 -.7v-1.7l12.6 -.8q1.2 -3.3 3.4 -4a2.8 2.8 0 1 1 3.4 0"
              f"q2.2 .7 3.4 4l12.6 .8v1.7l-9.6 .7q-5.6 .6 -5.6 2.6l-.6 16z")
    # Lisbon's bank: rising out of the river, with a skyline along its top
    fl = _noise(rng, 4)
    line = lambda x: SEA + 2 - 84 * _smooth((x - 850) / 440) + fl(x)
    rise = [(x, line(x)) for x in range(840, W + 30, 12)]
    blocks, x = "", 850.0
    while x < W + 20:
        w, h = rng.uniform(7, 15), rng.uniform(3, 13) * (.4 + .6 * _smooth((x - 850) / 300))
        blocks += f"M{x:.1f} {line(x + w / 2) + 5:.1f}v{-h - 5:.1f}h{w:.1f}v{h + 5:.1f}z"
        x += w + rng.uniform(.5, 3.5)
    dx, dy = 1096, line(1096) - 4
    dome = (f"M{dx - 17} {dy + 7}v-14h9v-5h16v5h9v14z"
            f"M{dx - 8} {dy - 12}q.5 -15 8 -17q7.5 2 8 17z M{dx - 1.1} {dy - 28}v-10h2.2v10z")
    shore = SEA + 30
    i = s.uid()
    s.defs.append(f'<g id="{i}"><path d="{_land(far, SEA + 8)}" {p.fill("far")}/>'
                  f'<path d="{_land(cliff, SEA + 8)}{cristo}" {p.fill("cliff")}/>'
                  f'<path d="{_land(rise, shore)}{blocks}{dome}" {p.fill("bank")}/></g>')
    s.river = s.uid()
    s.defs.append(f'<clipPath id="{s.river}"><rect y="{SEA}" width="{W}" height="{H - SEA}"/></clipPath>')
    s.reflection = f'<g clip-path="url(#{s.river})"><use href="#{i}" transform="matrix(1 0 0 -1 0 {2 * SEA + 2})" fill-opacity=".26"/></g>'
    return (f'<use href="#{i}"/>' + _lights(rng, [(x, y) for x, y in cliff if 60 < x < 600], 3, 16)
            + _lights(rng, [(x, y - 7) for x, y in rise[1:]], 3, 8))


def _lights(rng, ground, jitter, depth):
    """Windows across a shore: three sets that come on a little apart."""
    paths = ["", "", ""]
    for x, y in ground:
        for _ in range(rng.randint(1, 3)):
            paths[rng.randrange(3)] += f"M{x + rng.uniform(-9, 9):.1f} {y + rng.uniform(jitter, depth):.1f}h0"
    return "".join(f'<path class="lit{i}" opacity="0" d="{d}" stroke="#ffd58a" stroke-width="1.7" '
                   f'stroke-linecap="round"/>' for i, d in enumerate(paths))


def _water(s, p, rng):
    g = s.linear([p.stop(0, "water0"), p.stop(.28, "water1"), p.stop(1, "water2")], user=True, y1=SEA, y2=H)
    water = f'<rect y="{SEA}" width="{W}" height="{H - SEA}" fill="url(#{g})"/>'
    ripples = ["", ""]
    for i in range(170):
        y = SEA + 3 + (H - SEA) * rng.random() ** 1.6
        depth = (y - SEA) / (H - SEA)
        w = 8 + 56 * depth * rng.random() + 10 * rng.random()
        ripples[i % 2] += f"M{rng.uniform(0, W):.0f} {y:.1f}h{w:.0f}"
    r = (f'<g fill="none" stroke-width="1.2" stroke-linecap="round" stroke-opacity=".55" {p.stroke("ripple")}>'
         f'<path class="rip1" d="{ripples[0]}"/><path class="rip2" d="{ripples[1]}"/></g>')
    x0 = on_arc(0)[0]
    s.day("glint", {"transform": [f"translateX({num(on_arc(a)[0] - x0)}px)" for a in SUN], "stroke-opacity": values(GLINT)})
    s.day("mglint", {"transform": [f"translateX({num(on_arc(a)[0] - x0)}px)" for a in MOON], "stroke-opacity": values(MOONGLINT)})
    return (water + s.reflection + r + _glitter(rng, x0, "#fff0c8", "glint", GLINT[0], on_arc(SUN[0])[0] - x0)
            + _glitter(rng, x0, "#dbe2ff", "mglint", 0, 0))


def _glitter(rng, x0, colour, cls, opacity, shift):
    """The bright path on the water under the sun or moon, wider toward the viewer."""
    rows = [[], []]
    y = SEA + 2.0
    while y < H:
        depth = (y - SEA) / (H - SEA)
        spread = 12 + 92 * depth
        for _ in range(3):
            w = rng.uniform(.25, .75) * (14 + 62 * depth)
            rows[rng.randrange(2)].append(f"M{x0 + rng.uniform(-spread, spread) - w / 2:.0f} {y:.1f}h{w:.0f}")
        y += 2.4 + 7.5 * depth
    return (f'<g class="{cls}" stroke-opacity="{num(opacity)}" transform="translate({num(shift)} 0)" fill="none" '
            f'stroke="{colour}" stroke-width="1.9" stroke-linecap="round"><path class="rip1" d="{"".join(rows[0])}"/>'
            f'<path class="rip2" d="{"".join(rows[1])}"/></g>')


# ---- the 25 de Abril bridge, in perspective: u runs 0..1 from the Almada anchorage to Lisbon's, z is metres

GROW = .30
METRES = .64
TOWERS = (.3, .7)


def _grow(u):
    return 1 / (1 - GROW * u)


def _bx(u):
    return 268 + 770 * (u * _grow(u)) / _grow(1)


def _by(u, z):
    return SEA + 7 + 13 * u - z * _grow(u) * METRES


def _steps(a, b, n):
    return [a + (b - a) * i / n for i in range(n + 1)]


def _line(us, z):
    return "".join(f"{'M' if i == 0 else 'L'}{_bx(u):.1f} {_by(u, z(u)):.1f}" for i, u in enumerate(us))


def _cable(u):
    if u < TOWERS[0]:
        return 74 + 116 * (u / TOWERS[0]) ** 1.25
    if u > TOWERS[1]:
        return 74 + 116 * ((1 - u) / (1 - TOWERS[1])) ** 1.25
    return 80 + 110 * ((u - .5) / (.5 - TOWERS[0])) ** 2


def _bridge(s, p):
    span = _steps(-.05, 1.2, 60)
    chords = _line(span, lambda u: 70) + _line(span, lambda u: 58)
    us = _steps(-.05, 1.2, 96)
    truss = "".join(f"M{_bx(a):.1f} {_by(a, 58 if i % 2 else 70):.1f}L{_bx(b):.1f} {_by(b, 70 if i % 2 else 58):.1f}"
                    for i, (a, b) in enumerate(zip(us, us[1:])))
    wire = _line(_steps(0, 1, 90), _cable)
    hangers = "".join(f"M{_bx(u):.1f} {_by(u, _cable(u)):.1f}V{_by(u, 70):.1f}"
                      for u in _steps(0, 1, 74) if min(abs(u - t) for t in TOWERS) > .004)
    legs = ""
    for u in TOWERS:
        k = _grow(u)
        for side in (-1, 1):
            foot, head, w = _bx(u) + side * 6 * k, _bx(u) + side * 3.4 * k, 2.2 * k
            legs += f"M{foot - w:.1f} {_by(u, 0):.1f}L{head - w:.1f} {_by(u, 192):.1f}H{head + w:.1f}L{foot + w:.1f} {_by(u, 0):.1f}z"
        for z, half in ((190, 5.8), (150, 6.3), (112, 7), (74, 7.8), (54, 8)):
            legs += f"M{_bx(u) - half * k:.1f} {_by(u, z) - 1.6:.1f}h{2 * half * k:.1f}v3.2h{-2 * half * k:.1f}z"
    for u in (-.02, .985, 1.05, 1.11, 1.17):
        x, top, foot = _bx(u), _by(u, 58), _by(u, 0) + 4
        legs += f"M{x - 2.2:.1f} {foot:.1f}L{x - 1.4:.1f} {top:.1f}h2.8L{x + 2.2:.1f} {foot:.1f}z"
    i = s.uid()
    s.defs.append(f'<g id="{i}" fill="none"><path d="{chords}" stroke-width="2.4" {p.stroke("bridge")}/>'
                  f'<path d="{truss}" stroke-width="1" {p.stroke("bridge")}/>'
                  f'<path d="{hangers}" stroke-width=".8" {p.stroke("bridge")}/>'
                  f'<path d="{wire}" stroke-width="2.2" {p.stroke("bridge")}/>'
                  f'<path d="{legs}" {p.fill("bridge")}/></g>')
    # the warning lights on the towers, and traffic each way
    beacons = "".join(circle(_bx(u), _by(u, 197), 2.4) for u in TOWERS)
    s.clock("beacon", 3, [(0, "opacity:1"), (49.9, "opacity:1"), (50, "opacity:.08"), (100, "opacity:.08")])
    x0, y0, x1, y1 = _bx(0), _by(0, 73), _bx(1), _by(1, 73)
    dx, dy = num(x1 - x0), num(y1 - y0)
    s.clock("cars", 18, [(0, "transform:translate(0,0)"), (100, f"transform:translate({dx}px,{dy}px)")])
    s.clock("cars2", 22, [(0, f"transform:translate({dx}px,{dy}px)"), (100, "transform:translate(0,0)")])
    east = "".join(f"M{x0 - 150 * n - 20:.0f} {y0 + n * .95:.1f}h0" for n in range(-4, 2))
    west = "".join(f"M{x0 - 130 * n - 60:.0f} {y0 + 2 + n * .95:.1f}h0" for n in range(-4, 2))
    return (f'<g clip-path="url(#{s.river})"><use href="#{i}" transform="matrix(1 0 0 -1 0 {2 * SEA + 14})" fill-opacity=".2" stroke-opacity=".2"/></g><use href="#{i}"/>'
            f'<g class="night" opacity="0"><path class="beacon" d="{beacons}" fill="#ff5a4e"/>'
            f'<g stroke-linecap="round" stroke-width="2.2"><path class="cars" d="{east}" stroke="#ffe7b0"/>'
            f'<path class="cars2" d="{west}" stroke="#ff8a70"/></g></g>')


# ---- life on the river

def _boats(s, p):
    """A cacilheiro on its crossing, and a sailboat that never quite gets anywhere."""
    s.clock("ferry", 96, [(0, "transform:translate(760px,383px)"), (100, "transform:translate(-90px,398px)")])
    s.clock("sail", 48, [(0, "transform:translate(226px,374px)"), (50, "transform:translate(292px,376px)"), (100, "transform:translate(226px,374px)")])
    hull = "M-30 0h60l-4.6 8.4h-50.6z"
    stripe = "M-29 3h57.6l-1 2h-55.6z"
    cabin = "M-21 -9h40v9h-40z"
    roof = "M-23 -11h44v2h-44z"
    funnel = "M4 -18h6.4v7h-6.4z"
    cloth = "M0 -25L0 -1L15 -1z"
    jib = "M-2 -21L-2 -1L-11 -1z"
    keel = "M-13 1h29l-4 4.4h-21z"
    glow = "".join(f"M{x} -5h0" for x in range(-17, 17, 7))
    ferry = (f'<g class="ferry" transform="translate(760 383)"><path d="{hull}" fill="#f6efe6"/><path d="{stripe}" fill="#e2632f"/>'
             f'<path d="{cabin}" fill="#f6efe6"/><path d="{roof}" fill="#d8cfc4"/><path d="{funnel}" fill="#e2632f"/>'
             f'<path d="M-30 14h60M-20 18h40" stroke="#fff" stroke-width="1.2" stroke-linecap="round" opacity=".32"/>'
             f'<path class="dim" d="{hull}{cabin}{roof}{funnel}" fill="#0c1033" opacity="0"/>'
             f'<path class="night" d="{glow}" stroke="#ffd58a" stroke-width="3" stroke-linecap="round" opacity="0"/></g>')
    s.day("dim", {"opacity": values(timeline({0: .1, 1: .2, 2: .4, 3: .62, 4: .76, 5: .84, 9: .84, 10: .7, 11: .35, 12: .1, 13: 0, 15: 0}))})
    sail = (f'<g class="sail" transform="translate(226 374)"><path d="{cloth}" fill="#fff7ea"/>'
            f'<path d="{jib}" fill="#f1e4d0"/><path d="{keel}" fill="#3d4a7a"/>'
            f'<path class="dim" d="{cloth}{jib}{keel}" fill="#0c1033" opacity="0"/></g>')
    return sail + ferry


DOLPHIN = ("M100 0C95 -2 91 -3.6 86.5 -5.6C84 -10 78 -14.6 67 -17C60 -18.6 54 -19.2 49 -19"
           "C45 -24 40 -30 32 -33C33.5 -28 34 -23 33.5 -17.6C22 -15.6 8 -10.4 -6 -3.6"
           "C-13 -6 -24 -12 -36 -13C-33 -8 -29 -3.4 -22.4 .2C-27 5 -30 10 -31 17"
           "C-22 13.6 -13 7.6 -7.2 3.2C8 7 24 11.4 44 11.2L47 11.4C45 16 40.6 21.2 34 24"
           "C44 24.4 54 19 59 10.6C70 9.6 80 7.4 88 4.6C93 3 97 1.4 100 0z")
BELLY = "M97 1.2C88 4 78 7 66 8.6C50 10.6 26 10.4 -3 2.6C12 3.4 30 4.2 46 3.4C64 2.6 80 .6 97 1.2z"


def _leap(s, name, x, y, start, period, span, height, size):
    """One jump as stop-motion: a parabola sampled on the clock, the nose following the arc."""
    frames = round(1.5 * FPS)
    pct = lambda t: t * 100 / period
    hidden_a = f"transform:translate({x}px,{y + 60}px) rotate(-55deg) scale({size});opacity:0"
    hidden_b = f"transform:translate({x + span}px,{y + 60}px) rotate(60deg) scale({size});opacity:0"
    keys = [(0, hidden_a), (pct(start), hidden_a)]
    for f in range(frames + 1):
        u = f / frames
        px, py = x + span * u, y + 30 - 4 * (height + 30) * u * (1 - u)
        angle = math.degrees(math.atan(-4 * (height + 30) * (1 - 2 * u) / span))
        keys.append((pct(start + f / FPS), f"transform:translate({px:.1f}px,{py:.1f}px) rotate({angle:.1f}deg) scale({size});opacity:1"))
    end = start + (frames + 1) / FPS
    keys += [(pct(end), hidden_b), (100, hidden_b)]
    s.css.append(f"@keyframes {name}{{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + "}")
    s.css.append(f".{name}{{animation:{name} {period}s steps(1) infinite}}")
    return start, end


def _splash(s, name, x, y, when, period):
    """Rings and droplets where a dolphin breaks the water."""
    pct = lambda t: t * 100 / period
    grow = round(1.1 * FPS)
    keys = [(0, "opacity:0;transform:scale(.2)"), (pct(when), "opacity:0;transform:scale(.2)")]
    keys += [(pct(when + i / FPS), f"opacity:{num(1 - i / grow)};transform:scale({num(.3 + .85 * i / grow)})") for i in range(1, grow + 1)]
    keys += [(100, "opacity:0;transform:scale(1.15)")]
    s.css.append(f"@keyframes {name}{{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + "}")
    s.css.append(f".{name}{{animation:{name} {period}s steps(1) infinite;transform-origin:{x}px {y}px}}")
    return (f'<g class="{name}" opacity="0" fill="none" stroke="#fff" stroke-linecap="round">'
            f'<ellipse cx="{x}" cy="{y}" rx="34" ry="5.4" stroke-width="1.6"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="19" ry="3" stroke-width="1.4"/>'
            f'<path d="M{x - 16} {y - 9}h.1M{x + 15} {y - 11}h.1M{x - 7} {y - 17}h.1M{x + 7} {y - 19}h.1'
            f'M{x + 23} {y - 5}h.1M{x - 25} {y - 5}h.1" stroke-width="3"/></g>')


def _dolphins(s):
    period = 32
    skin = s.linear([(0, "#4a6488"), (.55, "#34496b"), (1, "#26344f")])
    out = ""
    # mother and calf, a beat apart
    for i, (x, y, start, span, height, size) in enumerate(((392, 424, 3.5, 138, 84, .62), (300, 456, 4.25, 118, 62, .46))):
        a, b = _leap(s, f"leap{i}", x, y, start, period, span, height, size)
        clip = s.uid()
        s.defs.append(f'<clipPath id="{clip}"><rect width="{W}" height="{y + 4}"/></clipPath>')
        out += (f'<g clip-path="url(#{clip})"><g class="leap{i}" opacity="0"><path d="{DOLPHIN}" fill="url(#{skin})"/>'
                f'<path d="{BELLY}" fill="#d4dfec" opacity=".92"/><circle cx="84" cy="-6.4" r="1.2" fill="#0e1626"/></g></g>')
        out += _splash(s, f"sp{i}a", x, y + 4, a + .2, period) + _splash(s, f"sp{i}b", x + span, y + 4, b - .3, period)
    return out


def _gulls(s):
    wing = "M0 0q5 -6 11 -1q6 -5 11 1q-6 -3 -11 1q-5 -4 -11 -1z"
    s.clock("gulls", 40, [(0, "transform:translate(1300px,206px)"), (100, "transform:translate(-160px,120px)")])
    s.clock("flap", 1, [(0, "transform:scaleY(1)"), (50, "transform:scaleY(.35)"), (100, "transform:scaleY(1)")])
    flock = ((0, 0, 1), (34, 20, .8), (66, -7, .7), (96, 26, .62))
    g = "".join(f'<g transform="translate({x} {y}) scale({k})"><path class="flap" d="{wing}" fill="#fff"/></g>' for x, y, k in flock)
    return f'<g class="daytime"><g class="gulls" transform="translate(1300 206)">{g}</g></g>'


# ---- Lisbon in front of us

WALLS = ("#f3e7d3", "#ecd9a8", "#f0b9a2", "#dfe5e8", "#e9a57f", "#f6efe4", "#d9c8e0", "#a9c8d8")
ROOFS = ("#c0603f", "#ae4f36", "#cf7450", "#a34a35")


STREET = 44           # how far the tram's street runs below the hilltop


def _hill(x):
    return 572 - 256 * max(0, (x - 680) / 600) ** 1.1


def _houses(rng, row):
    """One row of houses along the hill. Returns (drawing, silhouette, windows-that-light-up)."""
    k = .5 + row * .13
    ground = lambda x: _hill(x) + (8 + row * 31 if row < 2 else 139 + (row - 2) * 33)
    x = 690 + row * 6 - rng.uniform(0, 30)
    walls, roofs, darks, outline, lit = {}, {}, "", "", ["", "", ""]
    while x < W + 30:
        w, h = rng.uniform(50, 76) * k, rng.uniform(46, 70) * k
        foot = ground(x + w / 2)
        top = foot - h
        wall = f"M{x:.1f} {foot + 46 * k:.1f}V{top:.1f}h{w:.1f}V{foot + 46 * k:.1f}z"
        rise, eave = rng.uniform(.2, .32) * w, 2.4 * k
        roof = f"M{x - eave:.1f} {top + 1:.1f}L{x + w * .16:.1f} {top - rise:.1f}H{x + w * .84:.1f}L{x + w + eave:.1f} {top + 1:.1f}z"
        walls.setdefault(rng.choice(WALLS), []).append(wall)
        roofs.setdefault(rng.choice(ROOFS), []).append(roof)
        outline += wall + roof
        if rng.random() < .35:
            darks += f"M{x + w * .76:.1f} {top - rise * .6:.1f}v{-7 * k:.1f}h{5.4 * k:.1f}v{7 * k:.1f}z"
        columns, floors = rng.randint(2, 3), rng.randint(2, 3)
        for c in range(columns):
            for r in range(floors):
                wx, wy = x + w * (c + .5) / columns - 3.4 * k, top + 9 * k + r * (h - 10 * k) / floors
                rect = f"M{wx:.1f} {wy:.1f}h{6.8 * k:.1f}v{12 * k:.1f}h{-6.8 * k:.1f}z"
                darks += rect
                if rng.random() < .62:
                    lit[rng.randrange(3)] += rect
        x += w + rng.uniform(-3, 5) * k
    art = "".join(f'<path d="{"".join(d)}" fill="{c}"/>' for c, d in (*walls.items(), *roofs.items()))
    return art + f'<path d="{darks}" fill="#3a3a56" opacity=".66"/>', outline, lit


def _tram(s, p):
    """The 28, climbing the hill."""
    k = .92
    body = (f'<path d="M-29 -19q0 -5 5 -5h48q5 0 5 5v19h-58z" fill="#f6c21c"/>'
            f'<path d="M-29 -9h58v2.4h-58z" fill="#fff4cf"/><path d="M-29 -2.6h58V0h-58z" fill="#b83a2a"/>'
            f'<path d="M-25 -21h50v-1.6q0 -4 -4 -4h-42q-4 0 -4 4z" fill="#fff6e0"/>'
            + "".join(f'<path d="M{x} -20h9.4v9h-9.4z" fill="#3e5272"/>' for x in (-25.6, -13.6, -1.6, 10.4))
            + '<path d="M3 -27L13 -39.4" stroke="#39344a" stroke-width="1.3" fill="none"/>'
            + '<circle cx="-18" cy="2" r="3.4" fill="#2c2838"/><circle cx="18" cy="2" r="3.4" fill="#2c2838"/>')
    a, b = (770, _hill(770) + STREET + 13), (1320, _hill(1320) + STREET + 13)
    slope = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
    s.clock("tram", 32, [(0, f"transform:translate({num(a[0])}px,{num(a[1])}px) rotate({num(slope)}deg) scale({k})"),
                              (100, f"transform:translate({num(b[0])}px,{num(b[1])}px) rotate({num(slope)}deg) scale({k})")])
    glow = "".join(f"M{x} -15.6h7" for x in (-24.4, -12.4, -.4, 11.6))
    return (f'<g class="tram" transform="translate({num(a[0])} {num(a[1])})">{body}'
            f'<path class="dim" d="M-29 -19q0 -5 5 -5h48q5 0 5 5v19h-58zM-25 -21h50v-1.6q0 -4 -4 -4h-42q-4 0 -4 4z" fill="#0c1033" opacity="0"/>'
            f'<path class="night" d="{glow}" stroke="#ffd98e" stroke-width="7" opacity="0"/></g>')


def _city(s, p, rng):
    """The hill of houses, back rows then front, with a tram on the street between them. Each row gets the
    evening tint over its own outline and its lit windows on top, so they glow and nearer houses hide them."""
    s.day("shade", {"opacity": values(SHADE)})
    tint = p.fill("shade")
    def rows(numbers):
        out = ""
        for row in numbers:
            art, outline, lit = _houses(rng, row)
            out += art + f'<g {tint}><path class="shade" d="{outline}" opacity="{num(SHADE[0])}"/></g>'
            out += "".join(f'<path class="lit{i}" opacity="0" d="{d}" fill="#ffcd78"/>' for i, d in enumerate(lit) if d)
        return out
    back = rows(range(0, 2))
    front = rows(range(2, 6))
    land = f"M680 {H + 40}" + "".join(f"L{x} {_hill(x) + 6:.1f}" for x in range(680, W + 40, 20)) + f"L{W + 20} {H + 40}z"
    a, b = (700, _hill(700) + STREET), (1320, _hill(1320) + STREET)
    along = lambda dy: f"M{a[0]} {num(a[1] + dy)}L{b[0]} {num(b[1] + dy)}"
    street = (f'<path d="{along(0)}V{H + 60}L{a[0]} {H + 60}z" {p.fill("road")}/>'
              f'<path d="{along(-1.6)}{along(24)}" stroke-width="3" fill="none" {p.stroke("kerb")}/>'
              f'<path d="{along(10)}{along(15.5)}" stroke-width=".9" fill="none" stroke="#0e0e1c" opacity=".55"/>')
    wire = f'<path d="{along(-27)}" stroke-width=".9" fill="none" stroke="#17172a" opacity=".38"/>'
    return f'<path d="{land}" {p.fill("ground")}/>' + back + street + _tram(s, p) + wire + front


def _pine(s, p, rng):
    """An umbrella pine, framing the view from the left. Flat on top, dark below, sunlit along its crown."""
    trunk = ("M46 560C50 500 58 452 52 404l10 -3C74 444 68 500 76 560z"
             "M58 440L12 398l5 -4 45 34zM62 430L118 388l4 5L68 444zM64 414L88 382l4 3L72 422z")
    def crown(y, spread, n, r0, r1, cx=62):
        return "".join(circle(cx + spread * (2 * i / (n - 1) - 1) + rng.uniform(-7, 7),
                              y + rng.uniform(-4, 5) + abs(2 * i / (n - 1) - 1) ** 2 * 13, rng.uniform(r0, r1)) for i in range(n))
    return (f'<path d="{trunk}" {p.fill("trunk")}/>'
            f'<path d="{crown(382, 128, 16, 13, 25)}" {p.fill("pine")}/>'
            f'<path d="{crown(370, 112, 16, 7, 14)}" {p.fill("pinehi")}/>'
            f'<path d="{crown(376, 104, 14, 9, 16)}" {p.fill("pine")}/>')


def _lamp(s, p):
    """A Lisbon street lamp on the miradouro. It comes on at dusk."""
    x, y = 214, 410
    post = (f"M{x - 1.8} 560V{y + 12}h3.6V560z M{x - 4} 520h8v5h-8z M{x - 3} {y + 40}h6v3h-6z"
            f"M{x - 7} {y + 12}h14l-2.4 -2.4h-9.2z M{x - 6.4} {y - 12}h12.8l-3 -6h-6.8z M{x - 1} {y - 22}h2v5h-2z")
    glass = f"M{x - 6.4} {y - 12}h12.8l-2.4 21.6h-8z"
    halo = s.radial([(0, "#ffd894", .85), (.16, "#ffc873", .42), (.5, "#ffb060", .1), (1, "#ffa050", 0)])
    return (f'<circle class="lit1" opacity="0" cx="{x}" cy="{y}" r="104" fill="url(#{halo})"/>'
            f'<path d="{glass}" fill="#9fb4c8" opacity=".5"/>'
            f'<path class="lit1" opacity="0" d="{glass}" fill="#ffe3a4"/>'
            f'<path d="{post}" {p.fill("trunk")}/>')


# ---- the desktop on top of the wallpaper

def _lockup(s, sun, moon):
    """Laid out like the rice's desk clock: a heavy word, a light word, then two quiet lines."""
    right = W - 44
    scrim = s.radial([(0, "#04040e", .3), (.6, "#04040e", .14), (1, "#04040e", 0)])
    size = 66
    w2, w1 = width("Mercado", size, "d300"), width("Samir", size, "d800")
    sub = "ZINOXX  ·  SAMERCAD @ 42 LISBOA"
    day = f"{sun[0]} – {sun[1]}  ·  {moon['name']}"
    return (f'<ellipse cx="{right - 180}" cy="96" rx="330" ry="118" fill="url(#{scrim})"/>'
            + s.text("Samir", right - w2 - w1 - 16, 96, size, "d800")
            + s.text("Mercado", right - w2, 96, size, "d300")
            + s.text(sub, right, 129, 16, "t500", anchor="end", track=3.1, opacity=.94)
            + _sun_glyph(right - width(day, 16, "t400") - 18, 150)
            + s.text(day, right, 156, 16, "t400", anchor="end", opacity=.86))


def _sun_glyph(x, y):
    rays = "".join(f"M{x + 5.6 * math.cos(a):.1f} {y + 5.6 * math.sin(a):.1f}L{x + 7.6 * math.cos(a):.1f} {y + 7.6 * math.sin(a):.1f}"
                   for a in (i * math.pi / 4 for i in range(8)))
    return (f'<circle cx="{num(x)}" cy="{y}" r="3.2" fill="#fff" opacity=".86"/>'
            f'<path d="{rays}" stroke="#fff" stroke-width="1.3" stroke-linecap="round" opacity=".86"/>')


def _clock(s, x, y, size):
    """A clock that keeps the wallpaper's time, in five-minute ticks."""
    def time_at(t):
        i = min(int(t / (CYCLE / KNOTS)), KNOTS - 1)
        return CLOCK[i] + (CLOCK[i + 1] - CLOCK[i]) * (t / (CYCLE / KNOTS) - i)
    ticks = [round(time_at(t) * 12) for t in range(CYCLE)]
    return (strip(s, "hh", [t // 12 % 24 for t in ticks], [f"{h:02d}" for h in range(24)], x - 3, y, size, "t600", "end")
            + strip(s, "mm", [t % 12 for t in ticks], [f"{m * 5:02d}" for m in range(12)], x + 3, y, size, "t400")
            + s.text(":", x, y - 1, size, "t400", anchor="middle", opacity=.8))


def _bar(s, p):
    """The rice's floating bar: jewel launcher, an island of running apps, and the tray."""
    y, h = 482, 42
    hair = hairline(s, 24, W - 24)
    jewel = (f'<path d="{rrect(24, y, 54, h, 14)}" fill="#04040c" opacity=".3" transform="translate(0 3)"/>'
             f'<path class="ap" d="{rrect(24, y, 54, h, 14)}" fill="{PALETTE["primary"][0]}"/>'
             + mark42("#0b0c14", 37.5, y + 11.5, 27))
    tasks_x, tasks_w = 88, 214
    apps = ""
    for i, cls in enumerate(("ap", "aq", "ar", "ap", "aq", "ar")):
        apps += f'<circle class="{cls}" cx="{tasks_x + 26 + i * 32.4:.1f}" cy="{y + h / 2}" r="9" fill="{PALETTE["primary"][0]}" opacity="{.95 - i * .1:.2f}"/>'
    apps += f'<path d="M{tasks_x + 20} {y + h - 6}h12" stroke="#fff" stroke-width="2" stroke-linecap="round" opacity=".8"/>'
    tray_w = 190
    tray_x = W - 24 - tray_w
    tray = s.text("Lisbon", tray_x + 22, y + 26.5, 17, "t500", opacity=.92) + _clock(s, tray_x + 132, y + 27, 18)
    return (jewel + glass(s, tasks_x, y, tasks_w, h, 14, hair) + apps
            + glass(s, tray_x, y, tray_w, h, 14, hair) + tray)
