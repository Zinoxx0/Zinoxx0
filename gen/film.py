#!/usr/bin/env python3
"""Renders the hero to a 24 fps video the profile plays as a plain image. Runs here, never in CI.

An SVG inside an <img> repaints the whole scene for every frame. That's fine at 8 fps and heavy at 24,
while a browser plays the same day as AV1 for about a sixth of the CPU. So scene.py stays the source:
this films it one frame at a time, supersampled, and hero.svg stays as the fallback and still.

    python3 gen/film.py                    # writes dist/hero.avif
    python3 gen/film.py --crf 30           # re-encodes, reusing frames already rendered

Needs Firefox, ffmpeg with libsvtav1, and about 1.5 GB of space for the frames.
"""
import argparse
import concurrent.futures
import os
import pathlib
import subprocess
import sys
import tempfile

import draw

draw.FPS = FPS = 24                     # before scene is imported: its keyframes are cut from this
import scene                            # noqa: E402

DIST = pathlib.Path(__file__).resolve().parent.parent / "dist"
FRAMES = draw.CYCLE * FPS
RENDER = (2048, 864)                    # supersampled, so thin cables stay steady after scaling down
QUIET = {**os.environ, "MOZ_CRASHREPORTER_DISABLE": "1"}    # a rare crash on exit must not open a dialog on the desktop
MOON = {"phase": .62, "name": ""}       # a fixed moon: the real one is on the daily chip under the hero


def _capture(page_svg, index, folder, profile):
    """One frame: the scene paused at its moment, screenshotted by a headless Firefox."""
    png = folder / f"{index:05d}.png"
    if png.exists() and png.stat().st_size > 50_000:
        return
    seconds = (index + .5) / FPS        # mid-step: exactly on a boundary, rounding could land either side
    page = folder / f"{index:05d}.html"
    page.write_text("<!doctype html><style>*{animation-play-state:paused!important;"
                    f"animation-delay:-{seconds}s!important}}</style><body style=margin:0>{page_svg}", encoding="utf-8")
    for _ in range(3):
        subprocess.run(["firefox", "--headless", "--no-remote", "--profile", str(profile),
                        f"--window-size={RENDER[0]},{RENDER[1]}", "--screenshot", str(png), f"file://{page}"],
                       capture_output=True, timeout=60, env=QUIET)
        if png.exists() and png.stat().st_size > 50_000:
            break
    else:
        raise RuntimeError(f"frame {index} failed")
    page.unlink()


def render(folder, workers):
    svg = scene.hero(None, MOON, pace=FPS * draw.CYCLE // draw.KNOTS).replace(
        f'width="{scene.W}" height="{scene.H}"', f'width="{RENDER[0]}" height="{RENDER[1]}"', 1)
    profiles = [tempfile.mkdtemp(prefix="film-", dir=folder) for _ in range(workers)]
    def batch(worker):
        for index in range(worker, FRAMES, workers):
            _capture(svg, index, folder, profiles[worker])
    with concurrent.futures.ThreadPoolExecutor(workers) as pool:
        list(pool.map(batch, range(workers)))
    subprocess.run(["rm", "-rf", *profiles], check=True)


def encode(folder, out, width, crf, preset):
    height = width * scene.H // scene.W
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-framerate", str(FPS),
                    "-i", str(folder / "%05d.png"), "-an",
                    "-vf", f"scale={width}:{height}:flags=lanczos:out_color_matrix=bt709:out_range=tv,format=yuv420p10le",
                    "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "iec61966-2-1", "-color_range", "tv",
                    "-c:v", "libsvtav1", "-preset", str(preset), "-crf", str(crf), "-g", str(FPS * 10),
                    "-svtav1-params", "tune=0", "-f", "avif", "-loop", "0", str(out)], check=True,
                   stderr=subprocess.DEVNULL)
    print(f"{out.name}: {width}x{height}, crf {crf}, {out.stat().st_size / 1048576:.2f} MB")


def main():
    args = argparse.ArgumentParser()
    args.add_argument("--frames", type=pathlib.Path, default=pathlib.Path(tempfile.gettempdir()) / "hero-frames")
    args.add_argument("--width", type=int, default=1024)
    args.add_argument("--crf", type=int, default=34)
    args.add_argument("--preset", type=int, default=4)
    args.add_argument("--workers", type=int, default=8)
    args.add_argument("--out", type=pathlib.Path, default=DIST / "hero.avif")
    opts = args.parse_args()
    opts.frames.mkdir(parents=True, exist_ok=True)
    opts.out.parent.mkdir(exist_ok=True)
    render(opts.frames, opts.workers)
    encode(opts.frames, opts.out, opts.width, opts.crf, opts.preset)


if __name__ == "__main__":
    sys.exit(main())
