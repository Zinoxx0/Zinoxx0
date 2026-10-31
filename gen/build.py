#!/usr/bin/env python3
"""Draws every image on the profile into dist/, from live GitHub data.

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

import hero
import panels

LOGIN = "Zinoxx0"
DIST = pathlib.Path(__file__).resolve().parent.parent / "dist"
# the profile itself is drawn by a robot every night, so it would only skew the numbers
SKIP_REPOS = {LOGIN}
TOP_LANGUAGES = 6
# The bodies of the map, and the rows of the table. Seven, because a pass of the map is 7 x 6 s = 42 s.
ORBITS = 7
# Each row is a link in the README, which never changes, so the table keeps a fixed order.
TABLE = ("Atom-Plasma", "Libft_Tester", "Libft", "Piscine42", "Pipex", "Get_next_line", "Printf")

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions weeks { contributionDays { contributionCount } } }
    }
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false,
                 orderBy: {field: PUSHED_AT, direction: DESC}) {
      nodes {
        name pushedAt
        primaryLanguage { name }
        languages(first: 12) { edges { size node { name } } }
        defaultBranchRef { target { ... on Commit { abbreviatedOid history { totalCount } } } }
      }
    }
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


def ago(days):
    """How long ago, the way a process table would say it."""
    if days < 14:
        return f"{days}d ago"
    if days < 60:
        return f"{days // 7}w ago"
    if days < 730:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def repos(user, now):
    """My own public repos, freshest first."""
    out = []
    for node in user["repositories"]["nodes"]:
        if node["name"] in SKIP_REPOS or not node["defaultBranchRef"]:
            continue
        pushed = dt.datetime.fromisoformat(node["pushedAt"].replace("Z", "+00:00"))
        days = (now - pushed).days
        head = node["defaultBranchRef"]["target"]
        out.append({"name": node["name"], "lang": (node["primaryLanguage"] or {}).get("name", "-"),
                    "commits": head["history"]["totalCount"], "head": head["abbreviatedOid"],
                    "days": days, "ago": ago(days)})
    return sorted(out, key=lambda repo: repo["days"])


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


def render(data, now):
    """Every image, by file name, from fetch()'s answer."""
    user = data["user"]
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = [sum(day["contributionCount"] for day in week["contributionDays"]) for week in calendar["weeks"]]
    every = repos(user, now)
    by_name = {repo["name"]: repo for repo in every}
    stamp = now.strftime("%Y-%m-%d %H:%MZ")
    stats = {"repos": len(every), "commits": sum(repo["commits"] for repo in every),
             "year": calendar["totalContributions"], "stamp": stamp}
    images = {
        "hero": hero.hero(every[:ORBITS], weeks, stats),
        "atom": panels.atom(by_name["Atom-Plasma"]["commits"]),
        "libt": panels.libt(by_name["Libft_Tester"]["commits"]),
        "ps-head": panels.table_head(),
        "stack": panels.stack(languages(user)),
        "eof": panels.eof(stamp),
    }
    for name in TABLE:
        images[f"ps-{name.lower()}"] = panels.table_row(by_name[name])
    return images


def main():
    images = render(fetch(), dt.datetime.now(dt.timezone.utc))
    for svg in images.values():
        ElementTree.fromstring(svg)                 # a broken image must stop the run, not go live
    DIST.mkdir(exist_ok=True)
    for old in DIST.glob("*"):
        old.unlink()
    for name, svg in images.items():
        (DIST / f"{name}.svg").write_text(svg, encoding="utf-8")
    print(f"{len(images)} images, {sum(len(svg.encode()) for svg in images.values()) // 1024} KB")


if __name__ == "__main__":
    main()
