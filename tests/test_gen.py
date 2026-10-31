"""Run with: python3 -m unittest discover -s tests"""
import datetime as dt
import pathlib
import re
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "gen"))

import build
import hero
import kit
import letters
import panels

NOW = dt.datetime(2026, 10, 31, 3, 17, tzinfo=dt.timezone.utc)


def node(name, lang, commits, days, sizes):
    return {"name": name, "pushedAt": (NOW - dt.timedelta(days=days)).isoformat().replace("+00:00", "Z"),
            "primaryLanguage": {"name": lang},
            "languages": {"edges": [{"size": size, "node": {"name": key}} for key, size in sizes.items()]},
            "defaultBranchRef": {"target": {"abbreviatedOid": "30565be", "history": {"totalCount": commits}}}}


def sample():
    """The shape of fetch()'s answer."""
    days = [{"contributionCount": 9 if i > 330 and i % 3 == 0 else 0} for i in range(371)]
    weeks = [{"contributionDays": days[i:i + 7]} for i in range(0, 371, 7)]
    nodes = [node("Zinoxx0", "Python", 30, 0, {"Python": 99999}),
             node("Atom-Plasma", "QML", 118, 3, {"QML": 590, "Python": 450}),
             node("Libft_Tester", "C", 17, 4, {"C": 300}), node("Libft", "C", 57, 7, {"C": 300}),
             node("Piscine42", "C", 67, 97, {"C": 900, "Shell": 12}), node("Pipex", "C", 16, 817, {"C": 90}),
             node("Get_next_line", "C", 9, 926, {"C": 50}), node("Printf", "C", 13, 984, {"C": 80, "Makefile": 3})]
    calendar = {"totalContributions": 261, "weeks": weeks}
    return {"user": {"contributionsCollection": {"contributionCalendar": calendar}, "repositories": {"nodes": nodes}}}


IMAGES = build.render(sample(), NOW)


def keyframes(svg):
    return set(re.findall(r"@keyframes ([\w-]+)", svg))


class Images(unittest.TestCase):
    def test_all_are_valid_xml(self):
        for name, svg in IMAGES.items():
            with self.subTest(name):
                ET.fromstring(svg)

    def test_nothing_an_img_would_block(self):
        for name, svg in IMAGES.items():
            with self.subTest(name):
                self.assertNotRegex(svg, r"<script|<foreignObject|@import")
                self.assertNotRegex(svg, r"""(?:href|src)=["']https?:|url\(["']?https?:""")

    def test_every_animation_has_its_keyframes(self):
        for name, svg in IMAGES.items():
            with self.subTest(name):
                used = set(re.findall(r"animation:([a-z][\w-]*) ", svg))
                self.assertLessEqual(used, keyframes(svg))

    def test_reduced_motion_stops_everything(self):
        for name, svg in IMAGES.items():
            with self.subTest(name):
                self.assertIn("@media(prefers-reduced-motion:reduce){*{animation:none!important}}", svg)

    def test_the_still_has_one_readout(self):
        # a tracker and a readout per body, all stacked on each other if the still showed them all
        svg = IMAGES["hero"]
        self.assertIn(".slot{visibility:hidden", svg)
        self.assertEqual(svg.count(";visibility:visible\""), 2)

    def test_the_still_is_the_finished_picture(self):
        # with animations off, what's left has to be the end state: the run finished, the first wallpaper's palette
        board, atom, top = IMAGES["libt"], IMAGES["atom"], IMAGES["hero"]
        self.assertNotRegex(board, r"\.(done|bar|c\d+)\{visibility:hidden")
        self.assertNotRegex(atom, r"\.p0\{visibility:hidden")
        self.assertRegex(atom, r"\.p1\{visibility:hidden")
        self.assertRegex(top, r"\.flash\{visibility:hidden")       # the noise, never the text it resolves to
        self.assertNotRegex(top, r"\.after\{visibility:hidden")

    def test_the_page_stays_light(self):
        self.assertLess(sum(len(svg.encode()) for svg in IMAGES.values()), 500 * 1024)


class Motion(unittest.TestCase):
    """Each of these was a bug that cost far more CPU than anything visible."""

    def test_orbits_share_one_clock(self):
        for seconds, steps in re.findall(r"\.b\d\{animation:b\d (\d+)s steps\((\d+)\)", IMAGES["hero"]):
            self.assertEqual(int(steps) * hero.KNOTS / int(seconds), kit.FPS)

    def test_nothing_runs_forever_unstepped(self):
        for name, svg in IMAGES.items():
            for rule in re.findall(r"animation:[^;}]*infinite", svg):
                with self.subTest(name, rule=rule):
                    self.assertRegex(rule, r"steps\(|step-end")

    def test_the_wipe_holds_still_between_wipes(self):
        svg = IMAGES["atom"]
        for name in ("w1", "w2", "w3", "scan"):
            self.assertRegex(svg, rf"\.{name}\{{[^}}]*step-end infinite")

    def test_the_scan_bar_is_off_outside_a_wipe(self):
        # visibility reads as visible all the way between two keyframes, so it needs a hidden one before each wipe
        scan = re.search(r"@keyframes scan\{(.*?)\}\}", IMAGES["atom"]).group(1)
        self.assertEqual(scan.count("visibility:visible;animation-timing-function"), len(panels.SHOTS))
        self.assertTrue(scan.startswith("0%{transform:translateX(0);visibility:hidden"))

    def test_slots_never_overlap(self):
        match = re.search(r"@keyframes slot\{0%,([\d.]+)%\{visibility:visible\}([\d.]+)%", IMAGES["hero"])
        self.assertLess(float(match.group(2)) * build.ORBITS, 100)

    def test_a_pass_is_42_seconds(self):
        self.assertEqual(build.ORBITS * hero.SLOT, 42)


class Orbits(unittest.TestCase):
    def test_keplers_third_law(self):
        radii = [hero.NEAREST + i * hero.STEP for i in range(build.ORBITS)]
        periods = [hero.period(r) for r in radii]
        self.assertEqual(periods, sorted(periods))
        for r, t in zip(radii, periods):
            self.assertAlmostEqual(t ** 2 / r ** 3, periods[0] ** 2 / radii[0] ** 3,
                                   delta=periods[0] ** 2 / radii[0] ** 3 * .3)

    def test_periods_cut_to_whole_steps(self):
        for i in range(build.ORBITS):
            self.assertEqual(hero.period(hero.NEAREST + i * hero.STEP) * kit.FPS % hero.KNOTS, 0)

    def test_every_orbit_fits_the_panel(self):
        self.assertLess(hero.NEAREST + (build.ORBITS - 1) * hero.STEP, kit.WIDTH / 2)


class Data(unittest.TestCase):
    def test_repos_skip_the_profile_and_start_with_the_freshest(self):
        repos = build.repos(sample()["user"], NOW)
        self.assertNotIn("Zinoxx0", [repo["name"] for repo in repos])
        self.assertEqual(repos[0]["name"], "Atom-Plasma")
        self.assertEqual([r["days"] for r in repos], sorted(r["days"] for r in repos))

    def test_an_empty_repo_is_left_out(self):
        user = sample()["user"]
        user["repositories"]["nodes"][1]["defaultBranchRef"] = None
        self.assertNotIn("Atom-Plasma", [repo["name"] for repo in build.repos(user, NOW)])

    def test_ago(self):
        for days, want in ((0, "0d ago"), (13, "13d ago"), (14, "2w ago"), (59, "8w ago"), (97, "3mo ago"),
                           (729, "24mo ago"), (730, "2y ago")):
            self.assertEqual(build.ago(days), want)

    def test_languages_skip_the_profile(self):
        shares = dict(build.languages(sample()["user"]))
        self.assertAlmostEqual(sum(shares.values()), 100)
        self.assertLess(shares["Python"], 40)

    def test_every_table_row_is_drawn(self):
        for name in build.TABLE:
            self.assertIn(f"ps-{name.lower()}", IMAGES)

    def test_a_missing_repo_stops_the_run(self):
        data = sample()
        data["user"]["repositories"]["nodes"].pop()
        with self.assertRaises(KeyError):
            build.render(data, NOW)

    def test_the_recorded_run_passed(self):
        self.assertEqual(len(panels.functions()), 43)

    def test_every_wallpaper_has_a_palette(self):
        self.assertEqual(set(panels.PALETTES), set(panels.SHOTS))
        for ramp in panels.PALETTES.values():
            self.assertEqual(len(ramp), 6)
            for colour in ramp:
                self.assertRegex(colour, r"^#[0-9a-f]{6}$")


class Lettering(unittest.TestCase):
    def test_the_wordmark_fills_its_measure(self):
        height, total = 78, 880
        gap = letters.spaced(letters.WORDMARK, height, total)
        self.assertAlmostEqual(sum(g[0] for g in letters.WORDMARK) * height / 100 + gap * 5, total)

    def test_titles_are_in_the_alphabet(self):
        self.assertLessEqual(set("ATOMPLASMALIBFTTESTER"), set(letters.ALPHABET))

    def test_a_closed_letter_closes(self):
        self.assertTrue(letters.lines([letters.ALPHABET["O"]], 0, 0, 100, 0)[0].endswith("Z"))
        self.assertFalse(letters.lines([letters.ALPHABET["C"]], 0, 0, 100, 0)[0].endswith("Z"))


class Readme(unittest.TestCase):
    TEXT = (ROOT / "README.md").read_text(encoding="utf-8")

    def test_every_image_exists(self):
        for name in re.findall(r"/output/([\w.-]+)\.svg", self.TEXT):
            self.assertIn(name, IMAGES)

    def test_every_image_is_used(self):
        used = set(re.findall(r"/output/([\w.-]+)\.svg", self.TEXT))
        self.assertEqual(used, set(IMAGES))

    def test_every_image_has_alt_text(self):
        for tag in re.findall(r"<img[^>]*>", self.TEXT):
            self.assertRegex(tag, r'alt="[^"]+"')

    def test_no_image_stands_alone_on_a_line(self):
        # GitHub turns that into a raw HTML block, which sits differently from the panels around it
        self.assertNotRegex(self.TEXT, r"(?m)^<img")

    def test_each_row_links_to_its_own_repo(self):
        for name in build.TABLE:
            self.assertRegex(self.TEXT, rf'href="https://github.com/Zinoxx0/{name}"><img [^>]*ps-{name.lower()}\.svg')


if __name__ == "__main__":
    unittest.main()
