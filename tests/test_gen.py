"""Run with: python3 -m unittest discover -s tests"""
import datetime as dt
import pathlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "gen"))

import build
import draw
import scene
import sky

UTC = dt.timezone.utc


def sample():
    """The shape of fetch()'s answer: a year with a busy October, like the real one."""
    days = []
    start = dt.date(2025, 10, 26)
    for i in range(371):
        day = start + dt.timedelta(days=i)
        count = 40 if i > 340 and i % 3 == 0 else 3 if i % 41 == 0 else 0
        days.append({"date": day.isoformat(), "contributionCount": count})
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 371, 7)]
    repos = [{"name": "Atom-Plasma", "languages": {"edges": [{"size": 590, "node": {"name": "QML"}}, {"size": 450, "node": {"name": "Python"}}]}},
             {"name": "Libft", "languages": {"edges": [{"size": 300, "node": {"name": "C"}}]}},
             {"name": "Zinoxx0", "languages": {"edges": [{"size": 9999, "node": {"name": "Python"}}]}}]
    return {"user": {"contributionsCollection": {"contributionCalendar": {"totalContributions": 255, "weeks": weeks}},
                     "repositories": {"nodes": repos}},
            "atom": {"defaultBranchRef": {"target": {"history": {"totalCount": 118}}}}}


class Sky(unittest.TestCase):
    def test_sun_matches_an_independent_source(self):
        # api.sunrise-sunset.org for Lisbon, in UTC
        known = {(2026, 3, 20): ("06:39:44", "18:48:15"), (2026, 6, 21): ("05:11:58", "20:04:48"),
                 (2026, 9, 23): ("06:25:12", "18:32:36"), (2026, 12, 21): ("07:50:54", "17:18:21")}
        for day, times in known.items():
            for got, want in zip(sky.sun_times(dt.date(*day)), times):
                h, m, s = map(int, want.split(":"))
                self.assertLess(abs(got - dt.datetime(*day, h, m, s, tzinfo=UTC)), dt.timedelta(minutes=2), (day, want))

    def test_sun_times_are_local(self):
        self.assertEqual(sky.sun_times(dt.date(2026, 6, 21))[0].strftime("%H:%M"), "06:11")

    def test_new_moons(self):
        for when in (dt.datetime(2026, 8, 12, 17, 37, tzinfo=UTC), dt.datetime(2026, 11, 9, 7, 2, tzinfo=UTC)):
            before = sky.moon(when - dt.timedelta(hours=1))
            after = sky.moon(when + dt.timedelta(hours=1))
            self.assertGreater(before["phase"], .99)
            self.assertLess(after["phase"], .01)

    def test_full_moon(self):
        full = sky.moon(dt.datetime(2026, 10, 26, 4, 12, tzinfo=UTC))
        self.assertEqual(full["name"], "Full moon")
        self.assertGreater(full["lit"], .98)

    def test_phase_names_run_in_order(self):
        names = [sky.moon(dt.datetime(2026, 10, 10, 16, tzinfo=UTC) + dt.timedelta(days=d))["name"] for d in (0, 4, 8, 11, 15, 19, 22, 26)]
        self.assertEqual(names, ["New moon", "Waxing crescent", "First quarter", "Waxing gibbous", "Full moon",
                                 "Waning gibbous", "Last quarter", "Waning crescent"])


class Moon(unittest.TestCase):
    def test_lit_side(self):
        # the limb's sweep flag decides the side: right while waxing, left while waning
        self.assertIn("0 0 1 0 25", scene.moon_path(25, .2))
        self.assertIn("0 0 0 0 25", scene.moon_path(25, .8))


class Images(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.images = build.render(sample())

    def test_every_image_is_valid_xml(self):
        for name, svg in self.images.items():
            ET.fromstring(svg)

    def test_nothing_github_would_block_or_that_could_go_stale(self):
        for name, svg in self.images.items():
            for banned in ("<script", "<image", "<filter", "<foreignObject", "<text", "@import", "@font-face", "url(http", "data:"):
                self.assertNotIn(banned, svg, name)
            hrefs = re.findall(r'href="([^"]+)"', svg)
            self.assertTrue(all(h.startswith("#") for h in hrefs), name)

    def test_size_budget(self):
        total = sum(len(svg.encode()) for svg in self.images.values())
        self.assertLess(total, 400 * 1024)
        self.assertLess(len(self.images["hero"].encode()), 150 * 1024)

    def test_reduced_motion_everywhere(self):
        for name, svg in self.images.items():
            self.assertIn("prefers-reduced-motion", svg, name)

    def test_every_gradient_and_glyph_used_is_defined(self):
        for name, svg in self.images.items():
            ids = set(re.findall(r'id="([^"]+)"', svg))
            used = set(re.findall(r'url\(#([^)]+)\)', svg)) | set(re.findall(r'href="#([^"]+)"', svg))
            self.assertEqual(used - ids, set(), name)

    def test_page_runs_on_the_shared_clock(self):
        for name in ("hero", "atom", "libt", "dock", "pool"):
            self.assertIn(f"{draw.CYCLE}s", self.images[name], name)

    def test_alt_text_says_what_the_picture_shows(self):
        for name, svg in self.images.items():
            self.assertRegex(svg, r'<svg[^>]+aria-label="[^"]+"', name)


class Data(unittest.TestCase):
    def test_palette_covers_the_day(self):
        for key in ("primary", "secondary", "tertiary", "mood"):
            self.assertEqual(len(draw.PALETTE[key]), draw.KNOTS, key)

    def test_languages_leave_out_this_repo(self):
        names = [n for n, _ in build.languages(sample()["user"])]
        self.assertEqual(names, ["QML", "Python", "C"])
        self.assertAlmostEqual(sum(p for _, p in build.languages(sample()["user"])), 100)

    def test_the_tester_replay_is_a_passing_run(self):
        run = (draw.DATA / "libt-run.txt").read_text(encoding="utf-8")
        self.assertEqual(run.count("✓"), 43)
        self.assertIn("All 43 functions passed!", run)
        self.assertNotIn("✗", run)


class Text(unittest.TestCase):
    def test_kerning_applies(self):
        self.assertLess(draw.width("To", 100, "d800"), draw.width("T", 100, "d800") + draw.width("o", 100, "d800"))


if __name__ == "__main__":
    unittest.main()
