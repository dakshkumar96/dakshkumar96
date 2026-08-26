"""
Generates assets/card-stats-dark.svg and assets/card-stats-light.svg — four
tiles: total commits, total stars, longest contribution streak, and public
repo count.

Total commits / longest streak require walking the contribution calendar
year by year from account creation (GraphQL only returns ~1 year per call).
"""
import datetime as dt

import svgkit
from gh_api import all_repos, contributions, profile

TILES = [
    ("commits", "Total Commits", ""),
    ("stars", "Total Stars", ""),
    ("streak", "Longest Streak", " days"),
    ("repos", "Public Repos", ""),
]


def year_windows(created_at):
    start_year = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00")).year
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    for y in range(start_year, now.year + 1):
        frm = dt.datetime(y, 1, 1)
        to = min(dt.datetime(y, 12, 31, 23, 59, 59), now)
        yield frm.isoformat() + "Z", to.isoformat() + "Z"


def longest_streak(days):
    longest = current = 0
    for day in sorted(days, key=lambda d: d["date"]):
        if day["contributionCount"] > 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def compute_stats():
    repos = all_repos()
    total_repos = len([r for r in repos if not r.get("fork")])
    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    created_at = profile()["created_at"]

    total_commits = 0
    all_days = []
    for frm, to in year_windows(created_at):
        data = contributions(frm, to)
        total_commits += data["totalCommitContributions"]
        for week in data["contributionCalendar"]["weeks"]:
            all_days.extend(week["contributionDays"])

    return {
        "commits": total_commits,
        "stars": total_stars,
        "streak": longest_streak(all_days),
        "repos": total_repos,
    }


def build(p, stats):
    w, h = 760, 120
    tile_w, gap = 176, 16
    svg = [svgkit.svg_open(w, h, p)]

    x = 12
    for key, label, suffix in TILES:
        svg.append(svgkit.panel(x, 10, tile_w, h - 20, p))
        svg.append(
            svgkit.text(x + tile_w / 2, h / 2 - 6, f"{stats[key]}{suffix}", p, size=26, anchor="middle", color=p["accent"], weight="700")
        )
        svg.append(svgkit.text(x + tile_w / 2, h / 2 + 26, label, p, size=12, anchor="middle", color=p["subtext"]))
        x += tile_w + gap

    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    stats = compute_stats()
    svgkit.render_pair(lambda p: build(p, stats), "assets/card-stats-dark.svg", "assets/card-stats-light.svg")
