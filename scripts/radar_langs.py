"""
Generates assets/radar-langs-dark.svg and assets/radar-langs-light.svg — a
radar of the top languages by real byte-count across all non-fork repos
(live GitHub API), reusing the drawing code from radar.py.
"""
import svgkit
from gh_api import language_bytes
from radar import draw, RADIUS

CURVE = 0.4  # < 1 compresses large values so one dominant language doesn't
             # collapse the polygon into a single spike


def top_languages(n=7):
    totals = language_bytes()
    total_bytes = sum(totals.values()) or 1
    pct = {k: v / total_bytes * 100 for k, v in totals.items()}
    ranked = sorted(pct.items(), key=lambda kv: kv[1], reverse=True)[:n]
    return dict(ranked)


def build(p):
    raw = top_languages()
    scaled = {k: v**CURVE for k, v in raw.items()}
    w, h = 572, 418  # same canvas as radar.py's build() — matched pair, no
                      # caption row eating into it, so both panels line up
    svg = [svgkit.svg_open(w, h, p), svgkit.panel(11, 11, w - 22, h - 22, p)]
    svg.append(draw(w / 2, h / 2 + 7, RADIUS, list(scaled.keys()), list(scaled.values()), p, value_labels=list(raw.values())))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    svgkit.render_pair(build, "assets/radar-langs-dark.svg", "assets/radar-langs-light.svg")
