"""
Generates assets/hero-dark.svg and assets/hero-light.svg — "Hi, I'm Daksh"
rendered as real vector text with a blinking terminal-style cursor block,
replacing the plain markdown heading.

This exists specifically because CSS effects don't survive on GitHub: a
README is sanitized before rendering, and <style> blocks / :hover rules /
@keyframes are stripped entirely — there is no config that keeps them. An
image is the only way to get an actually-animated or actually-colored
piece of "text" onto the live profile page, which is why this is an SVG
with a real vector <text> element rather than a styled heading.

Animation: SMIL opacity keyframes on the cursor block, looping forever
(repeatCount="indefinite") — unlike the dashboard charts elsewhere, which
each animate once on load, a cursor is expected to blink continuously for
as long as it's on screen.

No filled background (unlike every other chart here) — this sits directly
in the page flow like a heading, not inside a bordered panel, so it needs
to be transparent and let GitHub's own page background show through.
"""
import svgkit

TEXT = "Hi, I'm Daksh"
FONT_SIZE = 40
CHAR_W = FONT_SIZE * 0.6  # Courier New is fixed-pitch, so this is exact enough


def build(p):
    text_w = len(TEXT) * CHAR_W
    cursor_x = 10 + text_w + 10
    cursor_w, cursor_h = 20, 46
    w = round(cursor_x + cursor_w + 12)
    h = 70

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" font-family="{svgkit.FONT_MONO}">'
        f"<defs>"
        f'<filter id="cursor-glow" x="-80%" y="-80%" width="260%" height="260%">'
        f'<feGaussianBlur stdDeviation="2" result="blur"/>'
        f'<feMerge><feMergeNode in="blur"/><feMergeNode in="SourceGraphic"/></feMerge>'
        f"</filter>"
        f"</defs>"
    ]
    svg.append(f'<text x="10" y="50" font-size="{FONT_SIZE}" font-weight="700" fill="{p["text"]}">{TEXT}</text>')
    svg.append(
        f'<rect x="{cursor_x:.0f}" y="14" width="{cursor_w}" height="{cursor_h}" fill="{p["accent"]}" filter="url(#cursor-glow)">'
        f'<animate attributeName="opacity" values="1;1;0;0;1" keyTimes="0;0.45;0.5;0.95;1" '
        f'dur="1.1s" repeatCount="indefinite"/>'
        f"</rect>"
    )
    svg.append(svgkit.SVG_CLOSE)
    return "".join(svg)


if __name__ == "__main__":
    svgkit.render_pair(build, "assets/hero-dark.svg", "assets/hero-light.svg")
