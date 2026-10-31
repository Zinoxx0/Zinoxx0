"""The first panel: the wordmark above an orbital map of my repositories.

Each public repo is a body circling the core. The closer it is, the more recently I pushed to it, so what I'm
working on sits near the middle and what I've left drifts out, and the whole map is laid out again every night.
Its size is its commit count. Periods follow Kepler's third law, because if it looks like orbital mechanics it
should be orbital mechanics. The ring around the core is the last year, one bar a week.

A tracker visits one body every 6 s: seven bodies, so a 42 s pass.
"""
import math
import random

import letters
from kit import DIM, FAINT, FPS, INK, LINE, SIG, VOID, Svg, dots, num, plate, px, sigil

H = 524
MARGIN = 60
CX, CY = 500, 372
TILT = .27                  # how far the orbital plane leans towards us: ry / rx
NEAREST, STEP = 186, 44     # radius of the first orbit, and between orbits
KNOTS = 64                  # keyed positions on an orbit
BASE_PERIOD = 64            # seconds, for the first orbit
SLOT = 6                    # seconds the tracker stays on a body
ACTIVE_DAYS = 30            # a repo pushed to this recently counts as live
RING = 112                  # the year's ring, around the core


def plane(r, angle):
    """A point of the orbital plane, on screen."""
    return CX + r * math.cos(angle), CY + r * TILT * math.sin(angle)


def period(r):
    """Kepler's third law, cut to a multiple of 32 s so a knot is a whole number of steps."""
    return max(1, round(BASE_PERIOD * (r / NEAREST) ** 1.5 / 32)) * 32


def orbit(s, i, repo, count, stroke):
    """The orbit's line, and its body with a name on it. Returns (orbit markup, body markup)."""
    r = NEAREST + i * STEP
    angle = i * 2.399 + .7                  # the golden angle, so no two bodies start together
    seconds = period(r)
    name = f"b{i}"
    live = repo["days"] <= ACTIVE_DAYS
    size = 2.2 + min(repo["commits"], 120) ** .5 * .3

    frames = ""
    for k in range(KNOTS + 1):
        x, y = plane(r, angle + k * 2 * math.pi / KNOTS)
        depth = 1 + .22 * math.sin(angle + k * 2 * math.pi / KNOTS)     # nearer is bigger
        frames += f"{num(k * 100 / KNOTS)}%{{transform:translate({px(x)},{px(y)}) scale({num(depth)})}}"
    s.css.append(f"@keyframes {name}{{{frames}}}")
    s.css.append(f".{name}{{animation:{name} {seconds}s steps({seconds * FPS // KNOTS}) infinite}}")

    delay = num(.25 + i * .09)
    line = (f'<path class="draw" pathLength="1" style="animation-delay:{delay}s" d="M{num(CX - r)} {CY}'
            f'a{r} {num(r * TILT)} 0 1 1 {2 * r} 0a{r} {num(r * TILT)} 0 1 1 {-2 * r} 0" fill="none" '
            f'stroke="url(#{stroke})"/>')

    x0, y0 = plane(r, angle)
    colour = SIG if live else INK
    body = (f'<g class="{name}" transform="translate({num(x0)} {num(y0)})">'
            f'<circle r="{num(size)}" fill="{colour}"/>'
            + tracker(s, i, count)
            + s.text(repo["name"].lower(), 0, -12, 10.5, INK if live else DIM, anchor="middle", track=.3) + "</g>")
    return line, body


def tracker(s, i, count):
    """Four corners around a body, shown during its slot of the pass."""
    a, b = 13, 5
    corners = "".join(f"M{x * a} {y * (a - b)}V{y * a}H{x * (a - b)}" for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1)))
    return f'<path class="slot" style="{slot_delay(i, count)}" d="{corners}" fill="none" stroke="{SIG}"/>'


def slot_delay(i, count):
    """Its place in the pass. Hidden by default, except the first: that's the still reduced motion gets."""
    return f"animation-delay:{(i - count) * SLOT}s" + (";visibility:visible" if i == 0 else "")


def year_ring(weeks):
    """The last year around the core: a bar a week standing on the plane, taller for a busier week."""
    busiest = math.log1p(max(weeks) or 1)
    quiet, busy = "", ""
    for i, week in enumerate(weeks):
        x, y = plane(RING, i * 2 * math.pi / len(weeks) - math.pi / 2)
        if week:
            busy += f"M{num(x)} {num(y)}V{num(y - 6 - 42 * math.log1p(week) / busiest)}"
        else:
            quiet += f"M{num(x)} {num(y)}V{num(y - 3)}"
    return (f'<ellipse cx="{CX}" cy="{CY}" rx="{RING}" ry="{num(RING * TILT)}" fill="none" stroke="{FAINT}"/>'
            f'<path d="{quiet}" stroke="{DIM}"/><path d="{busy}" stroke="{SIG}" stroke-width="1.3"/>')


def core(s):
    glow = s.radial([(0, SIG, .2), (.3, SIG, .06), (1, SIG, 0)])
    return (f'<ellipse cx="{CX}" cy="{CY}" rx="130" ry="46" fill="url(#{glow})"/>'
            f'<ellipse cx="{CX}" cy="{CY}" rx="16" ry="{num(16 * TILT)}" fill="none" stroke="{DIM}"/>'
            f'<circle cx="{CX}" cy="{CY}" r="3" fill="{SIG}"/>')


def wordmark(s):
    glyphs = letters.WORDMARK
    height = 78
    gap = letters.spaced(glyphs, height, 1000 - 2 * MARGIN)
    strokes = letters.lines(glyphs, MARGIN, 72, height, gap)
    out = ""
    for i, d in enumerate(strokes):
        colour = SIG if i == len(strokes) - 3 else INK      # one line of the last X carries the signal
        out += (f'<path class="draw slow" pathLength="1" style="animation-delay:{num(.5 + i * .05)}s" d="{d}" '
                f'fill="none" stroke="{colour}" stroke-width="3" stroke-linejoin="round"/>')
    return out


def decode(s, text, x, y, fill, at, seed):
    """A label that resolves out of noise once, left to right, when the page opens."""
    noise = random.Random(seed)
    frames, per = 9, .055
    out = ""
    for f in range(frames):
        known = len(text) * f // frames
        line = "".join(c if j < known or c == " " else noise.choice("01x/#_%*") for j, c in enumerate(text))
        out += s.label(line, x, y, DIM, attrs=f' class="flash" style="animation-delay:{num(at + f * per)}s"')
    return out + s.label(text, x, y, fill, attrs=f' class="after" style="animation-delay:{num(at + frames * per)}s"')


def session(s, x, y):
    """A clock that starts when the image does: the time you've been here, the one live number an image can know."""
    size, line = 11, 16
    cell = size * .6 + size * .13
    slot = s.uid()
    s.defs.append(f'<clipPath id="{slot}"><rect x="{num(x - 2)}" y="{num(y - size)}" width="{num(cell * 8 + 2)}" height="{num(size + 3)}"/></clipPath>')
    out = s.label("00:", x, y, INK)
    pen = x + cell * 3
    for digit, (count, seconds) in enumerate(((6, 3600), (10, 600), (6, 60), (10, 10))):
        name = f"t{digit}"
        s.css.append(f"@keyframes {name}{{to{{transform:translateY({-count * line}px)}}}}")
        s.css.append(f".{name}{{animation:{name} {seconds}s steps({count}) infinite}}")
        column = "".join(s.label(str(n), pen, y + n * line, INK) for n in range(count))
        out += f'<g class="{name}">{column}</g>'
        pen += cell + (cell if digit == 1 else 0)
    return f'<g clip-path="url(#{slot})">{out}</g>' + s.label(":", x + cell * 5, y, INK)


def readout(s, repo, i, count):
    """What the tracker has found: one body's numbers, bottom left, for as long as it stays on it."""
    x, y = 24, 446
    rows = (("TRACK", repo["name"].upper()), ("LANG", repo["lang"].upper()),
            ("COMMITS", str(repo["commits"])), ("PUSHED", repo["ago"].upper()))
    out = "".join(s.label(k, x, y + j * 18, DIM) + s.label(v, x + 78, y + j * 18, SIG if j == 0 else INK)
                  for j, (k, v) in enumerate(rows))
    return f'<g class="slot" style="{slot_delay(i, count)}">{out}</g>'


def hero(repos, weeks, stats):
    """repos freshest first, weeks as commit counts oldest first, stats {repos, commits, year, stamp}."""
    s = Svg(H, "Zinoxx. Samir Mercado, co-founder and lead engineer at ViVia Technologies, student at 42 Lisboa.",
            "An orbital map of my repositories: the closer a body is to the core, the more recently I pushed to it. "
            "The ring around the core is the last year of contributions, one bar a week. Redrawn every night.")
    stroke = s.linear([(0, LINE), (.45, FAINT), (1, "#4a5256")])     # the far side of an orbit is the dim one
    count = len(repos)
    share = 100 / count
    s.css += [
        "@keyframes draw{from{stroke-dashoffset:1.01}to{stroke-dashoffset:0}}",
        ".draw{stroke-dasharray:1.01 1;animation:draw 1.3s cubic-bezier(.3,.7,.1,1) both}",
        ".slow{animation-duration:1.1s}",
        "@keyframes flash{from,to{visibility:visible}}",
        ".flash{visibility:hidden;animation:flash .055s step-end}",
        "@keyframes after{from,to{visibility:hidden}}",
        ".after{animation:after .001s backwards}",
        # cut a touch short: at a boundary, two slots showing at once would double the readout for a frame
        f"@keyframes slot{{0%,{num(share - .03)}%{{visibility:visible}}{num(share - .02)}%,100%{{visibility:hidden}}}}",
        f".slot{{visibility:hidden;animation:slot {count * SLOT}s step-end infinite}}",
    ]
    plate(s)
    s.add(dots(50, 50, 950, 450))
    s.add(s.label("0x00", 24, 33, SIG), sigil(74, 22))
    s.add(s.label("38.7223N 9.1393W", 500, 33, DIM, anchor="middle"))
    s.add(s.label("SESSION", 852, 33, DIM), session(s, 912, 33))
    s.add(wordmark(s))

    columns = ((MARGIN, "SAMIR MERCADO", "LISBON, PT"),
               (394, "CO-FOUNDER, LEAD ENGINEER", "VIVIA TECHNOLOGIES"),
               (760, "STUDENT", "42 LISBOA / SAMERCAD"))
    for n, (x, top, bottom) in enumerate(columns):
        s.add(decode(s, top, x, 182, INK, 1 + n * .12, top), decode(s, bottom, x, 200, DIM, 1.1 + n * .12, bottom))

    placed = [orbit(s, i, repo, count, stroke) for i, repo in enumerate(repos)]
    s.add(*(line for line, _ in placed))
    s.add(year_ring(weeks), core(s))
    s.add(*(body for _, body in placed))

    fade = s.radial([(0, VOID), (.55, VOID), (1, VOID, 0)])
    s.add(f'<ellipse cx="50" cy="{H - 8}" rx="420" ry="126" fill="url(#{fade})"/>',
          f'<ellipse cx="950" cy="{H - 8}" rx="420" ry="126" fill="url(#{fade})"/>',
          f'<path d="M1 {H - 40}V{H - 1}H{s.w - 1}V{H - 40}" fill="none" stroke="{LINE}"/>')
    s.add(*(readout(s, repo, i, count) for i, repo in enumerate(repos)))
    rows = (("REPOS", str(stats["repos"])), ("COMMITS", f'{stats["commits"]:,}'),
            ("LAST 12 MO", f'{stats["year"]:,}'), ("UPLINK", stats["stamp"]))
    for j, (k, v) in enumerate(rows):
        s.add(s.label(k, 762, 446 + j * 18, DIM), s.label(v, 976, 446 + j * 18, INK, anchor="end"))
    return s.render()
