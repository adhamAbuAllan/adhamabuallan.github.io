"""Build Sahl logo SVGs with real glyph outlines (no font needed to display)."""
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen

AR = "ttf/ibm-plex-sans-arabic-arabic-700-normal.ttf"
LAT = "ttf/inter-latin-700-normal.ttf"


def shape_path(font_path, text, direction, size, x0=0.0, y0=0.0):
    """Return (svg path d, width, bounds) for text set at `size` px, baseline at y0."""
    blob = hb.Blob.from_file_path(font_path)
    face = hb.Face(blob)
    font = hb.Font(face)
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    buf.direction = direction
    hb.shape(font, buf, {"kern": True, "liga": True})
    tt = TTFont(font_path)
    gs = tt.getGlyphSet()
    order = tt.getGlyphOrder()
    upem = tt["head"].unitsPerEm
    scale = size / upem
    pen = SVGPathPen(gs)
    bpen = BoundsPen(gs)
    x = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        name = order[info.codepoint]
        t = (scale, 0, 0, -scale, x0 + (x + pos.x_offset) * scale, y0 - pos.y_offset * scale)
        gs[name].draw(TransformPen(pen, t))
        gs[name].draw(TransformPen(bpen, t))
        x += pos.x_advance
    return pen.getCommands(), x * scale, bpen.bounds


def wordmark(path_out, color="#22C55E", latin_color="#F5F7F5"):
    d_ar, w_ar, b_ar = shape_path(AR, "سهل", "rtl", 160, 0, 170)
    d_la, w_la, b_la = shape_path(LAT, "Sahl Digital", "ltr", 44, 0, 300)
    # centre both lines on the wider one
    W = max(b_ar[2] - b_ar[0], b_la[2] - b_la[0]) + 48
    dx_ar = (W - (b_ar[2] - b_ar[0])) / 2 - b_ar[0]
    dx_la = (W - (b_la[2] - b_la[0])) / 2 - b_la[0]
    H = 330
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H}" width="{W:.0f}" height="{H}">
<title>Sahl Digital</title>
<path transform="translate({dx_ar:.1f},0)" fill="{color}" d="{d_ar}"/>
<path transform="translate({dx_la:.1f},0)" fill="{latin_color}" d="{d_la}"/>
</svg>'''
    open(path_out, "w").write(svg)
    return W, H


def mark(path_out, size=1024, bg="#0A0A0A", fg="#22C55E", dot=True):
    """Square mark: سهل centred on a dark ground (safe inside a circle crop)."""
    d, w, b = shape_path(AR, "سهل", "rtl", 420, 0, 0)
    gw, gh = b[2] - b[0], b[3] - b[1]
    cx = (size - gw) / 2 - b[0]
    cy = (size - gh) / 2 - b[1] - (40 if dot else 0)
    dot_svg = f'<circle cx="{size/2:.0f}" cy="{size*0.74:.0f}" r="{size*0.035:.0f}" fill="{fg}"/>' if dot else ""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">
<title>Sahl Digital mark</title>
<rect width="{size}" height="{size}" fill="{bg}"/>
<path transform="translate({cx:.1f},{cy:.1f})" fill="{fg}" d="{d}"/>
{dot_svg}
</svg>'''
    open(path_out, "w").write(svg)


if __name__ == "__main__":
    import os
    os.makedirs("out/brand", exist_ok=True)
    print(wordmark("out/brand/sahl-wordmark.svg"))
    wordmark("out/brand/sahl-wordmark-light.svg", color="#15803D", latin_color="#0A0A0A")
    mark("out/brand/sahl-mark.svg", dot=False)
    print("ok")
