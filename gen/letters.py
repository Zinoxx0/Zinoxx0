"""The profile's own alphabet: capitals drawn as centre lines, one stroke weight, on a 100-tall cap.

A real font would be outlines. These are strokes, so a title costs a few hundred bytes, stays sharp at any
size and can draw itself on, one line at a time.

A point is (x, y) or (x, y, r), r rounding that corner. A line that ends where it began is closed.
"""
from kit import num

R = 22          # the corner every round letter shares

ALPHABET = {
    "A": (130, [[(0, 100), (65, 0), (130, 100)], [(28, 62), (102, 62)]]),
    "B": (130, [[(0, 50), (0, 0), (130, 0, R), (130, 50, R), (0, 50)],
                [(0, 50), (130, 50, R), (130, 100, R), (0, 100), (0, 50)]]),
    "C": (130, [[(130, 0), (0, 0, R), (0, 100, R), (130, 100)]]),
    "E": (130, [[(130, 0), (0, 0), (0, 100), (130, 100)], [(0, 50), (112, 50)]]),
    "F": (130, [[(130, 0), (0, 0), (0, 100)], [(0, 50), (112, 50)]]),
    "I": (0, [[(0, 0), (0, 100)]]),
    "K": (130, [[(0, 0), (0, 100)], [(130, 0), (0, 58)], [(52, 36), (130, 100)]]),
    "L": (120, [[(0, 0), (0, 100), (120, 100)]]),
    "M": (150, [[(0, 100), (0, 0), (75, 74), (150, 0), (150, 100)]]),
    "O": (130, [[(65, 0), (130, 0, R), (130, 100, R), (0, 100, R), (0, 0, R), (65, 0)]]),
    "P": (130, [[(0, 100), (0, 0), (130, 0, R), (130, 62, R), (0, 62)]]),
    "R": (130, [[(0, 100), (0, 0), (130, 0, R), (130, 62, R), (0, 62)], [(80, 62), (130, 100)]]),
    "S": (130, [[(130, 0), (0, 0, R), (0, 50, R), (130, 50, R), (130, 100, R), (0, 100)]]),
    "T": (130, [[(0, 0), (130, 0)], [(65, 0), (65, 100)]]),
}

# The wordmark is cut by hand: the strokes that would cross or touch stop short of each other.
WORDMARK = [
    (130, [[(0, 0), (130, 0)], [(113, 11), (17, 89)], [(0, 100), (130, 100)]]),                 # Z
    (0, [[(0, 0), (0, 100)]]),                                                                  # I
    (130, [[(0, 100), (0, 0)], [(15, 11), (115, 89)], [(130, 100), (130, 0)]]),                 # N
    (130, [[(60, 0), (106, 0), (130, 24), (130, 100, R), (0, 100, R), (0, 0, R), (60, 0)]]),    # O, cut like a panel
    (130, [[(0, 0), (130, 100)], [(130, 0), (78, 40)], [(52, 60), (0, 100)]]),                  # X
    (130, [[(0, 0), (130, 100)], [(130, 0), (78, 40)], [(52, 60), (0, 100)]]),                  # X
]


def _line(points, k, ox, oy):
    """A path through the points, its corners rounded where asked."""
    pts = [(ox + p[0] * k, oy + p[1] * k, p[2] * k if len(p) > 2 else 0) for p in points]
    out = f"M{num(pts[0][0])} {num(pts[0][1])}"
    for before, here, after in zip(pts, pts[1:], pts[2:] + [None]):
        x, y, r = here
        if not r or after is None:
            out += f"L{num(x)} {num(y)}"
            continue
        ax, ay = _towards(here, before, r)
        bx, by = _towards(here, after, r)
        out += f"L{num(ax)} {num(ay)}Q{num(x)} {num(y)} {num(bx)} {num(by)}"
    return out + ("Z" if points[0][:2] == points[-1][:2] else "")


def _towards(a, b, r):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = (dx * dx + dy * dy) ** .5
    return a[0] + dx / d * r, a[1] + dy / d * r


def lines(glyphs, x, y, height, gap):
    """Paths of a row of glyphs [(width, strokes)], top left at x, y, gap units between letters."""
    k = height / 100
    out = []
    for width, strokes in glyphs:
        out += [_line(stroke, k, x, y) for stroke in strokes]
        x += width * k + gap
    return out


def spaced(glyphs, height, total):
    """The gap that makes a row of glyphs exactly total wide."""
    return (total - sum(g[0] for g in glyphs) * height / 100) / (len(glyphs) - 1)


def title(s, text, x, y, height, stroke=2.4, gap=None, colour="#e8ebe6"):
    """A word in the alphabet, as one path. Its top left is at x, y."""
    glyphs = [ALPHABET[ch] for ch in text]
    d = "".join(lines(glyphs, x, y, height, height * .32 if gap is None else gap))
    return f'<path d="{d}" fill="none" stroke="{colour}" stroke-width="{num(stroke)}" stroke-linejoin="round"/>'
