"""
Generates assets/card-stats-dark.svg and assets/card-stats-light.svg — a
single row of four stat tiles: total commits, public repos, days with a
commit, and profile views.

Commits and active-days both come from gh_api.public_commits(), which
walks the GitHub Search Commits API — public repos only, regardless of
what the calling token could otherwise see — so those two numbers can
never disagree with each other or with the commit-activity line chart,
which is built from that exact same dataset. Public repo count already
comes from the public-only /users/{user}/repos listing. Profile views is
a live read of the komarev badge already in the README (see
gh_api.profile_views for the caveats on that number).
"""
import svgkit
from gh_api import all_repos, profile_views, public_commits

SCALE = 1.25 * 0.7
TILE_W = round(176 * SCALE)
TILE_H = round(100 * SCALE)
GAP = round(16 * SCALE)
OUTER_PAD = round(12 * SCALE)
VALUE_SIZE = round(26 * SCALE)
LABEL_SIZE = round(12 * SCALE)
COLS = 4

TILES = [
    ("commits", "Total Commits", lambda v: f"{v:,}"),
    ("repos", "Public Repos", lambda v: f"{v:,}"),
    ("active_days", "Days With a Commit", lambda v: f"{v:,}"),
    ("views", "Profile Views", lambda v: f"{v:,}"),
]


def compute_stats():
    repos = all_repos()
    total_repos = len([r for r in repos if not r.get("fork")])

    commit_dates = public_commits()
    active_days = len({d.date() for d in commit_dates})

    return {
        "commits": len(commit_dates),
        "repos": total_repos,
        "active_days": active_days,
        "views": profile_views(),
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
