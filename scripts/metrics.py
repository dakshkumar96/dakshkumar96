"""
Generates assets/metrics.dark.svg and assets/metrics.light.svg — a
GitHub-style contribution heatmap for the trailing 12 months (the
'Activity' section's calendar chart).
"""
import datetime as dt

import svgkit
from gh_api import contributions


def build(p):
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    frm = (now - dt.timedelta(days=364)).isoformat() + "Z"
    to = now.isoformat() + "Z"
    calendar = contributions(frm, to)["contributionCalendar"]
    weeks = calendar["weeks"]

    cell, gap = 11, 3
    grid_top = 36
    grid_height = 7 * cell + 6 * gap  # 7 rows (Sun–Sat), fixed regardless of week count
    caption_y = grid_top + grid_height + 24

    w = 40 + len(weeks) * (cell + gap)
    h = caption_y + 20
    svg = [svgkit.svg_open(w, h, p), svgkit.panel(10, 10, w - 20, h - 20, p)]

    max_count = max((d["contributionCount"] for wk in weeks for d in wk["contributionDays"]), default=1) or 1
    for wi, week in enumerate(weeks):
        for di, day in enumerate(week["contributionDays"]):
            x = 30 + wi * (cell + gap)
            y = grid_top + di * (cell + gap)
            count = day["contributionCount"]
            opacity = 0.10 if count == 0 else round(0.3 + 0.7 * (count / max_count), 2)
            svg.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2" fill="{p["accent"]}" opacity="{opacity}"/>')

    svg.append(svgkit.text(30, caption_y, f'{calendar["totalContributions"]} contributions in the last year', p, size=11, color=p["subtext"]))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    svgkit.render_pair(build, "assets/metrics.dark.svg", "assets/metrics.light.svg")
