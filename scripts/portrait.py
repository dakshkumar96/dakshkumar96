"""
Generates assets/portrait.svg — a placeholder initials badge, since there's
no real headshot asset checked into the repo. Swap this file out directly
if a real photo/illustration is ever added; the README already points at
this exact path.
"""
import svgkit


def render(path="assets/portrait.svg"):
    p = svgkit.PALETTES["dark"]
    w = h = 220
    svg = [svgkit.svg_open(w, h, p)]
    svg.append(f'<circle cx="{w/2}" cy="{h/2}" r="{w/2 - 6}" fill="{p["panel"]}" stroke="{p["accent"]}" stroke-width="3"/>')
    svg.append(svgkit.text(w / 2, h / 2 + 22, "DK", p, size=64, anchor="middle", color=p["accent"], weight="700"))
    svg.append(svgkit.SVG_CLOSE)
    with open(path, "w", encoding="utf-8") as f:
        f.write("".join(svg))


if __name__ == "__main__":
    render()
