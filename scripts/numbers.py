"""
Generates assets/numbers-dark.svg and assets/numbers-light.svg — the
most-used-languages breakdown (live GitHub API, real byte counts across
all non-fork repos), styled to match every other chart in assets/.

No stat grid here (stars/repos/followers/streaks) — card_stats.py and
commit_line.py already cover commit/repo/activity numbers elsewhere in
the profile, so this stays scoped to languages only rather than
duplicating them.

Transparent background, same reasoning as hero.py: this is meant to sit
directly in the page flow (and get reused on the portfolio site, where it
composites over that page's own background), not inside a bordered card,
so there's no svgkit.panel() here and no opaque background rect.

Language bytes reuse gh_api.language_bytes() (same source as the language
radar). Dot colors are GitHub's own linguist colors where known, falling
back to the theme's subtext gray for anything obscure enough not to be
worth hardcoding.
"""
import svgkit
from gh_api import language_bytes

CANVAS_W = 620
PAD = 4

BAR_H = 10
LANG_COLS = 2
LANG_ROW_H = 24
MAX_LANGS = 8

LANG_COLORS = {
    "JavaScript": "#f1e05a", "TypeScript": "#3178c6", "Python": "#3572A5",
    "CSS": "#563d7c", "HTML": "#e34c26", "Shell": "#89e051",
    "PowerShell": "#012456", "Dockerfile": "#384d54", "Java": "#b07219",
    "PLpgSQL": "#336790", "SQL": "#e38c00", "Jupyter Notebook": "#DA5B0B",
    "C": "#555555", "C++": "#f34b7d", "Go": "#00ADD8", "Rust": "#dea584",
    "Ruby": "#701516", "PHP": "#4F5D95", "Swift": "#F05138",
    "Kotlin": "#A97BFF", "Vue": "#41b883", "SCSS": "#c6538c",
}


def fmt_size(n):
    if n >= 1_000_000:
        return f"{n / 1_000_000:.2f} MB"
    if n >= 1_000:
        return f"{n / 1_000:.0f} kB"
    return f"{n} B"


def compute_stats():
    totals = language_bytes()
    total_bytes = sum(totals.values()) or 1
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:MAX_LANGS]
    return {
        "languages": [(name, n, n / total_bytes * 100) for name, n in ranked],
        "lang_count": len(totals),
    }


def build(p, s):
    lang_rows = -(-len(s["languages"]) // LANG_COLS)

    y = PAD
    caption_y = y
    y += 22
    bar_y = y
    y += BAR_H
    y += 18  # gap before legend
    legend_top = y
    y += lang_rows * LANG_ROW_H
    h = y + PAD

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W}" height="{h}" '
        f'viewBox="0 0 {CANVAS_W} {h}" font-family="{svgkit.FONT_MONO}">'
    ]

    svg.append(svgkit.text(CANVAS_W / 2, caption_y + 14, f"{s['lang_count']} languages · most used, by bytes", p, size=11, anchor="middle", color=p["subtext"]))

    bar_w = CANVAS_W - 2 * PAD
    clip_id = "numbers-bar-clip"
    svg.append(f'<clipPath id="{clip_id}"><rect x="{PAD}" y="{bar_y}" width="{bar_w}" height="{BAR_H}" rx="{BAR_H / 2}"/></clipPath>')
    svg.append(f'<g clip-path="url(#{clip_id})">')
    svg.append(f'<rect x="{PAD}" y="{bar_y}" width="{bar_w}" height="{BAR_H}" fill="{p["border"]}"/>')
    cursor = PAD
    for name, _, pct in s["languages"]:
        seg_w = bar_w * pct / 100
        color = LANG_COLORS.get(name, p["subtext"])
        svg.append(f'<rect x="{cursor:.1f}" y="{bar_y}" width="{seg_w:.1f}" height="{BAR_H}" fill="{color}"/>')
        cursor += seg_w
    svg.append("</g>")

    col_w = (CANVAS_W - 2 * PAD) / LANG_COLS
    for i, (name, n, pct) in enumerate(s["languages"]):
        col, row = i % LANG_COLS, i // LANG_COLS
        lx = PAD + col * col_w
        ly = legend_top + row * LANG_ROW_H + 14
        color = LANG_COLORS.get(name, p["subtext"])
        svg.append(f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4.5" fill="{color}"/>')
        svg.append(svgkit.text(lx + 16, ly, name, p, size=12, color=p["text"]))
        stat_str = f"{fmt_size(n)}  {pct:.2f}%"
        svg.append(svgkit.text(lx + col_w - 6, ly, stat_str, p, size=11, anchor="end", color=p["subtext"]))

    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    stats = compute_stats()
    svgkit.render_pair(lambda p: build(p, stats), "assets/numbers-dark.svg", "assets/numbers-light.svg")
