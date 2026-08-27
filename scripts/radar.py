"""
Generates assets/radar-dark.svg and assets/radar-light.svg — the self-rated
skill radar from assets/skills.json (static; edit that file to update it).
"""
import json
import math

import svgkit

RADIUS = 105
LABEL_GAP = 26
LABEL_MAX_CHARS = 16


def load_skills():
    with open("assets/skills.json", encoding="utf-8") as f:
        return json.load(f)


def polygon_points(cx, cy, r, values, max_value):
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        angle = -math.pi / 2 + i * (2 * math.pi / n)
        radius = r * (v / max_value) if max_value else 0
        pts.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return pts


def draw(cx, cy, r, labels, values, p, value_labels=None):
    n = len(labels)
    parts = []

    for ring in (1, 2, 3):
        ring_r = r * ring / 3
        pts = polygon_points(cx, cy, ring_r, [1] * n, 1)
        d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
        parts.append(f'<path d="{d}" fill="none" stroke="{p["grid"]}" stroke-width="1" opacity="0.6"/>')

    for i in range(n):
        angle = -math.pi / 2 + i * (2 * math.pi / n)
        x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{p["grid"]}" stroke-width="1" opacity="0.6"/>')

    max_v = max(values) if values else 1
    pts = polygon_points(cx, cy, r, values, max_v)
    d = "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    parts.append(f'<path d="{d}" fill="{p["accent"]}" fill-opacity="0.18" stroke="{p["accent"]}" stroke-width="2"/>')
    for x, y in pts:
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{p["accent"]}" stroke="{p["panel"]}" stroke-width="1"/>')

    for i, label in enumerate(labels):
        angle = -math.pi / 2 + i * (2 * math.pi / n)
        lx, ly = cx + (r + LABEL_GAP) * math.cos(angle), cy + (r + LABEL_GAP) * math.sin(angle)
        anchor = "middle"
        if math.cos(angle) > 0.3:
            anchor = "start"
        elif math.cos(angle) < -0.3:
            anchor = "end"
        lines = svgkit.wrap_label(label, max_chars=LABEL_MAX_CHARS)
        # vertically centre a multi-line label on its anchor point instead
        # of always growing downward, so it doesn't drift into the next axis
        start_y = ly - (len(lines) - 1) * 6.5
        label_svg, bottom_y = svgkit.text_lines(lx, start_y, lines, p, size=11, anchor=anchor, color=p["subtext"], line_height=13)
        parts.append(label_svg)
        if value_labels is not None:
            parts.append(svgkit.text(lx, bottom_y + 14, f"{value_labels[i]:.1f}", p, size=10, anchor=anchor))
    return "".join(parts)


def build(p):
    skills = load_skills()
    w, h = 520, 380
    svg = [svgkit.svg_open(w, h, p), svgkit.panel(10, 10, w - 20, h - 20, p)]
    svg.append(draw(w / 2, h / 2 + 6, RADIUS, list(skills.keys()), list(skills.values()), p))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    svgkit.render_pair(build, "assets/radar-dark.svg", "assets/radar-light.svg")
