"""The README's cards: Atom Plasma, Libft_Tester, the stack, and the chips for links.

Each card is one image, and they all share the day clock, so while the hero's sky moves their accents
move with it. The numbers come from build.py's fetch. The Libft_Tester terminal replays a real run,
kept in data/libt-run.txt.
"""
from draw import DATA, FPS, ICONS, KNOTS, PALETTE, Svg, glass, hairline, mark42, num, rrect, strip, width

W = 1280
INK, SOFT, DIM = "#f3f4f9", "#c3c6d4", "#858aa0"
CARD, TERM = "#0e0f17", "#0c0d15"


def frame(s, h, r=26):
    """The card itself: obsidian, washed with the current accent from one corner, with the bar's hairline."""
    hair = hairline(s, 0, W)
    wash = s.radial([(0, PALETTE["primary"][0], .2, "hp"), (.55, PALETTE["primary"][0], .06, "hp"), (1, PALETTE["primary"][0], 0, "hp")],
                    cx=1, cy=0, r=1)
    wash2 = s.radial([(0, PALETTE["tertiary"][0], .12, "hr"), (1, PALETTE["tertiary"][0], 0, "hr")], cx=0, cy=1, r=.8)
    sheen = s.linear([(0, "#fff", .07), (1, "#fff", 0)], y2=.28)
    body = rrect(0, 0, W, h, r)
    return (f'<path d="{body}" fill="{CARD}"/><path d="{body}" fill="url(#{wash})"/><path d="{body}" fill="url(#{wash2})"/>'
            f'<path d="{body}" fill="url(#{sheen})"/>'
            f'<path d="{rrect(.75, .75, W - 1.5, h - 1.5, r - .75)}" fill="none" stroke="url(#{hair})" stroke-width="1.5"/>')


def title(s, heavy, light, x, y, size=62):
    """Heading in the same lockup as the hero's name."""
    w = width(heavy, size, "d800")
    return s.text(heavy, x, y, size, "d800", INK) + s.text(light, x + w + size * .24, y, size, "d300", INK)


def label(s, text, x, y, anchor="start"):
    return s.text(text, x, y, 15, "t600", "#fff", anchor, track=3, opacity=.62)


def paragraph(s, lines, x, y, size=23, fill=SOFT, leading=1.45):
    return "".join(s.text(line, x, y + i * size * leading, size, "t400", fill) for i, line in enumerate(lines))


def pill(s, text, x, y, hair, face="m400"):
    """A small glass tag; returns (svg, its width)."""
    w = width(text, 17, face) + 32
    return glass(s, x, y, w, 38, 19, hair) + s.text(text, x + 16, y + 25, 17, face, INK), w


def pills(s, texts, x, y, hair):
    out = ""
    for text in texts:
        part, w = pill(s, text, x, y, hair)
        out += part
        x += w + 12
    return out


def atom(commits):
    h = 412
    s = Svg(W, h, "Atom Plasma", "Atom Plasma, a KDE Plasma 6 rice driven by the wallpaper. The swatches show this "
            "page's palette, computed by Atom Plasma's engine from the sky above.")
    hair = hairline(s, 0, W)
    s.add(frame(s, h))
    s.add(label(s, "KDE PLASMA 6 RICE", 52, 70), title(s, "Atom", "Plasma", 52, 138))
    s.add(paragraph(s, ("A desktop driven by the wallpaper. Every screen",
                        "gets its own palette, and the colours, bars, terminals,",
                        "VS Code, Zen, the login screen and even the keyboard",
                        "lighting all follow it."), 52, 190))
    s.add(pills(s, ("QML", "Python", f"{commits} commits"), 52, 326, hair))

    # the palette panel: the very colours this page is wearing right now
    x, y, pw, ph = 696, 44, 540, 324
    s.add(glass(s, x, y, pw, ph, 22, hair))
    s.add(s.text("This page's palette", x + 28, y + 44, 21, "t600", INK))
    s.add(s.text("from the sky above, by Atom Plasma's engine", x + 28, y + 70, 16.5, "t400", DIM))
    moods = sorted(set(PALETTE["mood"]))
    wm = max(width(m, 16, "m700") for m in moods) + 30
    s.add(f'<path class="ap" d="{rrect(x + pw - 28 - wm, y + 26, wm, 32, 16)}" fill="{PALETTE["primary"][0]}"/>')
    s.add(strip(s, "mood", [moods.index(m) for m in PALETTE["mood"]], moods, x + pw - 28 - wm / 2, y + 47.5, 16, "m700",
                "middle", "#0b0c14"))
    sw, gap = 148, 20
    for i, (key, cls) in enumerate((("primary", "ap"), ("secondary", "aq"), ("tertiary", "ar"))):
        sx = x + 28 + i * (sw + gap)
        sy = y + 94
        s.add(f'<path class="{cls}" d="{rrect(sx, sy, sw, 120, 18)}" fill="{PALETTE[key][0]}"/>')
        s.add(s.text(key, sx + 2, sy + 150, 17, "t500", INK))
        hexes = PALETTE[key]
        s.add(strip(s, f"x{i}", list(range(KNOTS)), hexes, sx + 2, sy + 178, 16, "m400", fill=SOFT))
    return s.render()


def libt():
    h = 470
    s = Svg(W, h, "Libft Tester", "Libft Tester replaying a real run: all 43 functions pass.")
    s.add(frame(s, h))
    s.add(label(s, "THE 42 LIBFT, UNDER PRESSURE", 52, 70), title(s, "Libft", "Tester", 52, 138))
    s.add(paragraph(s, ("Tells you exactly which call failed and why,", "before your evaluator does."), 52, 190))
    checks = ("Crashes and infinite loops", "Leaks, double frees, bad frees",
              "One byte past a malloc block", "Every malloc failing, in turn")
    for i, line in enumerate(checks):
        y = 280 + i * 38
        s.add(s.text("✓", 52, y, 21, "m700", "#9ece6a"), s.text(line, 84, y, 21, "t400", INK))
    s.add(_terminal(s, 628, 40, 612, h - 80))
    return s.render()


def _terminal(s, x, y, w, h):
    """A replay of the run: the command typed, then a cover sliding down the lines, then the page scrolling."""
    period = 24
    run = (DATA / "libt-run.txt").read_text(encoding="utf-8").rstrip("\n").split("\n")
    run = run[1:]                                   # the build line says nothing the prompt doesn't
    size, step = 16, 21.5
    pad = y + 86
    visible = int((h - 88) // step)
    hair = hairline(s, 0, W)
    out = glass(s, x, y, w, h, 18, hair) + f'<path d="{rrect(x + 1, y + 1, w - 2, h - 2, 17)}" fill="{TERM}"/>'
    out += "".join(f'<circle cx="{x + 24 + i * 19}" cy="{y + 21}" r="5.6" fill="{c}"/>'
                   for i, c in enumerate(("#f7768e", "#e0af68", "#9ece6a")))
    out += s.text("~/libft", x + w / 2, y + 26, 15, "m400", DIM, "middle")
    # the prompt line stays put
    out += s.text("~/libft", x + 20, y + 62, size, "m400", "#7aa2f7") + s.text(">", x + 96, y + 62, size, "m700", "#9ece6a")
    command = "libt all"
    cx = x + 116
    out += s.text(command, cx, y + 62, size, "m400", INK)
    glyph = size * .6
    ticks = len(command)
    keys = [(0, "transform:translateX(0)"), (8.33, "transform:translateX(0)")]
    keys += [(8.33 + (i + 1) * 100 / FPS / period, f"transform:translateX({num(glyph * (i + 1))}px)") for i in range(ticks)]
    keys += [(100, f"transform:translateX({num(glyph * ticks)}px)")]
    s.css.append("@keyframes type{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + "}")
    s.css.append(f".type{{animation:type {period}s steps(1) infinite}}")
    out += f'<path class="type" transform="translate({num(glyph * ticks)} 0)" d="M{cx - 1} {y + 46}h{num(glyph * ticks + 12)}v22h{num(-(glyph * ticks + 12))}z" fill="{TERM}"/>'
    # output: every line laid out once, then cover and scroll over it
    lines = ""
    for i, line in enumerate(run):
        ly = pad + (i + 1) * step
        if "✓" in line:
            lines += s.text("✓", x + 34, ly, size, "m700", "#9ece6a") + s.text(line.strip("✓ "), x + 58, ly, size, "m400", SOFT)
        elif "✨" in line:
            lines += _spark(x + 42, ly - 6) + s.text(line.replace("✨", "").strip(), x + 58, ly, size, "m700", "#fff")
        elif "─" in line:
            lines += f'<path d="M{x + 22} {ly - 5}h{w - 60}" stroke="{DIM}" opacity=".6"/>'
        elif line.strip():
            lines += s.text(line.strip(), x + 22, ly, size, "m700", INK)
    n = len(run)
    scroll = (n - visible + 1) * step
    start, show_end = 2.0, 11.0
    per = (show_end - start) / n
    cover_top = pad + step * .35
    pct = lambda t: t * 100 / period
    # the cover uncovers a line a tick, the scroll takes over when the window is full
    cover, slide = [(0, "transform:translateY(0)"), (pct(start), "transform:translateY(0)")], [(0, "transform:translateY(0)"), (pct(start), "transform:translateY(0)")]
    for i in range(1, n + 1):
        t = start + i * per
        shown = min(i, visible - 1)
        cover.append((pct(t), f"transform:translateY({num(shown * step)}px)"))
        slide.append((pct(t), f"transform:translateY({num(-max(0, i - visible + 1) * step)}px)"))
    cover.append((100, f"transform:translateY({num((visible - 1) * step)}px)"))
    slide.append((100, f"transform:translateY({num(-scroll)}px)"))
    for name, keys in (("cover", cover), ("slide", slide)):
        s.css.append(f"@keyframes {name}{{" + "".join(f"{num(k)}%{{{c}}}" for k, c in keys) + "}")
        s.css.append(f".{name}{{animation:{name} {period}s steps(1) infinite}}")
    clip = s.uid()
    bottom = y + h - 12
    s.defs.append(f'<clipPath id="{clip}"><rect x="{x + 2}" y="{num(cover_top)}" width="{w - 4}" height="{num(bottom - cover_top)}"/></clipPath>')
    out += (f'<g clip-path="url(#{clip})"><g class="slide" transform="translate(0 {num(-scroll)})">{lines}</g>'
            f'<rect class="cover" transform="translate(0 {num((visible - 1) * step)})" x="{x + 2}" y="{num(cover_top)}" '
            f'width="{w - 4}" height="{num(h)}" fill="{TERM}"/></g>')
    return out


def _spark(x, y):
    """Stands in for the run's ✨, which no font here has."""
    return (f'<path d="M{x} {y - 8}q1.4 6.6 8 8q-6.6 1.4 -8 8q-1.4 -6.6 -8 -8q6.6 -1.4 8 -8z" fill="#e0af68"/>')


def dock(languages):
    """The tools, on a dock, over what my public repos are actually written in."""
    h = 282
    s = Svg(W, h, "Stack", "C, C++, Python, QML and Qt, JavaScript, Bash, Linux, Git, Photoshop, After Effects. "
            + ", ".join(f"{n} {p:.0f}%" for n, p in languages) + " across public repositories.")
    hair = hairline(s, 0, W)
    s.add(frame(s, h))
    keys = list(ICONS["skills"])
    size, gap = 76, 18
    total = len(keys) * size + (len(keys) - 1) * gap
    x0 = (W - total) / 2
    s.add(glass(s, x0 - 24, 38, total + 48, size + 36, 28, hair))
    wave = 16                                       # a ripple crosses the dock, then it rests
    for i, key in enumerate(keys):
        bump = i * .375 / wave * 100
        name = f"b{i}"
        s.clock(name, wave, _bounce(bump))
        k = size / 256
        s.add(f'<g class="{name}"><g transform="translate({num(x0 + i * (size + gap))} 56) scale({k:.4f})">{ICONS["skills"][key]}</g></g>')
    # the language bar
    x, y, full = 52, 186, W - 104
    shades = _ramp(len(languages))
    bar = ""
    cx = x
    legend = x
    clip = s.uid()
    s.defs.append(f'<clipPath id="{clip}"><path d="{rrect(x, y, full, 12, 6)}"/></clipPath>')
    for i, (lang, share) in enumerate(languages):
        w = full * share / 100
        bar += f'<rect class="{shades[i][0]}" x="{num(cx)}" y="{y}" width="{num(w + .5)}" height="12" fill="{PALETTE["primary"][0]}" opacity="{shades[i][1]}"/>'
        cx += w
        text = f"{lang} {share:.1f}%"
        bar_label = s.text(text, legend + 20, y + 54, 17, "t500", SOFT)
        dot = f'<circle class="{shades[i][0]}" cx="{num(legend + 6)}" cy="{y + 48}" r="6" fill="{PALETTE["primary"][0]}" opacity="{shades[i][1]}"/>'
        s.add(dot, bar_label)
        legend += width(text, 17, "t500") + 58
    s.add(f'<g clip-path="url(#{clip})">{bar}</g>')
    return s.render()


def _bounce(start):
    end = min(start + 3.75, 99)
    rest = "transform:translateY(0)"
    return [(0, rest), (start, rest), ((start + end) / 2, "transform:translateY(-11px)"), (end, rest), (100, rest)]


def _ramp(n):
    """(accent class, opacity) for n segments, walking the three accents from strong to faint."""
    classes = ("ap", "aq", "ar")
    return [(classes[i % 3], num(max(.36, 1 - i * .11))) for i in range(n)]


# ---- chips: one small image per link

CHIP = 48


def chip(text, icon, sub=None):
    """A glass pill with an icon, for a link in the README."""
    s = Svg(1, CHIP, text)
    w = int(width(text, 19, "t500") + 66 + (width(sub, 17, "m400") + 14 if sub else 0))
    s.w = w
    hair = hairline(s, 0, w)
    r = CHIP / 2 - 1
    s.add(f'<path d="{rrect(1, 1, w - 2, CHIP - 2, r)}" fill="#0e0f17"/>')
    sheen = s.linear([(0, "#fff", .12), (1, "#fff", 0)], y2=.7)
    s.add(f'<path d="{rrect(1, 1, w - 2, CHIP - 2, r)}" fill="url(#{sheen})"/>')
    s.add(f'<path d="{rrect(1, 1, w - 2, CHIP - 2, r)}" fill="none" stroke="url(#{hair})" stroke-width="1.5"/>')
    s.add(_icon(s, icon, 16, 13))
    s.add(s.text(text, 50, 31, 19, "t500", INK))
    if sub:
        s.add(s.text(sub, 50 + width(text, 19, "t500") + 14, 31, 17, "m400", SOFT))
    return s.render()


def _icon(s, icon, x, y):
    """A 22 px icon at x, y."""
    if icon == "42":
        return mark42(INK, x, y + 2, 22)
    if icon == "mail":
        return (f'<g fill="none" stroke="{INK}" stroke-width="1.9" stroke-linejoin="round" stroke-linecap="round" '
                f'transform="translate({x} {y})"><path d="{rrect(1, 3.5, 20, 15, 3)}"/><path d="M2 5.5l9 7l9 -7"/></g>')
    if icon == "repo":
        return f'<circle class="ap" cx="{x + 11}" cy="{y + 11}" r="6.5" fill="{PALETTE["primary"][0]}"/>'
    return f'<path transform="translate({x} {y}) scale({22 / 24:.4f})" d="{ICONS["brands"][icon]}" fill="{INK}"/>'
