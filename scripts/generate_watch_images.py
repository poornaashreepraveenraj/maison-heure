"""Generate clean placeholder SVG watch illustrations for the seed catalogue.

    python scripts/generate_watch_images.py

Writes static/img/watches/<slug>-<1..4>.svg (front, angled, caseback, side)
plus static/img/hero-watch.svg and static/img/watch-placeholder.svg.
The drawings are generic and carry no brand names or logos; replace them with
your own licensed product photos by uploading images in /admin/.
"""
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from store.catalogue_data import WATCHES  # noqa: E402

OUT_DIR = ROOT / "static" / "img" / "watches"
GOLD = "#c8a45d"
METALS = {"#b8bbbe", "#a9adb0", "#c9ccce", "#e1e2e3"}
CX = CY = 300


def shade(hex_colour, factor):
    """factor < 1 darkens, > 1 lightens."""
    h = hex_colour.lstrip("#")
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    if factor < 1:
        rgb = [int(c * factor) for c in rgb]
    else:
        rgb = [int(c + (255 - c) * (factor - 1)) for c in rgb]
    return "#" + "".join(f"{max(0, min(255, c)):02x}" for c in rgb)


def is_dark(hex_colour):
    h = hex_colour.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) < 140


def polar(r, degrees):
    a = math.radians(degrees - 90)
    return CX + r * math.cos(a), CY + r * math.sin(a)


def defs(look):
    case = look["case"]
    return (
        "<defs>"
        f'<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="{shade(case, 1.25)}"/><stop offset=".5" stop-color="{case}"/>'
        f'<stop offset="1" stop-color="{shade(case, 0.72)}"/></linearGradient>'
        f'<radialGradient id="dial" cx=".38" cy=".32" r=".9">'
        f'<stop offset="0" stop-color="{shade(look["dial"], 1.18)}"/><stop offset="1" stop-color="{shade(look["dial"], 0.86)}"/>'
        "</radialGradient></defs>"
    )


def strap(look, cut_top=165, cut_bottom=435):
    colour = look["strap"]
    edge = shade(colour, 0.75)
    parts = [
        f'<rect x="{CX - 68}" y="18" width="136" height="{cut_top - 10}" rx="12" fill="{colour}" stroke="{edge}" stroke-width="2"/>',
        f'<rect x="{CX - 68}" y="{cut_bottom - 8}" width="136" height="{600 - cut_bottom - 10}" rx="12" fill="{colour}" stroke="{edge}" stroke-width="2"/>',
    ]
    if colour in METALS:
        # Bracelet links
        for y in list(range(42, cut_top, 26)) + list(range(cut_bottom + 14, 585, 26)):
            parts.append(f'<line x1="{CX - 66}" y1="{y}" x2="{CX + 66}" y2="{y}" stroke="{edge}" stroke-width="2"/>')
        for x in (CX - 24, CX + 24):
            parts.append(f'<line x1="{x}" y1="20" x2="{x}" y2="{cut_top}" stroke="{edge}" stroke-width="2"/>')
            parts.append(f'<line x1="{x}" y1="{cut_bottom}" x2="{x}" y2="580" stroke="{edge}" stroke-width="2"/>')
    else:
        # Leather/rubber stitching
        for y1, y2 in ((28, cut_top), (cut_bottom, 578)):
            for x in (CX - 56, CX + 56):
                parts.append(
                    f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{shade(colour, 1.35)}" stroke-width="2" stroke-dasharray="7 6"/>'
                )
    return "".join(parts)


def markers(r_out, r_in, colour, lume=True):
    parts = []
    for i in range(12):
        deg = i * 30
        x1, y1 = polar(r_out, deg)
        x2, y2 = polar(r_in if i % 3 else r_in - 10, deg)
        width = 9 if i % 3 == 0 else 6
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colour}" stroke-width="{width}" stroke-linecap="round"/>'
        )
    if lume:
        x, y = polar(r_out - 6, 0)
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{GOLD}"/>')
    return "".join(parts)


def hands(length, colour):
    parts = []
    for deg, ln, width in ((305, length * 0.62, 11), (60, length * 0.92, 8)):
        x, y = polar(ln, deg)
        parts.append(
            f'<line x1="{CX}" y1="{CY}" x2="{x:.1f}" y2="{y:.1f}" stroke="{colour}" stroke-width="{width}" stroke-linecap="round"/>'
        )
    sx, sy = polar(length, 215)
    tx, ty = polar(length * 0.22, 35)
    parts.append(
        f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{sx:.1f}" y2="{sy:.1f}" stroke="{GOLD}" stroke-width="3" stroke-linecap="round"/>'
    )
    parts.append(f'<circle cx="{CX}" cy="{CY}" r="9" fill="{colour}"/><circle cx="{CX}" cy="{CY}" r="3.5" fill="{GOLD}"/>')
    return "".join(parts)


def bezel_ticks(r, colour, count=60):
    parts = []
    for i in range(count):
        long = i % 5 == 0
        x1, y1 = polar(r, i * 360 / count)
        x2, y2 = polar(r - (14 if long else 7), i * 360 / count)
        parts.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{colour}" stroke-width="{3 if long else 1.5}"/>'
        )
    return "".join(parts)


def round_front(look, brand, model):
    shape = look["shape"]
    case_stroke = shade(look["case"], 0.62)
    hand_colour = "#e9ecee" if is_dark(look["dial"]) else "#2e3438"
    marker_colour = "#e9ecee" if is_dark(look["dial"]) else "#2e3438"
    out = []
    # Lugs + crown
    for dx in (-1, 1):
        for dy in (-1, 1):
            out.append(
                f'<rect x="{CX + dx * 112 - 22}" y="{CY + dy * 150 - 30}" width="44" height="60" rx="10" fill="url(#metal)" stroke="{case_stroke}" stroke-width="2"/>'
            )
    out.append(f'<rect x="{CX + 168}" y="{CY - 20}" width="30" height="40" rx="7" fill="url(#metal)" stroke="{case_stroke}" stroke-width="2"/>')
    out.append(f'<circle cx="{CX}" cy="{CY}" r="178" fill="url(#metal)" stroke="{case_stroke}" stroke-width="3"/>')

    if shape == "dive":
        if "bezel2" in look:
            out.append(f'<path d="M {CX - 166} {CY} A 166 166 0 0 1 {CX + 166} {CY} Z" fill="{look["bezel"]}"/>')
            out.append(f'<path d="M {CX - 166} {CY} A 166 166 0 0 0 {CX + 166} {CY} Z" fill="{look["bezel2"]}"/>')
        else:
            out.append(f'<circle cx="{CX}" cy="{CY}" r="166" fill="{look["bezel"]}"/>')
        out.append(bezel_ticks(160, "#d9dbdc"))
        dial_r = 128
    elif shape == "chrono":
        out.append(f'<circle cx="{CX}" cy="{CY}" r="166" fill="{look["bezel"]}"/>')
        out.append(bezel_ticks(160, "#d9dbdc" if is_dark(look["bezel"]) else "#2e3438", count=40))
        dial_r = 132
    else:
        out.append(f'<circle cx="{CX}" cy="{CY}" r="166" fill="{shade(look["bezel"], 1.08)}" stroke="{case_stroke}" stroke-width="1.5"/>')
        if look["bezel"] != look["case"]:  # fluted bezel
            for i in range(72):
                x1, y1 = polar(164, i * 5)
                x2, y2 = polar(146, i * 5)
                out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{case_stroke}" stroke-width="1.2"/>')
        dial_r = 142

    out.append(f'<circle cx="{CX}" cy="{CY}" r="{dial_r}" fill="url(#dial)" stroke="{shade(look["dial"], 0.6)}" stroke-width="2"/>')
    out.append(markers(dial_r - 12, dial_r - 34, marker_colour))

    if shape == "chrono":
        for dx, dy in ((-62, 0), (62, 0), (0, 62)):
            sub = look.get("sub", shade(look["dial"], 0.7))
            out.append(f'<circle cx="{CX + dx}" cy="{CY + dy}" r="32" fill="{sub}" stroke="{shade(sub, 1.5)}" stroke-width="2"/>')
            out.append(f'<line x1="{CX + dx}" y1="{CY + dy}" x2="{CX + dx + 14}" y2="{CY + dy - 20}" stroke="{hand_colour if is_dark(sub) else "#2e3438"}" stroke-width="3" stroke-linecap="round"/>')
    if "date" in model.lower():
        out.append(f'<rect x="{CX + dial_r - 62}" y="{CY - 13}" width="34" height="26" rx="3" fill="#ffffff" stroke="#656565"/>')
        out.append(f'<text x="{CX + dial_r - 45}" y="{CY + 7}" font-family="Poppins, Arial, sans-serif" font-size="18" text-anchor="middle" fill="#0f0e0c">24</text>')
    out.append(hands(dial_r - 20, hand_colour))
    # Crystal reflection
    out.append(f'<path d="M {CX - 110} {CY - 70} A 135 135 0 0 1 {CX + 40} {CY - 128}" stroke="#ffffff" stroke-opacity=".18" stroke-width="16" fill="none" stroke-linecap="round"/>')
    return "".join(out)


def rect_front(look, brand, model):
    stroke = shade(look["case"], 0.62)
    w, h = 236, 296
    x, y = CX - w / 2, CY - h / 2
    out = [
        f'<rect x="{CX + w / 2 - 4}" y="{CY - 18}" width="26" height="36" rx="8" fill="url(#metal)" stroke="{stroke}" stroke-width="2"/>',
        f'<circle cx="{CX + w / 2 + 24}" cy="{CY}" r="9" fill="#2b4fa8"/>',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="26" fill="url(#metal)" stroke="{stroke}" stroke-width="3"/>',
        f'<rect x="{x + 22}" y="{y + 26}" width="{w - 44}" height="{h - 52}" rx="12" fill="url(#dial)" stroke="{shade(look["dial"], 0.7)}" stroke-width="2"/>',
        f'<rect x="{x + 44}" y="{y + 50}" width="{w - 88}" height="{h - 100}" rx="6" fill="none" stroke="#2e3438" stroke-width="1.5"/>',
    ]
    for label, tx, ty in (("XII", CX, y + 92), ("III", x + w - 66, CY + 8), ("VI", CX, y + h - 70), ("IX", x + 66, CY + 8)):
        out.append(
            f'<text x="{tx}" y="{ty}" font-family="Georgia, serif" font-size="26" text-anchor="middle" fill="#2e3438">{label}</text>'
        )
    out.append(hands(96, "#1f3a8a"))
    out.append(f'<path d="M {x + 34} {y + 60} L {x + 90} {y + 40}" stroke="#ffffff" stroke-opacity=".25" stroke-width="12" stroke-linecap="round"/>')
    return "".join(out)


def cushion_front(look, brand, model):
    stroke = shade(look["case"], 0.62)
    hand_colour = "#e9ecee" if is_dark(look["dial"]) else "#2e3438"
    out = [
        f'<rect x="{CX + 160}" y="{CY - 18}" width="30" height="36" rx="7" fill="url(#metal)" stroke="{stroke}" stroke-width="2"/>',
        f'<rect x="{CX - 172}" y="{CY - 172}" width="344" height="344" rx="86" fill="url(#metal)" stroke="{stroke}" stroke-width="3"/>',
        f'<rect x="{CX - 150}" y="{CY - 150}" width="300" height="300" rx="70" fill="{shade(look["case"], 1.12)}" stroke="{stroke}" stroke-width="1.5"/>',
        f'<rect x="{CX - 122}" y="{CY - 122}" width="244" height="244" rx="52" fill="url(#dial)" stroke="{shade(look["dial"], 0.6)}" stroke-width="2"/>',
    ]
    if brand == "audemars-piguet":
        for i in range(-110, 120, 20):  # grid texture
            out.append(f'<line x1="{CX - 112}" y1="{CY + i}" x2="{CX + 112}" y2="{CY + i}" stroke="{shade(look["dial"], 0.78)}" stroke-width="2"/>')
            out.append(f'<line x1="{CX + i}" y1="{CY - 112}" x2="{CX + i}" y2="{CY + 112}" stroke="{shade(look["dial"], 0.78)}" stroke-width="2"/>')
        for i in range(8):  # bezel screws
            sx, sy = polar(136, i * 45 + 22.5)
            out.append(f'<circle cx="{sx:.1f}" cy="{sy:.1f}" r="7" fill="{shade(look["case"], 1.3)}" stroke="{stroke}" stroke-width="1.5"/>')
    else:
        for i in range(-108, 112, 9):  # horizontal embossing
            out.append(f'<line x1="{CX - 112}" y1="{CY + i}" x2="{CX + 112}" y2="{CY + i}" stroke="{shade(look["dial"], 0.8)}" stroke-width="3"/>')
    out.append(markers(104, 84, "#e9ecee" if is_dark(look["dial"]) else "#2e3438"))
    out.append(hands(92, hand_colour))
    return "".join(out)


def front(watch):
    look, shape = watch["look"], watch["look"]["shape"]
    body = {"rect": rect_front, "cushion": cushion_front}.get(shape, round_front)(look, watch["brand"], watch["model"])
    return strap(look) + body


def back(watch):
    look = watch["look"]
    stroke = shade(look["case"], 0.62)
    ref = watch["reference_number"]
    out = [strap(look)]
    if look["shape"] == "rect":
        out.append(f'<rect x="{CX - 118}" y="{CY - 148}" width="236" height="296" rx="26" fill="url(#metal)" stroke="{stroke}" stroke-width="3"/>')
        for dx, dy in ((-90, -120), (90, -120), (-90, 120), (90, 120)):
            out.append(f'<circle cx="{CX + dx}" cy="{CY + dy}" r="8" fill="{shade(look["case"], 1.2)}" stroke="{stroke}"/>')
    elif look["shape"] == "cushion":
        out.append(f'<rect x="{CX - 172}" y="{CY - 172}" width="344" height="344" rx="86" fill="url(#metal)" stroke="{stroke}" stroke-width="3"/>')
        out.append(f'<circle cx="{CX}" cy="{CY}" r="112" fill="#1b1f22" stroke="{stroke}" stroke-width="6"/>')
        out.append(f'<path d="M {CX} {CY} L {CX + 96} {CY - 40} A 104 104 0 0 1 {CX + 60} {CY + 84} Z" fill="{shade(look["case"], 1.1)}" opacity=".85"/>')
    else:
        out.append(f'<circle cx="{CX}" cy="{CY}" r="178" fill="url(#metal)" stroke="{stroke}" stroke-width="3"/>')
        for i in range(48):  # screw-down caseback notches
            x1, y1 = polar(156, i * 7.5)
            x2, y2 = polar(144, i * 7.5)
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" stroke-width="3"/>')
        out.append(f'<circle cx="{CX}" cy="{CY}" r="138" fill="none" stroke="{stroke}" stroke-width="2"/>')
    out.append(
        f'<path id="arc" d="M {CX - 92} {CY} A 92 92 0 1 1 {CX + 92} {CY}" fill="none"/>'
        f'<text font-family="Cabin, Arial, sans-serif" font-size="15" letter-spacing="3" fill="{stroke}">'
        f'<textPath href="#arc" startOffset="50%" text-anchor="middle">MAISON HEURE CERTIFIED</textPath></text>'
        f'<text x="{CX}" y="{CY + 52}" font-family="Poppins, Arial, sans-serif" font-size="18" text-anchor="middle" fill="{stroke}">REF {ref}</text>'
    )
    return "".join(out)


def side(watch):
    look = watch["look"]
    stroke = shade(look["case"], 0.62)
    s = look["strap"]
    return (
        f'<path d="M 170 300 C 90 330, 70 430, 118 540" stroke="{s}" stroke-width="48" fill="none" stroke-linecap="round"/>'
        f'<path d="M 430 300 C 510 330, 530 430, 482 540" stroke="{s}" stroke-width="48" fill="none" stroke-linecap="round"/>'
        f'<rect x="196" y="318" width="208" height="22" rx="11" fill="{shade(look["case"], 0.85)}" stroke="{stroke}" stroke-width="2"/>'
        f'<rect x="140" y="252" width="320" height="72" rx="22" fill="url(#metal)" stroke="{stroke}" stroke-width="3"/>'
        f'<rect x="158" y="230" width="284" height="26" rx="9" fill="{look["bezel"]}" stroke="{stroke}" stroke-width="2"/>'
        f'<path d="M 176 231 Q 300 206 424 231 Z" fill="#ffffff" fill-opacity=".55" stroke="{stroke}" stroke-width="1.5"/>'
        f'<rect x="458" y="270" width="30" height="36" rx="7" fill="url(#metal)" stroke="{stroke}" stroke-width="2"/>'
        f'<line x1="466" y1="272" x2="466" y2="304" stroke="{stroke}"/><line x1="474" y1="272" x2="474" y2="304" stroke="{stroke}"/>'
        f'<line x1="482" y1="272" x2="482" y2="304" stroke="{stroke}"/>'
        f'<path d="M 160 270 L 440 270" stroke="#ffffff" stroke-opacity=".35" stroke-width="6" stroke-linecap="round"/>'
    )


def svg(look, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" role="img" aria-label="{title}">'
        f"{defs(look)}{body}</svg>\n"
    )


def angled(watch):
    return f'<g transform="translate(300 300) rotate(-18) scale(.9) translate(-300 -300)">{front(watch)}</g>'


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    views = [("front", front), ("angled", angled), ("caseback", back), ("side", side)]
    count = 0
    for watch in WATCHES:
        for index, (label, draw) in enumerate(views, start=1):
            path = OUT_DIR / f"{watch['slug']}-{index}.svg"
            path.write_text(svg(watch["look"], draw(watch), f"{watch['model']} {label} illustration"), encoding="utf-8")
            count += 1

    hero = {
        "brand": "generic", "model": "Diver", "reference_number": "MH-01",
        "look": {"shape": "dive", "dial": "#0f0e0c", "bezel": "#14181b", "case": "#c9ccce", "strap": "#b8bbbe"},
    }
    (ROOT / "static" / "img" / "hero-watch.svg").write_text(svg(hero["look"], front(hero), "Pre-owned dive watch illustration"), encoding="utf-8")
    placeholder = dict(hero, look=dict(hero["look"], dial="#ddd2bf", bezel="#c9ccce"))
    (ROOT / "static" / "img" / "watch-placeholder.svg").write_text(svg(placeholder["look"], front(placeholder), "Watch illustration"), encoding="utf-8")
    print(f"Wrote {count} watch images + hero + placeholder to {OUT_DIR.parent}")


if __name__ == "__main__":
    main()
