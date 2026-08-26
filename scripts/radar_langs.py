"""
Generates assets/radar-langs-dark.svg and assets/radar-langs-light.svg — a
radar of the top languages by real byte-count across all non-fork repos
(live GitHub API), reusing the drawing code from radar.py.
"""
import svgkit
from gh_api import USER, language_bytes
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
    w, h = 560, 460
    svg = [svgkit.svg_open(w, h, p), svgkit.panel(10, 10, w - 20, h - 20, p)]
    svg.append(svgkit.text(w / 2, 34, f"{USER} · language mix", p, size=12, anchor="middle", color=p["subtext"]))
    svg.append(draw(w / 2, h / 2 + 22, RADIUS, list(scaled.keys()), list(scaled.values()), p, value_labels=list(raw.values())))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    svgkit.render_pair(build, "assets/radar-langs-dark.svg", "assets/radar-langs-light.svg")
