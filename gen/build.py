#!/usr/bin/env python3
"""Draws every image on the profile into dist/, from live GitHub data and today's sky.

Standard library only, so the daily workflow needs no setup. Anything failing here is an error on
purpose: the workflow then publishes nothing and yesterday's images stay up.

    python3 gen/build.py          # needs GITHUB_TOKEN, or a logged-in gh
"""
import datetime as dt
import json
import os
import pathlib
import subprocess
import urllib.request
from xml.etree import ElementTree

import cards
import pool
import scene
import sky

LOGIN = "Zinoxx0"
DIST = pathlib.Path(__file__).resolve().parent.parent / "dist"
# not code I wrote by hand for itself, so it would only skew the language bar
SKIP_REPOS = {LOGIN}
TOP_LANGUAGES = 6

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      nodes { name languages(first: 12) { edges { size node { name } } } }
    }
  }
  atom: repository(owner: "Zinoxx0", name: "Atom-Plasma") {
    defaultBranchRef { target { ... on Commit { history { totalCount } } } }
  }
}
"""


def token():
    return os.environ.get("GITHUB_TOKEN") or subprocess.run(
        ["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()


def fetch():
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode(),
        headers={"Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as reply:
        body = json.load(reply)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def languages(user):
    """[(name, percent)] by bytes across my own public repos, the small ones folded into Other."""
    sizes = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"] not in SKIP_REPOS:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                sizes[name] = sizes.get(name, 0) + edge["size"]
    total = sum(sizes.values())
    ranked = sorted(sizes.items(), key=lambda kv: -kv[1])
    top = [(name, size * 100 / total) for name, size in ranked[:TOP_LANGUAGES]]
    rest = sum(size for _, size in ranked[TOP_LANGUAGES:]) * 100 / total
    return top + ([("Other", rest)] if rest >= .1 else [])


def render(data):
    """Every image, by file name, from fetch()'s answer and today's sky."""
    user = data["user"]
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for week in calendar["weeks"] for d in week["contributionDays"]]
    now = dt.datetime.now(sky.TZ)
    sunrise, sunset = sky.sun_times(now.date())
    images = {
        "hero": scene.hero((sunrise.strftime("%H:%M"), sunset.strftime("%H:%M")), sky.moon(now)),
        "atom": cards.atom(data["atom"]["defaultBranchRef"]["target"]["history"]["totalCount"]),
        "libt": cards.libt(),
        "dock": cards.dock(languages(user)),
        "pool": pool.pool(days, calendar["totalContributions"]),
        "today": cards.today((sunrise.strftime("%H:%M"), sunset.strftime("%H:%M")), sky.moon(now)),
        "chip-intra": cards.chip("42 Intra", "42", "samercad"),
        "chip-mail": cards.chip("samercad@student.42lisboa.com", "mail"),
        "chip-instagram": cards.chip("Instagram", "instagram", "Zinoxx.0"),
        "chip-steam": cards.chip("Steam", "steam", "Zinoxx"),
    }
    for repo in ("Piscine42", "Libft", "Printf", "Get_next_line", "Pipex"):
        images[f"chip-{repo.lower()}"] = cards.chip(repo, "repo")
    return images


def main():
    images = render(fetch())
    for svg in images.values():
        ElementTree.fromstring(svg)                 # a broken image must stop the run, not go live
    DIST.mkdir(exist_ok=True)
    for name, svg in images.items():
        (DIST / f"{name}.svg").write_text(svg, encoding="utf-8")
    print(f"{len(images)} images, {sum(len(svg.encode()) for svg in images.values()) // 1024} KB")


if __name__ == "__main__":
    main()
