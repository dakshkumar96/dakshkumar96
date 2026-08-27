"""
Generates the project-card SVGs referenced in the README's 'Featured work'
table (assets/card-<slug>-dark.svg / -light.svg), from assets/projects.json.
"""
import json
import textwrap

import svgkit


def load_projects():
    with open("assets/projects.json", encoding="utf-8") as f:
        return json.load(f)


WRAP_WIDTH = 48  # chars; tuned for Courier New (wider per-char than the old font) at font-size 12
MAX_LINES = 6     # hard ceiling so one very long description can't run off the card
LINE_HEIGHT = 18
DESC_TOP = 92


def wrapped_description(project):
    return textwrap.wrap(project["description"], width=WRAP_WIDTH)[:MAX_LINES]


def build_card(project, p, height):
    w = 420
    svg = [svgkit.svg_open(w, height, p), svgkit.panel(6, 6, w - 12, height - 12, p)]
    svg.append(f'<rect x="6" y="6" width="6" height="{height - 12}" rx="3" fill="{p["accent"]}"/>')
    svg.append(svgkit.text(30, 40, project["name"], p, size=18, weight="700"))
    svg.append(svgkit.text(30, 62, project["stack"], p, size=11, color=p["accent"]))
    for i, line in enumerate(wrapped_description(project)):
        svg.append(svgkit.text(30, DESC_TOP + i * LINE_HEIGHT, line, p, size=12, color=p["subtext"]))
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


def render():
    projects = load_projects()
    # every card gets the same height (tallest description's line count),
    # so the README's 2x2 grid doesn't end up with mismatched row heights
    max_lines = max(len(wrapped_description(proj)) for proj in projects)
    height = DESC_TOP + max_lines * LINE_HEIGHT + 20

    for project in projects:
        slug = project["slug"]
        svgkit.render_pair(
            lambda p, proj=project: build_card(proj, p, height),
            f"assets/card-{slug}-dark.svg",
            f"assets/card-{slug}-light.svg",
        )


if __name__ == "__main__":
    render()
