"""
Generates assets/commit-line-dark.svg and assets/commit-line-light.svg — a
self-drawing animated line graph of weekly commit activity over the
trailing year.

Data: gh_api.public_commits() (Search Commits API, public repos only —
same dataset the stat-card totals are built from) filtered to the last
WINDOW_DAYS days, bucketed into Mon-Sun weeks including zero-commit weeks
so spacing stays even. No fallback/sample data is ever generated — if the
fetch comes back empty the chart just shows zeros, which is the honest
result, not a randomly-generated stand-in for it.

Animation: the line draws itself in via SMIL stroke-dashoffset — the only
animation mechanism that survives a GitHub README's <img> embed (no CSS,
no JS reaches through that boundary). At weekly resolution the point count
is low enough (~52) that markers are drawn visibly rather than hover-only,
so — unlike the daily version this replaced — every element here actually
renders on the live GitHub profile, no viewing caveats.
"""
import datetime as dt
import math

import svgkit
from gh_api import public_commits

WINDOW_DAYS = 365
DRAW_DURATION = 2.2  # seconds


def fetch_series():
    commit_dates = public_commits()
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    today = now.date()
    window_start_day = today - dt.timedelta(days=WINDOW_DAYS - 1)
    first_monday = window_start_day - dt.timedelta(days=window_start_day.weekday())
    current_monday = today - dt.timedelta(days=today.weekday())

    counts = {}
    for d in commit_dates:
        day = d.date()
        if day < window_start_day:
            continue
        week_start = day - dt.timedelta(days=day.weekday())
        counts[week_start] = counts.get(week_start, 0) + 1

    series, cursor = [], first_monday
    while cursor <= current_monday:
        series.append({"date": cursor.isoformat(), "commits": counts.get(cursor, 0)})
        cursor += dt.timedelta(days=7)
    return series or [{"date": current_monday.isoformat(), "commits": 0}]


def build(p, series):
    w, h = 760, 260
    pad_l, pad_r, pad_t, pad_b = 46, 20, 30, 34
    plot_w, plot_h = w - pad_l - pad_r, h - pad_t - pad_b

    n = len(series)
    values = [pt["commits"] for pt in series]
    max_v = max(values, default=0) or 1
    max_idx = values.index(max_v) if any(values) else 0
    total = sum(values)
    active_weeks = sum(1 for v in values if v > 0)
    avg = total / n if n else 0

    def px(i):
        return pad_l + (plot_w * i / max(n - 1, 1))

    def py(v):
        return pad_t + plot_h - (plot_h * v / max_v)

    pts = [(px(i), py(v)) for i, v in enumerate(values)]

    svg = [svgkit.svg_open(w, h, p), svgkit.panel(10, 10, w - 20, h - 20, p)]

    for frac in (0.0, 0.33, 0.66, 1.0):
        gy = pad_t + plot_h * frac
        svg.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{w - pad_r}" y2="{gy:.1f}" stroke="{p["grid"]}" stroke-width="1" opacity="0.5"/>')

    caption = f"commit activity · weekly · {active_weeks}/{n} active weeks · avg {avg:.1f}/wk"
    svg.append(svgkit.text(pad_l, pad_t - 10, caption, p, size=11, color=p["subtext"]))

    # static area fill under the line
    area_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area_d += f" L {pts[-1][0]:.1f},{pad_t + plot_h:.1f} L {pts[0][0]:.1f},{pad_t + plot_h:.1f} Z"
    svg.append(f'<path d="{area_d}" fill="{p["accent"]}" fill-opacity="0.12" stroke="none"/>')

    # the main line, self-drawing left to right via stroke-dashoffset
    line_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    length = max(sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))), 1)
    svg.append(
        f'<path d="{line_d}" fill="none" stroke="{p["accent"]}" stroke-width="2" '
        f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
        f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" '
        f'dur="{DRAW_DURATION}s" begin="0s" fill="freeze" calcMode="linear"/>'
        f"</path>"
    )

    # visible weekly markers — at ~52 points this doesn't clutter the way
    # the daily version did, so no hover-gating needed here
    for i, (x, y) in enumerate(pts):
        commits = values[i]
        title = f"week of {series[i]['date']}: {commits} commit{'s' if commits != 1 else ''}"
        svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{p["accent"]}" stroke="{p["panel"]}" stroke-width="1"><title>{title}</title></circle>')

    # peak annotation, drawn directly on the chart rather than only in the caption
    if any(values):
        peak_x, peak_y = pts[max_idx]
        label_y = peak_y - 12 if peak_y - 12 > pad_t + 4 else peak_y + 18
        svg.append(svgkit.text(peak_x, label_y, f"peak {max_v}", p, size=10, anchor="middle", color=p["accent"], weight="700"))

    label_idxs = sorted(set([0, n // 4, n // 2, (3 * n) // 4, n - 1]))
    for i in label_idxs:
        anchor = "start" if i == 0 else "end" if i == n - 1 else "middle"
        svg.append(svgkit.text(pts[i][0], h - 14, series[i]["date"], p, size=10, anchor=anchor, color=p["subtext"]))

    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    commit_series = fetch_series()
    svgkit.render_pair(lambda p: build(p, commit_series), "assets/commit-line-dark.svg", "assets/commit-line-light.svg")
