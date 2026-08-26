"""
Generates the three project-card SVGs referenced in the README's
'Featured work' table (assets/card-<slug>-dark.svg / -light.svg), from
assets/projects.json.
"""
import json
import textwrap

import svgkit


def load_projects():
    with open("assets/projects.json", encoding="utf-8") as f:
        return json.load(f)


def build_card(project, p):
    w, h = 420, 190
    svg = [svgkit.svg_open(w, h, p), svgkit.panel(6, 6, w - 12, h - 12, p)]
    svg.append(f'<rect x="6" y="6" width="6" height="{h - 12}" rx="3" fill="{p["accent"]}"/>')
    svg.append(svgkit.text(30, 40, project["name"], p, size=18, weight="700"))
    svg.append(svgkit.text(30, 62, project["stack"], p, size=11, color=p["accent"]))
    for i, line in enumerate(textwrap.wrap(project["description"], width=52)[:4]):
        svg.append(svgkit.text(30, 92 + i * 18, line, p, size=12, color=p["subtext"]))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


def render():
    for project in load_projects():
        slug = project["slug"]
        svgkit.render_pair(
            lambda p, proj=project: build_card(proj, p),
            f"assets/card-{slug}-dark.svg",
            f"assets/card-{slug}-light.svg",
        )


if __name__ == "__main__":
    render()
