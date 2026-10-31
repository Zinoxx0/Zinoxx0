"""Everything below the hero: the two projects, the process table, the stack and the sign-off.

The page is addressed like a hex dump, 0x00 to 0x2A, so it ends on 42.
"""
import base64
import json
import pathlib
import re

import letters
from kit import DATA, DIM, FAINT, INK, LINE, SIG, Svg, VOID, arrow, dots, num, plate, sigil

ASSETS = DATA.parent.parent / "assets"
SHOTS = ("teal", "lilac", "ink")
PALETTES = json.loads((DATA / "palettes.json").read_text(encoding="utf-8"))
PRIMARY = 4                 # the primary accent's place in a palette's ramp

SWITCH = 6                  # seconds a wallpaper stays
WIPE = .9                   # seconds a wallpaper takes to replace the last
WIPE_FPS = 24

PASS_AT = .16               # seconds per function in the tester's replay
RUN = 30                    # seconds a replay takes, including the hold on the result


def _pct(seconds, cycle):
    return num(seconds * 100 / cycle)


def _paragraph(s, lines, x, y, fill=DIM, size=13, lead=20):
    return "".join(s.text(line, x, y + i * lead, size, fill) for i, line in enumerate(lines))


def atom(commits):
    """The one place on the page with colour in it, because colour is what the project does."""
    h = 424
    box = 24, 52, 620, 348
    s = Svg(h, "Atom Plasma: a KDE Plasma 6 rice driven by the wallpaper.",
            "The same desktop on three wallpapers, and the palette the rice computed from each.")
    plate(s, "0x10", "ATOM PLASMA", f"{commits} COMMITS")
    s.add(arrow(s.w - 16, 26))

    x, y, w, h_ = box
    clip = s.uid()
    s.defs.append(f'<clipPath id="{clip}"><rect x="{x}" y="{y}" width="{w}" height="{h_}"/></clipPath>')
    for name in SHOTS:
        data = base64.b64encode((ASSETS / f"atom-{name}.webp").read_bytes()).decode()
        s.defs.append(f'<image id="{name}" href="data:image/webp;base64,{data}" x="{x}" y="{y}" width="{w}" '
                      f'height="{h_}" preserveAspectRatio="xMidYMid slice"/>')
    cycle = SWITCH * len(SHOTS)
    frames = round(WIPE * WIPE_FPS)
    layers = f'<use href="#{SHOTS[0]}"/>'
    scan = f"0%{{transform:translateX(0);visibility:hidden}}"
    # Between wipes nothing may change at all, not even out of sight: step-end holds every value, and only the
    # wipe itself runs. An invisible bar sliding back cost four times what the whole panel costs now.
    for i, name in enumerate(SHOTS[1:] + SHOTS[:1], 1):         # the first comes back on top to close the loop
        end = i * SWITCH
        start = end - WIPE
        s.css.append(f"@keyframes w{i}{{0%{{clip-path:inset(0 100% 0 0)}}"
                     f"{_pct(start, cycle)}%{{clip-path:inset(0 100% 0 0);animation-timing-function:steps({frames})}}"
                     f"{_pct(end, cycle)}%,100%{{clip-path:inset(0 0 0 0)}}}}")
        s.css.append(f".w{i}{{animation:w{i} {cycle}s step-end infinite}}")
        layers += f'<use class="w{i}" href="#{name}"/>'
        scan += (f"{_pct(start, cycle)}%{{transform:translateX(0);visibility:visible;animation-timing-function:steps({frames})}}"
                 f"{_pct(end, cycle)}%{{transform:translateX({w}px);visibility:{'visible' if end == cycle else 'hidden'}}}")
        if end < cycle:
            scan += f"{_pct(end + .01, cycle)}%{{transform:translateX(0);visibility:hidden}}"
    s.css.append(f"@keyframes scan{{{scan}}}")
    s.css.append(f".scan{{visibility:hidden;animation:scan {cycle}s step-end infinite}}")
    s.add(f'<g clip-path="url(#{clip})">{layers}<rect class="scan" x="{x}" y="{y}" width="1.5" height="{h_}" fill="{SIG}"/></g>',
          f'<rect x="{x + .5}" y="{y + .5}" width="{w - 1}" height="{h_ - 1}" fill="none" stroke="{FAINT}"/>')

    right = 668
    s.add(letters.title(s, "ATOM", right, 62, 30), letters.title(s, "PLASMA", right, 104, 30))
    s.add(_paragraph(s, ("A KDE Plasma 6 rice driven by", "the wallpaper. Every screen", "computes its own palette."), right, 168))

    s.add(s.label("PALETTE", right, 252))
    size, gap = 46, 6
    for i, name in enumerate(SHOTS):
        ramp = PALETTES[name]
        cells = "".join(f'<rect x="{right + j * (size + gap)}" y="264" width="{size}" height="{size}" fill="{c}"/>'
                        f'<rect x="{right + j * (size + gap) + .5}" y="264.5" width="{size - 1}" height="{size - 1}" fill="none" stroke="#fff" stroke-opacity=".08"/>'
                        for j, c in enumerate(ramp))
        info = s.label(ramp[PRIMARY].upper(), s.w - 24, 252, INK, anchor="end")
        s.add(f'<g class="p{i}">{cells}{info}</g>')
        # each palette arrives halfway through the wipe that brings its wallpaper
        on = (i * SWITCH - WIPE / 2) % cycle
        off = ((i + 1) * SWITCH - WIPE / 2) % cycle
        if i == 0:
            keys = (f"0%,{_pct(off, cycle)}%{{visibility:visible}}{_pct(off + .01, cycle)}%,{_pct(on, cycle)}%{{visibility:hidden}}"
                    f"{_pct(on + .01, cycle)}%,100%{{visibility:visible}}")
        else:
            keys = (f"0%,{_pct(on, cycle)}%{{visibility:hidden}}{_pct(on + .01, cycle)}%,{_pct(off, cycle)}%{{visibility:visible}}"
                    f"{_pct(off + .01, cycle)}%,100%{{visibility:hidden}}")
            s.css.append(f".p{i}{{visibility:hidden}}")
        s.css.append(f"@keyframes p{i}{{{keys}}}.p{i}{{animation:p{i} {cycle}s step-end infinite}}")

    s.add(s.label("FOLLOWS", right, 346))
    s.add(s.label("BARS  TERMINALS  VS CODE", right, 366, INK), s.label("ZEN  LOGIN  KEYBOARD", right, 386, INK))
    return s.render()


def functions():
    """The tester's real run, as [(function, part)]."""
    run = (DATA / "libt-run.txt").read_text(encoding="utf-8")
    found = re.findall(r"✓ (ft_\w+)", run)
    if not re.search(rf"All {len(found)} functions passed", run):
        raise RuntimeError("the recorded run didn't pass: rerun make_data.py libt")
    return found


def libt(commits):
    """The real run replayed as a board, each function lighting up as it passed."""
    names = functions()
    columns, cell, row = 5, 121, 26
    rows = -(-len(names) // columns)
    h = 52 + rows * row + 14
    s = Svg(h, "Libft Tester: tells you exactly which call failed and why.",
            f"A board of the {len(names)} libft functions, replaying a real run where all of them pass.")
    plate(s, "0x18", "LIBFT TESTER", f"{commits} COMMITS")
    s.add(arrow(s.w - 16, 26))

    s.add(letters.title(s, "LIBFT", 24, 62, 30), letters.title(s, "TESTER", 24, 104, 30))
    s.add(_paragraph(s, ("Tells you exactly which call failed", "and why: crashes, leaks, one byte", "past a malloc block, malloc failures."), 24, 168))

    left = 372
    finish = 1 + len(names) * PASS_AT
    board = ""
    for i, name in enumerate(names):
        x, y = left + i % columns * cell, 66 + i // columns * row
        at = 1 + i * PASS_AT
        board += (f'<rect x="{x + .5}" y="{y - 7.5}" width="6" height="6" fill="none" stroke="{FAINT}"/>'
                  + s.text(name, x + 14, y, 11, FAINT))
        s.css.append(f"@keyframes c{i}{{0%,{_pct(at, RUN)}%{{visibility:hidden}}{_pct(at + .01, RUN)}%,98%{{visibility:visible}}"
                     f"98.01%,100%{{visibility:hidden}}}}.c{i}{{animation:c{i} {RUN}s step-end infinite}}")
        board += (f'<g class="c{i}"><rect x="{x}" y="{y - 8}" width="7" height="7" fill="{SIG}"/>'
                  + s.text(name, x + 14, y, 11, INK) + "</g>")
    s.add(board)

    y = h - 22
    s.add(s.text("$ libt all", 24, y - 24, 12, DIM))
    s.css.append(f"@keyframes bar{{0%,{_pct(1, RUN)}%{{transform:scaleX(0)}}{_pct(finish, RUN)}%,98%{{transform:scaleX(1)}}100%{{transform:scaleX(0)}}}}"
                 f".bar{{transform-box:fill-box;transform-origin:left;animation:bar {RUN}s steps({len(names)}) infinite}}")
    s.css.append(f"@keyframes done{{0%,{_pct(finish, RUN)}%{{visibility:hidden}}{_pct(finish + .01, RUN)}%,98%{{visibility:visible}}"
                 f"98.01%,100%{{visibility:hidden}}}}.done{{animation:done {RUN}s step-end infinite}}")
    s.add(f'<rect x="24" y="{y - 14}" width="296" height="2" fill="{LINE}"/><rect class="bar" x="24" y="{y - 14}" width="296" height="2" fill="{SIG}"/>')
    s.add(s.label(f"ALL {len(names)} FUNCTIONS PASSED", 24, y + 4, SIG, attrs=' class="done"'))
    return s.render()


TABLE_COLUMNS = (("REPO", 46), ("LANG", 330), ("COMMITS", 450), ("HEAD", 590), ("PUSHED", 720), ("STATE", 850))


def table_head():
    s = Svg(72, "The process table: my public repositories.")
    plate(s, "0x20", "PROCESS TABLE")
    s.add(f'<path d="M24 46.5H976" stroke="{LINE}"/>')
    for name, x in TABLE_COLUMNS:
        s.add(s.label(name, x, 63, DIM, size=10))
    return s.render()


def table_row(repo):
    live = repo["days"] <= 30
    s = Svg(40, f'{repo["name"]}: {repo["lang"]}, {repo["commits"]} commits, pushed {repo["ago"].lower()}.')
    s.add(f'<path d="M.5 .5H{s.w - .5}V39.5H.5Z" fill="{VOID}" stroke="{LINE}"/>')
    s.add(f'<circle cx="30" cy="20" r="3" fill="{SIG if live else FAINT}"/>')
    y = 24.5
    s.add(s.text(repo["name"].lower(), 46, y, 13, INK), s.label(repo["lang"].upper(), 330, y, DIM),
          s.label(str(repo["commits"]), 450, y, INK), s.text(repo["head"], 590, y, 12, DIM),
          s.label(repo["ago"].upper(), 720, y, DIM), s.label("RUNNING" if live else "IDLE", 850, y, SIG if live else DIM))
    s.add(arrow(s.w - 24, 16))
    return s.render()


def stack(languages):
    """The languages I've actually written, by bytes across my public repos, then what they run on."""
    s = Svg(118, "Stack: the languages across my public repositories, by bytes.",
            ", ".join(f"{name} {share:.1f}%" for name, share in languages))
    plate(s, "0x28", "STACK", "BY BYTES")
    x, width, gap = 24, 952, 3
    usable = width - gap * (len(languages) - 1)
    ramp = (SIG, INK, "#b4bbb7", DIM, "#565d5a", "#3e4446", FAINT)
    pen = x
    for i, (name, share) in enumerate(languages):
        wide = max(2, usable * share / 100)
        s.add(f'<rect x="{num(pen)}" y="50" width="{num(wide)}" height="6" fill="{ramp[min(i, len(ramp) - 1)]}"/>')
        pen += wide + gap
    step = width / len(languages)
    for i, (name, share) in enumerate(languages):
        at = x + i * step
        s.add(s.label(name.upper(), at, 78, INK), s.label(f"{share:.1f}", at, 96, DIM))
    return s.render()


def eof(stamp):
    s = Svg(64, "End of file: 0b101010 = 42 = 0x2A.")
    plate(s)
    s.css.append("@keyframes blink{50%{visibility:hidden}}.blink{animation:blink 1.2s step-end infinite}")
    s.add(s.label("0x2A", 24, 37, SIG), s.label("EOF", 74, 37, INK), sigil(124, 25))
    s.add(s.label("0b101010 = 42 = 0x2A = '*'", 500, 37, DIM, anchor="middle"))
    s.add(s.label("EXITED WITH CODE 42", 956, 37, DIM, anchor="end"),
          f'<rect class="blink" x="964" y="26" width="7" height="12" fill="{SIG}"/>')
    return s.render()
