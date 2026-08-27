"""
Shared SVG drawing primitives and the two palettes (dark / light) every
generated asset in assets/ must use. The README switches images via
<picture><source media="(prefers-color-scheme: ...)"> so every chart needs
a real dark AND light render — this is the one place that pairing lives,
so nothing drifts to a different look than the rest.

Theme: ASCII terminal, dark background, GitHub's own green accent, Courier
monospace. Real Primer green tokens (GitHub's actual design system) —
dark and light each get their own shade, same as GitHub's own UI does,
rather than one compromise value that's too dim on one background or too
loud on the other. Because every script pulls its palette/font from here
instead of hardcoding values, this file is the single place a full
re-theme happens.
"""

FONT_MONO = "'Courier New', Courier, monospace"

PALETTES = {
    "dark": dict(
        bg="#0D1117",
        panel="#161B22",
        border="#30363D",
        grid="#30363D",
        accent="#3FB950",       # GitHub Primer green.4 (dark mode)
        accent_dim="#238636",   # Primer green.6
        accent_light="#7EE787", # Primer green.2
        text="#F0F6FC",
        subtext="#8B949E",
    ),
    "light": dict(
        bg="#FFFFFF",
        panel="#F6F8FA",
        border="#D0D7DE",
        grid="#D0D7DE",
        accent="#1A7F37",       # GitHub Primer green.6 (light mode)
        accent_dim="#116329",   # Primer green.8
        accent_light="#4AC26B", # Primer green.3
        text="#1F2328",
        subtext="#57606A",
    ),
}

SVG_CLOSE = "</svg>"


def svg_open(w, h, p):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT_MONO}">'
        f"<defs>"
        f'<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">'
        f'<feGaussianBlur stdDeviation="2.2" result="blur"/>'
        f'<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f"</filter>"
        f"</defs>"
        f'<rect width="{w}" height="{h}" fill="{p["bg"]}"/>'
    )


def panel(x, y, w, h, p, radius=12):
    """The rounded card every chart sits inside, drawn over the existing
    rect bounds so no caller has to change its content coordinates to
    use this."""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{p["panel"]}" stroke="{p["border"]}" stroke-width="1"/>'
    )


def text(x, y, s, p, size=12, anchor="start", color=None, weight=None, glow=False):
    fill = color or p["text"]
    fw = f' font-weight="{weight}"' if weight else ""
    fl = ' filter="url(#glow)"' if glow else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" font-size="{size}"{fw}{fl}>{s}</text>'


def wrap_label(label, max_chars=18, max_lines=2):
    """Greedy word-wrap for axis/legend labels, so a long label (e.g.
    'Statistics / Survival Analysis') breaks into short stacked lines
    instead of running off the edge of the canvas as one long string."""
    if len(label) <= max_chars:
        return [label]
    words = label.split()
    lines, cur = [], ""
    for word in words:
        if len(lines) >= max_lines - 1:
            # already on the last allowed line — keep appending rather than
            # drop words, even if it runs a little long
            cur = f"{cur} {word}".strip()
            continue
        candidate = f"{cur} {word}".strip()
        if len(candidate) <= max_chars or not cur:
            cur = candidate
        else:
            lines.append(cur)
            cur = word
    lines.append(cur)
    return lines


def text_lines(x, y, lines, p, size=11, anchor="middle", color=None, line_height=13):
    """Stack of <text> elements, top line at y. Returns (svg, bottom_y) so
    callers can position what comes next (e.g. a value label) below it."""
    fill = color or p["subtext"]
    parts = []
    for i, line in enumerate(lines):
        parts.append(f'<text x="{x}" y="{y + i * line_height}" text-anchor="{anchor}" fill="{fill}" font-size="{size}">{line}</text>')
    bottom_y = y + (len(lines) - 1) * line_height
    return "".join(parts), bottom_y


def render_pair(build_fn, dark_path, light_path):
    """Call build_fn(palette) for both themes and write the two files."""
    with open(dark_path, "w", encoding="utf-8") as f:
        f.write(build_fn(PALETTES["dark"]))
    with open(light_path, "w", encoding="utf-8") as f:
        f.write(build_fn(PALETTES["light"]))
