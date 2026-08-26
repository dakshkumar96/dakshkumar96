"""
Generates assets/card-stats-dark.svg and assets/card-stats-light.svg — a
2x3 grid of stat tiles: total commits, total stars, longest streak, public
repos, estimated lines of code, and days with a commit.

Total commits / longest streak / active days require walking the
contribution calendar year by year from account creation (GraphQL only
returns ~1 year per call). Lines of code is an estimate — GitHub's API
only exposes byte counts per language, not real line counts — using a
documented bytes-per-line heuristic rather than claiming false precision.
"""
import datetime as dt

import svgkit
from gh_api import all_repos, contributions, language_bytes, profile

BYTES_PER_LINE = 50  # rough average across languages; this is an estimate, labelled as such

SCALE = 1.25
TILE_W = round(176 * SCALE)
TILE_H = round(100 * SCALE)
GAP = round(16 * SCALE)
OUTER_PAD = round(12 * SCALE)
VALUE_SIZE = round(26 * SCALE)
LABEL_SIZE = round(12 * SCALE)
COLS = 3

TILES = [
    ("commits", "Total Commits", lambda v: f"{v:,}"),
    ("stars", "Total Stars", lambda v: f"{v:,}"),
    ("streak", "Longest Streak", lambda v: f"{v} days"),
    ("repos", "Public Repos", lambda v: f"{v:,}"),
    ("loc", "Lines of Code (est.)", lambda v: f"~{v:,}"),
    ("active_days", "Days With a Commit", lambda v: f"{v:,}"),
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
    total_bytes = sum(language_bytes().values())

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
        "loc": round(total_bytes / BYTES_PER_LINE),
        "active_days": len([d for d in all_days if d["contributionCount"] > 0]),
    }


def build(p, stats):
    rows = -(-len(TILES) // COLS)  # ceil
    w = OUTER_PAD * 2 + COLS * TILE_W + (COLS - 1) * GAP
    h = OUTER_PAD * 2 + rows * TILE_H + (rows - 1) * GAP
    svg = [svgkit.svg_open(w, h, p)]

    for i, (key, label, fmt) in enumerate(TILES):
        col, row = i % COLS, i // COLS
        x = OUTER_PAD + col * (TILE_W + GAP)
        y = OUTER_PAD + row * (TILE_H + GAP)
        svg.append(svgkit.panel(x, y, TILE_W, TILE_H, p))
        cx = x + TILE_W / 2
        svg.append(svgkit.text(cx, y + TILE_H / 2 - 8, fmt(stats[key]), p, size=VALUE_SIZE, anchor="middle", color=p["accent"], weight="700"))
        svg.append(svgkit.text(cx, y + TILE_H / 2 + VALUE_SIZE - 10, label, p, size=LABEL_SIZE, anchor="middle", color=p["subtext"]))

    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    stats = compute_stats()
    svgkit.render_pair(lambda p: build(p, stats), "assets/card-stats-dark.svg", "assets/card-stats-light.svg")
