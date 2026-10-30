"""The Piscine: the contribution calendar as a swimming pool.

Every day with contributions is a fish. A dolphin swims the year in date order and eats them, which is
the classic contribution snake, redone as 42's Piscine and Hitchhiker's Guide joke at once.
"""
import math

from cards import SOFT, W, frame, label, title
from draw import FPS, PALETTE, Svg, mark42, num, rrect
from scene import BELLY, DOLPHIN

H = 372
CELL, GAP = 20, 2
TOP = 124
PERIOD = 24
SWIM = 19               # seconds of the loop the dolphin spends in the water; the rest is the pool refilling


def _fish(x, y, r):
    """A little fish facing right, r long from nose to tail."""
    return (f"M{num(x + r)} {num(y)}C{num(x + r * .5)} {num(y - r * .62)} {num(x - r * .28)} {num(y - r * .5)} {num(x - r * .52)} {num(y)}"
            f"L{num(x - r)} {num(y - r * .42)}V{num(y + r * .42)}L{num(x - r * .52)} {num(y)}"
            f"C{num(x - r * .28)} {num(y + r * .5)} {num(x + r * .5)} {num(y + r * .62)} {num(x + r)} {num(y)}z")


def _route(points):
    """Catmull-Rom through the fish, sampled finely, then respaced evenly so the dolphin keeps a steady speed."""
    pts = [points[0]] + points + [points[-1]]
    path = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for j in range(16):
            t = j / 16
            path.append(tuple(.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t + (3 * b - a - 3 * c + d) * t ** 3)
                              for a, b, c, d in zip(p0, p1, p2, p3)))
    path.append(points[-1])
    return path


def pool(days, total):
    """days: [(iso date, count)] for the calendar's last 371 days, oldest first, whole weeks from a Sunday."""
    s = Svg(W, H, "The Piscine", f"{total} contributions in the last year, as fish in a swimming pool. A dolphin swims "
            "through and eats them. So long, and thanks for all the fish.")
    s.add(frame(s, H))
    s.add(label(s, "THE LAST YEAR", 52, 54), title(s, "The", "Piscine", 52, 96, 40))
    s.add(s.text(f"{total} contributions", W - 52, 96, 21, "t500", SOFT, "end"))
    x0 = (W - 53 * (CELL + GAP) + GAP) / 2
    wide, tall = 53 * (CELL + GAP) - GAP, 7 * (CELL + GAP) - GAP
    body = rrect(x0 - 12, TOP - 12, wide + 24, tall + 24, 16)
    water = s.linear([(0, "#22a2c8"), (.5, "#147fb0"), (1, "#0d5f94")])
    glow = s.linear([(0, "#fff", .22), (.4, "#fff", 0)])
    s.add(f'<path d="{body}" fill="url(#{water})"/>'
          f'<path d="{body}" class="ap" fill="{PALETTE["primary"][0]}" opacity=".1"/>'
          f'<path d="{body}" fill="url(#{glow})"/>')
    # the tiles, the lane number on the floor, then the light moving across them
    tiles = "".join(f"M{num(x0 + c * (CELL + GAP))} {num(TOP + r * (CELL + GAP))}h{CELL}v{CELL}h-{CELL}z" for c in range(53) for r in range(7))
    s.add(f'<path d="{tiles}" fill="#c4f1ff" opacity=".1"/>')
    s.add(f'<g opacity=".13">{mark42("#fff", W / 2 - 62, TOP + 8, 124)}</g>')
    s.clock("sway", 8, [(0, "transform:translateX(0)"), (50, "transform:translateX(-46px)"), (100, "transform:translateX(0)")])
    s.clock("sway2", 12, [(0, "transform:translateX(-30px)"), (50, "transform:translateX(30px)"), (100, "transform:translateX(-30px)")])
    clip = s.uid()
    s.defs.append(f'<clipPath id="{clip}"><path d="{body}"/></clipPath>')
    lights = ""
    for i, y in enumerate((TOP + 24, TOP + 92, TOP + 136)):
        d = f"M{num(x0 - 60)} {y}" + "".join(f"q45 {-13 if j % 2 else 13} 90 0" for j in range(16))
        lights += f'<path class="{"sway" if i % 2 else "sway2"}" d="{d}" fill="none" stroke="#e4f9ff" stroke-width="2.6" opacity=".22"/>'
    # lane ropes
    ropes = ""
    for row in (2, 5):
        y = TOP + row * (CELL + GAP) - GAP / 2
        ropes += (f'<path d="M{num(x0 - 12)} {y}h{wide + 24}" stroke="#fff" stroke-width="4.4" stroke-dasharray="11 11"/>'
                  f'<path d="M{num(x0 + 11 - 12)} {y}h{wide + 24}" stroke="#ff6470" stroke-width="4.4" stroke-dasharray="11 11"/>')
    s.add(f'<g clip-path="url(#{clip})">{lights}<g opacity=".7">{ropes}</g></g>')

    centre = lambda col, row: (x0 + col * (CELL + GAP) + CELL / 2, TOP + row * (CELL + GAP) + CELL / 2)
    fish = []
    for i, (date, count) in enumerate(days):
        if count:
            fish.append((*centre(i // 7, i % 7), count))
    top = max((f[2] for f in fish), default=1)
    route = [(x0 - 90, TOP + 90)] + [(f[0], f[1]) for f in fish] + [(x0 + wide + 90, TOP + 60)]
    path = _route(route)
    # lengths along the route, to know when the dolphin reaches each fish
    lengths = [0]
    for a, b in zip(path, path[1:]):
        lengths.append(lengths[-1] + math.dist(a, b))
    length = lengths[-1] or 1
    def time_at(distance):
        return distance / length * SWIM
    arrival = []
    j = 0
    for fx, fy, _ in fish:
        while j < len(path) - 1 and math.dist(path[j], (fx, fy)) > 7:
            j += 1
        arrival.append(time_at(lengths[j]))
    # frames of the swim, with the nose along the route
    frames = []
    for f in range(SWIM * FPS + 1):
        d = f / (SWIM * FPS) * length
        k = next((i for i, v in enumerate(lengths) if v >= d), len(path) - 1)
        a = path[max(0, k - 1)]
        b = path[min(len(path) - 1, k + 1)]
        angle = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        frames.append((path[k][0], path[k][1], angle))
    pct = lambda t: t * 100 / PERIOD
    keys = [(pct(i / FPS), f"transform:translate({x:.1f}px,{y:.1f}px) rotate({a:.1f}deg) scale(.5)") for i, (x, y, a) in enumerate(frames)]
    keys.append((100, keys[-1][1]))
    s.css.append("@keyframes swim{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + "}")
    s.css.append(f".swim{{animation:swim {PERIOD}s steps(1) infinite}}")
    s.clock("wag", 1, [(0, "transform:scaleY(1)"), (50, "transform:scaleY(.82)"), (100, "transform:scaleY(1)")])
    # fish: each swims in place until the dolphin arrives, then pops, and all refill at the end
    colours = ["#fff6c8", "#ffd86a", "#ffa45e", "#ff6f91"]
    shoal = ""
    for i, ((fx, fy, count), when) in enumerate(zip(fish, arrival)):
        name = f"f{i}"
        keys = [(0, "opacity:1;transform:scale(1)"), (pct(when), "opacity:1;transform:scale(1)"),
                (pct(when + 1 / FPS), "opacity:1;transform:scale(1.4)"), (pct(when + 2 / FPS), "opacity:0;transform:scale(.2)"),
                (pct(SWIM + 1.5), "opacity:0;transform:scale(.2)"), (pct(SWIM + 2.5), "opacity:1;transform:scale(1)"), (100, "opacity:1;transform:scale(1)")]
        s.css.append(f"@keyframes {name}{{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + "}")
        s.css.append(f".{name}{{animation:{name} {PERIOD}s steps(6) infinite;transform-origin:{num(fx)}px {num(fy)}px}}")
        level = min(3, int(4 * math.log1p(count) / math.log1p(top + 1)))
        shoal += f'<path class="{name}" d="{_fish(fx, fy, 10)}" fill="{colours[level]}"/>'
    skin = s.linear([(0, "#6d89ad"), (.55, "#4c6890"), (1, "#39507a")])
    dolphin = (f'<g class="swim" transform="translate({num(frames[-1][0])} {num(frames[-1][1])}) scale(.5)"><g class="wag">'
               f'<path d="{DOLPHIN}" fill="url(#{skin})"/><path d="{BELLY}" fill="#eaf2fa"/><circle cx="84" cy="-6.4" r="1.6" fill="#0e1626"/></g></g>')
    s.add(shoal, f'<g clip-path="url(#{clip})">{dolphin}</g>')
    s.add(f'<path d="{body}" fill="none" stroke="#eaf8ff" stroke-width="3.5"/>')
    s.add(s.text("So long, and thanks for all the fish.", W / 2, H - 28, 21, "t400", SOFT, "middle"))
    return s.render()
