"""
Shared SVG drawing primitives and the two palettes (dark / light) every
generated asset in assets/ must use. The README switches images via
<picture><source media="(prefers-color-scheme: ...)"> so every chart needs
a real dark AND light render — this is the one place that pairing lives,
so nothing drifts to a different look than the rest.
"""

FONT_MONO = "'JetBrains Mono','SFMono-Regular',Consolas,monospace"

PALETTES = {
    "dark": dict(
        bg="#0D1117",
        panel="#161B22",
        border="#30363D",
        grid="#30363D",
        accent="#3B82F6",
        accent_dim="#1E40AF",
        accent_light="#93C5FD",
        text="#F0F6FC",
        subtext="#8B949E",
    ),
    "light": dict(
        bg="#FFFFFF",
        panel="#F6F8FA",
        border="#D0D7DE",
        grid="#D0D7DE",
        accent="#3B82F6",
        accent_dim="#1E40AF",
        accent_light="#93C5FD",
        text="#1F2328",
        subtext="#57606A",
    ),
}

SVG_CLOSE = "</svg>"


def svg_open(w, h, p):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{FONT_MONO}">'
        f'<rect width="{w}" height="{h}" fill="{p["bg"]}"/>'
    )


def panel(x, y, w, h, p, radius=12):
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
        f'fill="{p["panel"]}" stroke="{p["border"]}" stroke-width="1"/>'
    )


def text(x, y, s, p, size=12, anchor="start", color=None, weight=None):
    fill = color or p["text"]
    fw = f' font-weight="{weight}"' if weight else ""
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{fill}" font-size="{size}"{fw}>{s}</text>'


def render_pair(build_fn, dark_path, light_path):
    """Call build_fn(palette) for both themes and write the two files."""
    with open(dark_path, "w", encoding="utf-8") as f:
        f.write(build_fn(PALETTES["dark"]))
    with open(light_path, "w", encoding="utf-8") as f:
        f.write(build_fn(PALETTES["light"]))
