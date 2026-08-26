"""
Generates assets/commit-line-dark.svg and assets/commit-line-light.svg — a
self-drawing animated line graph of commit activity over time.

Data: ~30 buckets spanning the account's full history. Bucket size is just
elapsed_days / 30, so it naturally comes out to roughly a day for a young
account and roughly a week for an older one — no special-casing needed.
Each bucket's count comes from GraphQL contributionsCollection(from, to)
.totalCommitContributions, which is the only field that reports *commits*
specifically rather than all contribution types combined.

Animation: pure SVG SMIL (<animate>/<animateTransform>) — no CSS, no JS.
This renders as a static .svg file embedded via <img> in a GitHub README,
and SMIL is the only animation mechanism that survives that embedding.
The line draws itself in via stroke-dashoffset over DRAW_DURATION seconds;
each point marker fades + scales in just after the line reaches it. Runs
once (SMIL's default is a single play — no repeatCount is set).
"""
import datetime as dt
import math

import svgkit
from gh_api import contributions, profile

TARGET_POINTS = 30
DRAW_DURATION = 2.2  # seconds


def bucket_windows():
    created_at = profile()["created_at"]
    start = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00")).replace(tzinfo=None)
    now = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
    elapsed_days = max((now - start).days, 1)
    bucket_days = max(1, round(elapsed_days / TARGET_POINTS))

    windows, cursor = [], start
    while cursor < now:
        end = min(cursor + dt.timedelta(days=bucket_days), now)
        windows.append((cursor, end))
        cursor = end
    return windows or [(start, now)]


def fetch_series():
    points = []
    for frm, to in bucket_windows():
        data = contributions(frm.isoformat() + "Z", to.isoformat() + "Z")
        points.append({"date": to.date().isoformat(), "commits": data["totalCommitContributions"]})
    return points


def build(p, series):
    w, h = 760, 260
    pad_l, pad_r, pad_t, pad_b = 46, 20, 30, 34
    plot_w, plot_h = w - pad_l - pad_r, h - pad_t - pad_b

    n = len(series)
    values = [pt["commits"] for pt in series]
    max_v = max(values, default=0) or 1

    def px(i):
        return pad_l + (plot_w * i / max(n - 1, 1))

    def py(v):
        return pad_t + plot_h - (plot_h * v / max_v)

    pts = [(px(i), py(v)) for i, v in enumerate(values)]

    svg = [svgkit.svg_open(w, h, p), svgkit.panel(10, 10, w - 20, h - 20, p)]

    for frac in (0.0, 0.33, 0.66, 1.0):
        gy = pad_t + plot_h * frac
        svg.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{w - pad_r}" y2="{gy:.1f}" stroke="{p["grid"]}" stroke-width="1" opacity="0.5"/>')

    svg.append(svgkit.text(pad_l, pad_t - 10, f"commit activity over time · peak {max_v}", p, size=11, color=p["subtext"]))

    # static area fill under the line
    area_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area_d += f" L {pts[-1][0]:.1f},{pad_t + plot_h:.1f} L {pts[0][0]:.1f},{pad_t + plot_h:.1f} Z"
    svg.append(f'<path d="{area_d}" fill="{p["accent"]}" fill-opacity="0.12" stroke="none"/>')

    # the line, self-drawing left to right via stroke-dashoffset
    line_d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    length = max(sum(math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]) for i in range(1, len(pts))), 1)
    svg.append(
        f'<path d="{line_d}" fill="none" stroke="{p["accent"]}" stroke-width="2" '
        f'stroke-dasharray="{length:.1f}" stroke-dashoffset="{length:.1f}">'
        f'<animate attributeName="stroke-dashoffset" from="{length:.1f}" to="0" '
        f'dur="{DRAW_DURATION}s" begin="0s" fill="freeze" calcMode="linear"/>'
        f"</path>"
    )

    # point markers: fade + scale in shortly after the line reaches each one.
    # A <title> gives a native tooltip, but that only works if the SVG is
    # viewed directly — an <img>-embedded README strips DOM interactivity,
    # so the commit count is also drawn as an always-visible small label
    # (skipped on zero-commit buckets to keep a dense chart readable).
    for i, (x, y) in enumerate(pts):
        t = (i / max(n - 1, 1)) * DRAW_DURATION + 0.05
        commits = values[i]
        title = f"{series[i]['date']}: {commits} commit{'s' if commits != 1 else ''}"
        svg.append(
            f'<g transform="translate({x:.1f},{y:.1f})">'
            f'<circle cx="0" cy="0" r="4" fill="{p["accent"]}" stroke="#FFFFFF" stroke-width="1" opacity="0">'
            f"<title>{title}</title>"
            f'<animate attributeName="opacity" from="0" to="1" begin="{t:.2f}s" dur="0.3s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="scale" from="0" to="1" '
            f'begin="{t:.2f}s" dur="0.3s" fill="freeze" additive="sum"/>'
            f"</circle></g>"
        )
        if commits > 0:
            label_y = y - 10 if y - 10 > pad_t - 4 else y + 16
            svg.append(
                f'<text x="{x:.1f}" y="{label_y:.1f}" text-anchor="middle" fill="{p["subtext"]}" '
                f'font-size="9" opacity="0">{commits}'
                f'<animate attributeName="opacity" from="0" to="1" begin="{t:.2f}s" dur="0.3s" fill="freeze"/>'
                f"</text>"
            )

    label_idxs = sorted(set([0, n // 3, (2 * n) // 3, n - 1]))
    for i in label_idxs:
        # hug the inside edge at the ends instead of centering on the point,
        # so the first/last date label doesn't run off the canvas
        anchor = "start" if i == 0 else "end" if i == n - 1 else "middle"
        svg.append(svgkit.text(pts[i][0], h - 14, series[i]["date"], p, size=10, anchor=anchor, color=p["subtext"]))

    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    commit_series = fetch_series()
    svgkit.render_pair(lambda p: build(p, commit_series), "assets/commit-line-dark.svg", "assets/commit-line-light.svg")
