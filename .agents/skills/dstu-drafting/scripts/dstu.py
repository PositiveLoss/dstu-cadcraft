#!/usr/bin/env python3
"""ДСТУ / ГОСТ (ЄСКД) / ISO drafting helpers for cadcraft-cli, on top of the cadcraft skill's Drawing.

    import sys, os
    sys.path.insert(0, "<skills>/dstu-drafting/scripts")
    import dstu
    cad = dstu.new_drawing(scale=1)              # 1:1 ; scale=K for 1:K
    fr = dstu.frame(cad, "A1")                   # returns the frame rectangle and title-block anchor
    dstu.title_block(cad, fr, name="Корпус", designation="АБВГ.123456.001", scale="1:1", ...)
    cad.layer(dstu.L.MAIN); cad.rect(...)
    dstu.run(cad, "part.dwg")

All sizes are paper millimetres; geometry is in model units (mm). See ../SKILL.md for the rules.
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cadcraft", "scripts"))
from cadcraft_build import Drawing  # noqa: E402

# ------------------------------------------------------------------ ГОСТ 2.301—68 / ДСТУ ISO 5457 formats
# Landscape (long side first). ГОСТ 2.301 табл. 1; A5 148×210 is allowed "при необходимости".
FORMATS = {"A0": (1189, 841), "A1": (841, 594), "A2": (594, 420), "A3": (420, 297), "A4": (297, 210),
           "A5": (210, 148)}
# ГОСТ 2.301 табл. 2 — additional formats: the short side of the base format is multiplied, e.g. "A4x3" = 297×630.
MULTIPLES = {  # exact sizes from ГОСТ 2.301 табл. 2 (short side × long side, mm)
    "A0": {2: (1189, 1682), 3: (1189, 2523)},
    "A1": {3: (841, 1783), 4: (841, 2378)},
    "A2": {3: (594, 1261), 4: (594, 1682), 5: (594, 2102)},
    "A3": {3: (420, 891), 4: (420, 1189), 5: (420, 1486), 6: (420, 1783), 7: (420, 2080)},
    "A4": {3: (297, 630), 4: (297, 841), 5: (297, 1051), 6: (297, 1261), 7: (297, 1471), 8: (297, 1682), 9: (297, 1892)},
}
SIZE_TOLERANCE = ((150, 1.5), (600, 2.0), (10 ** 9, 3.0))   # ГОСТ 2.301 табл. 3: side ≤150 ±1,5; ≤600 ±2; >600 ±3
MARGINS = {"page": (20, 10, 10, 10),   # left, right, top, bottom — the source page and ISO 5457
           "gost": (20, 5, 5, 5)}       # ЄСКД practice (ГОСТ 2.104 figure; not stated in ГОСТ 2.301 text)


def format_size(fmt, landscape=True):
    """'A1' → (841, 594); 'A4x3' → (630, 297) per ГОСТ 2.301 табл. 2 (long side first when landscape)."""
    base, _, mult = fmt.upper().replace("Х", "X").replace("А", "A").partition("X")
    long_, short = FORMATS[base]
    if mult:
        n = int(mult)
        if n not in MULTIPLES.get(base, {}):
            raise ValueError(f"{fmt}: ГОСТ 2.301 allows {base}x{sorted(MULTIPLES.get(base, {}))}")
        a, b = MULTIPLES[base][n]
        long_, short = max(a, b), min(a, b)
    return (long_, short) if landscape else (short, long_)


# ------------------------------------------------------------------ ГОСТ 2.302—68 scales (п. 2–4)
SCALES_REDUCE = ["1:2", "1:2,5", "1:4", "1:5", "1:10", "1:15", "1:20", "1:25", "1:40", "1:50",
                 "1:75", "1:100", "1:200", "1:400", "1:500", "1:800", "1:1000"]
SCALES_LARGE_OBJECTS = ["1:2000", "1:5000", "1:10000", "1:20000", "1:25000", "1:50000"]   # п. 3, генплани
SCALES_ENLARGE = ["2:1", "2,5:1", "4:1", "5:1", "10:1", "20:1", "40:1", "50:1", "100:1"]  # + (100·n):1, п. 4
SCALES = ["1:1"] + SCALES_REDUCE + SCALES_LARGE_OBJECTS + SCALES_ENLARGE


def check_scale(s):
    if s not in SCALES and not (s.endswith(":1") and s[:-2].isdigit() and int(s[:-2]) % 100 == 0):
        raise ValueError(f"ГОСТ 2.302: scale {s!r} is not in the standard series")
    return s


# ------------------------------------------------------------------ ГОСТ 2.304—81 lettering
# Sizes h (capital height); 1,8 is "не рекомендується" and only for type Б.
FONT_SIZES = [2.5, 3.5, 5, 7, 10, 14, 20, 28, 40]
# Relative parameters from ГОСТ 2.304 табл. 1–2 (multiples of h): c lowercase height, a letter spacing,
# b minimum line pitch (base-line to base-line), e word spacing, d stroke thickness.
FONT_PARAMS = {"A": dict(d=1 / 14, c=10 / 14, a=2 / 14, b=22 / 14, e=6 / 14),
               "B": dict(d=1 / 10, c=7 / 10, a=2 / 10, b=17 / 10, e=6 / 10)}
FONT_CANDIDATES = ["GOST type A", "GOST type B", "ISOCPEUR", "osifont", "Arial Narrow", "Arial"]


class L:  # layer names (Ukrainian, ГОСТ 2.303 line types)
    MAIN = "ОСНОВНА"          # суцільна товста основна, s
    THIN = "ТОНКА"            # суцільна тонка, s/3..s/2
    HIDDEN = "ШТРИХОВА"       # штрихова, s/3..s/2, штрих 2–8, проміжок 1–2
    AXIS = "ОСЬОВА"           # штрихпунктирна тонка, штрих 5–30, проміжок 3–5
    AXIS_THICK = "ШТРИХПУНКТИРНА_ПОТОВЩЕНА"  # s/2..2s/3, штрих 3–8, проміжок 3–4
    PHANTOM = "ДВОТОЧКОВА"    # штрихпунктирна з двома точками, штрих 5–30, проміжок 4–6
    CUT = "РОЗІМКНЕНА"        # розімкнена, s..1,5s, штрихи 8–20
    HATCH = "ШТРИХУВАННЯ"
    DIM = "РОЗМІРИ"
    TEXT = "ТЕКСТ"
    FRAME = "РАМКА"


# Linetypes in paper mm (LTSCALE = drawing scale factor K keeps them true on paper).
# ГОСТ 2.303 says only that dash length is chosen by image size and dashes/gaps are uniform (п. 7–9);
# the ranges in the comments (2–8/1–2, 5–30/3–5 …) are the ones shown in its table figure.
LIN_ISO_TEMPLATE = (  # ДСТУ ISO 128-20/-21: elements in multiples of the line thickness d
    "*ISO_02_ШТРИХОВА,ISO 128 тип 02 (штрих 12d, проміжок 3d)\nA,{d12},-{d3}\n"
    "*ISO_04_ОСЬОВА,ISO 128 тип 04 (довгий штрих 24d, проміжок 3d, крапка 0,5d)\nA,{d24},-{d3},{d05},-{d3}\n"
    "*ISO_05_ДВОТОЧКОВА,ISO 128 тип 05 (довгий штрих 24d, дві крапки)\nA,{d24},-{d3},{d05},-{d3},{d05},-{d3}\n")
LIN = ("*ГОСТ_ШТРИХОВА,Штрихова ГОСТ 2.303 (штрих 5, проміжок 1,5)\nA,5,-1.5\n"
       "*ГОСТ_ОСЬОВА,Штрихпунктирна тонка ГОСТ 2.303 (штрих 15, проміжок 4)\nA,15,-2,0,-2\n"
       "*ГОСТ_ОСЬОВА_ПОТОВЩЕНА,Штрихпунктирна потовщена (штрих 6, проміжок 3)\nA,6,-1.5,0,-1.5\n"
       "*ГОСТ_ДВОТОЧКОВА,Штрихпунктирна з двома точками (штрих 15, проміжок 5)\nA,15,-1.67,0,-1.67,0,-1.67\n")


def detect_font():
    dirs = ["/Library/Fonts", os.path.expanduser("~/Library/Fonts"), "/System/Library/Fonts/Supplemental",
            "/usr/share/fonts", os.path.expanduser("~/.fonts"), "C:/Windows/Fonts"]
    names = []
    for d in dirs:
        for root, _, files in os.walk(d) if os.path.isdir(d) else []:
            names += [f.lower() for f in files]
    for cand in FONT_CANDIDATES:
        key = cand.lower().replace(" ", "")
        if any(key in n.replace(" ", "").replace("_", "") for n in names):
            return cand
    return None  # CADCraft's own stroke font (Cyrillic falls back to a system font)


def new_drawing(scale=1.0, s=0.7, text=3.5, arrow=3.5, font=None, system="eskd"):
    """A metric Drawing with ДСТУ layers, linetypes, a type A text style and a ДСТУ dimension style.
    s = thickness of the solid main line (ГОСТ 2.303 п. 5: 0,5–1,4 mm).
    system="eskd": ГОСТ 2.303 linetypes (default).
    system="iso": ДСТУ ISO 128-20/-21 linetypes built from the thin-line thickness d (dash 12d, gap 3d,
    long dash 24d, dot 0,5d) and thin:thick = 1:2. ДСТУ ISO 128 is in force on an alternative basis
    with ЄСКД, but a drawing made to it must say so and show the projection-method symbol
    (ДСТУ ISO 5456-2) — use projection_symbol() and iso_note()."""
    if not 0.5 <= s <= 1.4:
        raise ValueError("ГОСТ 2.303 п. 5: s must be 0,5–1,4 mm")
    cad = Drawing(metric=True, scale=scale)
    cad.s, cad.system = s, system
    thin = s / 2 if system == "iso" else (0.25 if s <= 0.8 else 0.35)
    cad.thin = thin
    if system == "iso":
        f = lambda m: f"{m * thin:g}"
        cad.cmd("linetype", text=LIN + LIN_ISO_TEMPLATE.format(d12=f(12), d3=f(3), d24=f(24), d05=f(0.5)), load="*")
        hidden_lt, axis_lt, ph_lt = "ISO_02_ШТРИХОВА", "ISO_04_ОСЬОВА", "ISO_05_ДВОТОЧКОВА"
    else:
        cad.cmd("linetype", text=LIN, load="*")
        hidden_lt, axis_lt, ph_lt = "ГОСТ_ШТРИХОВА", "ГОСТ_ОСЬОВА", "ГОСТ_ДВОТОЧКОВА"
    cad.layers([
        (L.MAIN, 7, "Continuous", s), (L.THIN, 7, "Continuous", thin),
        (L.HIDDEN, 4, hidden_lt, thin if system == "iso" else 0.35), (L.AXIS, 1, axis_lt, thin),
        (L.AXIS_THICK, 1, "ГОСТ_ОСЬОВА_ПОТОВЩЕНА", 0.5), (L.PHANTOM, 6, ph_lt, thin),
        (L.CUT, 7, "Continuous", 1.0), (L.HATCH, 8, "Continuous", thin),
        (L.DIM, 2, "Continuous", thin), (L.TEXT, 7, "Continuous", thin), (L.FRAME, 7, "Continuous", s),
    ])
    cad.cmd("setvar", name="LTSCALE", value=cad.scale)
    font = font or detect_font()
    st = dict(name="ГОСТ_А", widthFactor=0.85, oblique=0, current=True)  # тип А без нахилу
    if font:
        st["font"] = font
    cad.cmd("style", **st)
    dimstyle(cad, "ДСТУ", text=text, arrow=arrow)
    return cad


def dimstyle(cad, name="ДСТУ", text=3.5, arrow=3.5, lfac=1.0, current=True):
    """ГОСТ 2.307: number above the line (DIMTAD), extension lines start at the contour (DIMEXO 0)
    and pass the dimension line by 2 mm (1–5), decimal comma, no units, text aligned with the line."""
    cad.cmd("dimstyle", name=name, current=current, DIMTXT=text, DIMASZ=arrow, DIMEXO=0, DIMEXE=2,
            DIMGAP=1, DIMTAD=1, DIMTIH=0, DIMTOH=0, DIMDSEP=",", DIMDEC=1, DIMZIN=8,
            DIMSCALE=cad.scale, DIMLFAC=lfac, DIMTXSTY="ГОСТ_А")


def text(cad, x, y, s, h=3.5, justify="MC", rotation=0):
    if h not in FONT_SIZES:
        raise ValueError(f"ГОСТ 2.304 font size {h} not in {FONT_SIZES}")
    cad.cmd("text", at=[x, y], text=s, height=h * cad.scale, justify=justify, rotation=rotation)


def mtext(cad, x, y, s, h=3.5, width=180, font_type="A"):
    """Multi-line text with the ГОСТ 2.304 minimum line pitch b (22/14·h for type A, 17/10·h for type Б).
    CAD line spacing 1,0 ≈ 1,667·h, so the factor is b / 1,667."""
    factor = round(FONT_PARAMS[font_type]["b"] / (5 / 3), 3)
    cad.cmd("mtext", at=[x, y], text=s, height=h * cad.scale, width=width * cad.scale, lineSpacing=factor)
    return FONT_PARAMS[font_type]["b"] * h


# ------------------------------------------------------------------ frame + title block
# ISO 5457 grid reference fields (secondary source: cadsetterout.com, ISO 5457 summary):
# fields 50 mm counted from the centring marks; letters top→bottom, numerals left→right; no I, O.
ZONE_COUNTS = {"A0": (24, 16), "A1": (16, 12), "A2": (12, 8), "A3": (8, 6), "A4": (6, 4)}


def frame(cad, fmt="A1", landscape=True, origin=(0, 0), margins="page", extra_column=None,
          centring_marks=False, zones=False):
    """Trim edge (thin) and frame (thick). Returns dict(x0, y0, x1, y1, tb=(x1, y0)) in model units.
    fmt: "A0".."A5" or an additional format like "A4x3" (ГОСТ 2.301 табл. 2).
    extra_column: designation for графа 26 (70x14, top-left, rotated 180°) — ГОСТ 2.104.
    centring_marks: ISO 5457 marks at the middle of each side, from the trim edge across the margin.
    zones: ISO 5457 grid reference (50 mm fields from the centring marks, letters down the side,
    numerals along the top; only top and left on A4); also feeds the "Зона" column of a специфікація."""
    w, h = format_size(fmt, landscape)
    ml, mr, mt, mb = MARGINS[margins]
    k, (ox, oy) = cad.scale, origin
    cad.layer(L.THIN)
    cad.rect(ox, oy, ox + w * k, oy + h * k)
    x0, y0, x1, y1 = ox + ml * k, oy + mb * k, ox + (w - mr) * k, oy + (h - mt) * k
    cad.layer(L.FRAME)
    cad.cmd("pline", vertices=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]], closed=True, width=cad.s * k)
    if extra_column:
        cad.cmd("pline", vertices=[[x0, y1], [x0 + 70 * k, y1], [x0 + 70 * k, y1 - 14 * k], [x0, y1 - 14 * k]],
                closed=True, width=cad.s * k)
        cad.layer(L.TEXT)
        text(cad, x0 + 35 * k, y1 - 7 * k, extra_column, 5, rotation=180)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if centring_marks or zones:
        cad.layer(L.FRAME)
        for a, b in (([cx, oy], [cx, y0 + 5 * k]), ([cx, oy + h * k], [cx, y1 - 5 * k]),
                     ([ox, cy], [x0 + 5 * k, cy]), ([ox + w * k, cy], [x1 - 5 * k, cy])):
            cad.cmd("pline", vertices=[a, b], width=cad.s * k)   # trim edge → 5 mm inside the frame
    if zones:
        base = fmt.upper().split("X")[0]
        nx, ny = ZONE_COUNTS.get(base, (int(round((x1 - x0) / k / 50)), int(round((y1 - y0) / k / 50))))
        if not landscape:
            nx, ny = ny, nx
        letters = [c for c in "ABCDEFGHJKLMNPQRSTUVWXYZ"]  # I and O are not used
        cad.layer(L.THIN)
        sides = ("top", "left") if base == "A4" else ("top", "bottom", "left", "right")
        f = 50 * k

        def ticks(c0, c1, center, n):
            half = n // 2
            return [center + i * f for i in range(-half + 1, half) if c0 < center + i * f < c1]

        xs = [x0] + ticks(x0, x1, cx, nx) + [x1]
        ys = [y0] + ticks(y0, y1, cy, ny) + [y1]
        for x in xs[1:-1]:
            if "top" in sides:
                cad.cmd("line", points=[[x, y1], [x, oy + h * k]])
            if "bottom" in sides:
                cad.cmd("line", points=[[x, y0], [x, oy]])
        for y in ys[1:-1]:
            if "left" in sides:
                cad.cmd("line", points=[[x0, y], [ox, y]])
            if "right" in sides:
                cad.cmd("line", points=[[x1, y], [ox + w * k, y]])
        cad.layer(L.TEXT)
        for i in range(len(xs) - 1):
            xm = (xs[i] + xs[i + 1]) / 2
            if "top" in sides:
                text(cad, xm, (y1 + oy + h * k) / 2, str(i + 1), 3.5)
            if "bottom" in sides:
                text(cad, xm, (y0 + oy) / 2, str(i + 1), 3.5)
        rows = list(reversed(range(len(ys) - 1)))
        for j, i in enumerate(rows):
            ym = (ys[i] + ys[i + 1]) / 2
            if "left" in sides:
                text(cad, (x0 + ox) / 2, ym, letters[j], 3.5)
            if "right" in sides:
                text(cad, (x1 + ox + w * k) / 2, ym, letters[j], 3.5)
    return dict(x0=x0, y0=y0, x1=x1, y1=y1, tb=(x1, y0), fmt=fmt)


def projection_symbol(cad, x, y, method="E", h=3.5):
    """Projection-method symbol (ДСТУ ISO 5456-2 / ДСТУ ISO 128-30): a truncated cone and its end view.
    Method E (first angle, ЄСКД) — end view to the RIGHT of the cone; method A (third angle) — to the LEFT.
    Proportions follow the ISO 5456-2 figure approximately (H = 2h)."""
    k = cad.scale
    H = 2 * h * k
    cone_w = H * 1.2
    gap = H * 0.4
    if method == "E":
        cx0, ex = x, x + cone_w + gap + H / 2
    else:
        ex, cx0 = x + H / 2, x + H + gap
    cad.layer(L.MAIN)
    cad.cmd("pline", closed=True, vertices=[[cx0, y - H / 2], [cx0 + cone_w, y - H / 4],
                                            [cx0 + cone_w, y + H / 4], [cx0, y + H / 2]])
    cad.cmd("circle", center=[ex, y], radius=H / 2)
    cad.cmd("circle", center=[ex, y], radius=H / 4)
    cad.layer(L.AXIS)
    left, right = min(cx0, ex - H / 2) - 2 * k, max(cx0 + cone_w, ex + H / 2) + 2 * k
    cad.cmd("line", points=[[left, y], [right, y]])
    cad.cmd("line", points=[[ex, y - H / 2 - 2 * k], [ex, y + H / 2 + 2 * k]])
    return right - x


def title_block(cad, fr, name, designation, scale, org="", material="", liter="", mass="",
                sheet="1", sheets="1", roles=None, doc_type="", width=None):
    """Основний напис, форма 1 (ГОСТ 2.104), 55 mm high, bottom-right corner of the frame.
    width: 180 (source page / ISO 7200, default) or 185 (strict ГОСТ 2.104).
    roles: [(role, surname, date), …] for rows Розроб., Перев., Т.контр., —, Н.контр., Затв."""
    check_scale(scale)
    k = cad.scale
    width = width or 180
    x1, y0 = fr["tb"]
    x0 = x1 - width * k
    cw = [7, 10, 23 - (185 - width), 15, 10]      # left part (changes + signatures)
    lx = [0]
    for c in cw:
        lx.append(lx[-1] + c)                       # 0,7,17,40|35,55|50,65|60
    L0 = lx[-1]                                    # 65 or 60
    X = lambda u: x0 + u * k
    Y = lambda v: y0 + v * k                        # v from the bottom, 0..55
    thick = cad.s * k

    def tline(a, b):
        cad.cmd("pline", vertices=[a, b], width=thick)

    def nline(a, b):
        cad.cmd("line", points=[a, b])

    cad.layer(L.FRAME)
    cad.cmd("pline", vertices=[[X(0), Y(0)], [X(width), Y(0)], [X(width), Y(55)], [X(0), Y(55)]], closed=True, width=thick)
    # left part: 11 rows x 5 mm; rows 1–4 changes, row 5 header, rows 6–11 signatures
    for c in lx[1:-1]:
        tline([X(c), Y(30)], [X(c), Y(55)])          # verticals through the changes area
    for c in lx[2:-1]:
        tline([X(c), Y(0)], [X(c), Y(30)])           # role | surname | signature | date
    tline([X(L0), Y(0)], [X(L0), Y(55)])
    tline([X(0), Y(30)], [X(L0), Y(30)])
    cad.layer(L.THIN)
    for v in (5, 10, 15, 20, 25, 35, 40, 45, 50):
        nline([X(0), Y(v)], [X(L0), Y(v)])
    cad.layer(L.FRAME)
    tline([X(0), Y(35)], [X(L0), Y(35)])            # under the header row
    # right part
    R = L0
    tline([X(R), Y(40)], [X(width), Y(40)])          # designation field 120 x 15
    tline([X(R + 70), Y(0)], [X(R + 70), Y(40)])     # name | right block
    tline([X(R), Y(15)], [X(R + 70), Y(15)])         # name | material
    tline([X(R + 70), Y(35)], [X(width), Y(35)])     # header Літ./Маса/Масштаб
    tline([X(R + 70), Y(20)], [X(width), Y(20)])
    tline([X(R + 70), Y(15)], [X(width), Y(15)])
    for u in (R + 70 + 15, R + 70 + 32):
        tline([X(u), Y(20)], [X(u), Y(40)])
    cad.layer(L.THIN)
    for u in (R + 75, R + 80):
        nline([X(u), Y(20)], [X(u), Y(35)])          # three liter cells
    cad.layer(L.FRAME)
    tline([X(R + 90), Y(15)], [X(R + 90), Y(20)])    # Аркуш | Аркушів
    # captions
    cad.layer(L.TEXT)
    for i, cap in enumerate(["Зм.", "Арк.", "№ докум.", "Підпис", "Дата"]):
        text(cad, X((lx[i] + lx[i + 1]) / 2), Y(32.5), cap, 2.5)
    roles = roles or [("Розроб.", "", ""), ("Перев.", "", ""), ("Т.контр.", "", ""), ("", "", ""),
                      ("Н.контр.", "", ""), ("Затв.", "", "")]
    for i, (role, who, date) in enumerate(roles[:6]):
        v = 27.5 - 5 * i
        text(cad, X(1), Y(v), role, 2.5, "ML")
        text(cad, X(lx[2] + 1), Y(v), who, 2.5, "ML")
        text(cad, X((lx[4] + lx[5]) / 2), Y(v), date, 2.5)
    text(cad, X(R + 60), Y(47.5), designation, 7)                         # графа 2
    text(cad, X(R + 35), Y(30 if doc_type else 27.5), name, 5)            # графа 1
    if doc_type:
        text(cad, X(R + 35), Y(22), doc_type, 3.5)
    if material:
        text(cad, X(R + 35), Y(7.5), material, 3.5)                       # графа 3
    text(cad, X(R + 77.5), Y(37.5), "Літ.", 2.5)
    text(cad, X(R + 93.5), Y(37.5), "Маса", 2.5)
    text(cad, X(R + 111), Y(37.5), "Масштаб", 2.5)
    if liter:
        text(cad, X(R + 72.5), Y(27.5), liter, 3.5)
    text(cad, X(R + 93.5), Y(27.5), mass, 3.5)
    text(cad, X(R + 111), Y(27.5), scale, 3.5)
    text(cad, X(R + 71), Y(17.5), f"Аркуш {sheet}", 2.5, "ML")
    text(cad, X(R + 91), Y(17.5), f"Аркушів {sheets}", 2.5, "ML")
    text(cad, X(R + 95), Y(7.5), org, 3.5)                                # графа 9
    return dict(x0=x0, y0=y0, x1=x1, y1=Y(55))


def specification(cad, x1, y0, rows, width=None, row_h=8, title=None):
    """Специфікація (ГОСТ 2.106 form 1 columns) drawn bottom-up from (x1, y0) — e.g. directly on the title block.
    rows: list of tuples (format, zone, pos, designation, name, qty, note); a row with only `name`
    set and others "" is a section heading (centred, e.g. "Деталі")."""
    k = cad.scale
    width = width or 180
    cols = [6, 6, 8, 70, 63 - (185 - width), 10, 22]
    xs = [0]
    for c in cols:
        xs.append(xs[-1] + c)
    x0 = x1 - width * k
    X = lambda u: x0 + u * k
    hdr = 15
    total = hdr + row_h * len(rows)
    ytop = y0 + total * k
    cad.layer(L.FRAME)
    cad.cmd("pline", vertices=[[X(0), y0], [X(width), y0], [X(width), ytop], [X(0), ytop]], closed=True, width=cad.s * k)
    for u in xs[1:-1]:
        cad.cmd("pline", vertices=[[X(u), y0], [X(u), ytop]], width=cad.s * k)
    cad.cmd("pline", vertices=[[X(0), ytop - hdr * k], [X(width), ytop - hdr * k]], width=cad.s * k)
    cad.layer(L.THIN)
    for i in range(1, len(rows)):
        y = ytop - (hdr + i * row_h) * k
        cad.cmd("line", points=[[X(0), y], [X(width), y]])
    cad.layer(L.TEXT)
    for i, cap in enumerate(["Формат", "Зона", "Поз.", "Позначення", "Найменування", "Кіл.", "Примітка"]):
        text(cad, X((xs[i] + xs[i + 1]) / 2), ytop - hdr / 2 * k, cap, 2.5, rotation=90 if i < 3 else 0)
    for r, row in enumerate(rows):
        y = ytop - (hdr + (r + 0.5) * row_h) * k
        fmt, zone, pos, des, name, qty, note = row
        if name and not any((fmt, zone, pos, des, qty, note)):
            text(cad, X((xs[4] + xs[5]) / 2), y, name, 3.5)   # section heading
            continue
        for i, val in enumerate(row):
            if val == "":
                continue
            if i in (0, 1, 2, 5):
                text(cad, X((xs[i] + xs[i + 1]) / 2), y, str(val), 3.5)
            else:
                text(cad, X(xs[i] + 1), y, str(val), 3.5, "ML")
    if title:
        text(cad, X(width / 2), ytop + 4 * k, title, 5)
    return ytop


# ------------------------------------------------------------------ views, sections, positions
def position(cad, n, target, shelf, h=5, side=None):
    """Позиція (ГОСТ 2.109) drawn to ДСТУ ISO 128-22: a thin leader that ends in a dot of 5 line
    thicknesses inside the part's outline, a horizontal shelf (полиця) at least 20 line thicknesses
    long or as long as the number, the number above the shelf at a gap of 2 line thicknesses.
    Numbers are 1–2 sizes larger than the dimension numbers. Keep leaders at > 15° to hatching and
    not crossing each other or dimension numbers (ДСТУ ISO 128-22)."""
    k = cad.scale
    d = getattr(cad, "thin", 0.25)
    side = side or (1 if shelf[0] >= target[0] else -1)
    w = max(len(str(n)) * 0.75 * h + 2, 20 * d) * k
    cad.layer(L.THIN)
    cad.cmd("donut", center=list(target), inside=0, outside=5 * d * k)
    cad.cmd("line", points=[list(target), list(shelf)])
    cad.cmd("line", points=[list(shelf), [shelf[0] + side * w, shelf[1]]])
    cad.layer(L.TEXT)
    text(cad, shelf[0] + side * w / 2, shelf[1] + (2 * d + h / 2) * k, str(n), h)


def view_label(cad, x, y, label, h=7):
    """Designation above a view/section: "А", "А (2:1)", "Б–Б", "Б–Б (2:1)" — no underline (ГОСТ 2.305)."""
    cad.layer(L.TEXT)
    text(cad, x, y, label, h)


def cut_line(cad, p1, p2, letter, look=(0, 1), stroke=12, h=7, through=True):
    """Розімкнена лінія for a section: thick strokes (8–20 mm, s..1,5s) at both ends, arrows 2–3 mm from the
    outer end showing the viewing direction `look` (unit vector), letters at the arrows (ГОСТ 2.305)."""
    k = cad.scale
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    Lg = math.hypot(dx, dy)
    ux, uy = dx / Lg, dy / Lg
    lx, ly = look
    cad.layer(L.CUT)
    for (px, py), sgn in ((p1, -1), (p2, 1)):
        inner = [px - sgn * ux * stroke * k * 0.5, py - sgn * uy * stroke * k * 0.5]
        outer = [px + sgn * ux * stroke * k * 0.5, py + sgn * uy * stroke * k * 0.5]
        cad.cmd("pline", vertices=[inner, outer], width=cad.s * 1.4 * k)
        a = [outer[0] - sgn * ux * 2.5 * k, outer[1] - sgn * uy * 2.5 * k]
        tip = [a[0] + lx * 10 * k, a[1] + ly * 10 * k]
        cad.layer(L.THIN)
        cad.cmd("line", points=[a, [a[0] + lx * 6 * k, a[1] + ly * 6 * k]])
        nx, ny = -ly, lx
        b = [a[0] + lx * 6 * k, a[1] + ly * 6 * k]
        cad.cmd("solid", points=[tip, [b[0] + nx * 1.3 * k, b[1] + ny * 1.3 * k], [b[0] - nx * 1.3 * k, b[1] - ny * 1.3 * k]])
        cad.layer(L.TEXT)
        text(cad, outer[0] + sgn * ux * 4 * k + lx * 6 * k, outer[1] + sgn * uy * 4 * k + ly * 6 * k, letter, h)
        cad.layer(L.CUT)
    if through:
        cad.layer(L.AXIS)
        cad.cmd("line", points=[list(p1), list(p2)])


def detail_mark(cad, center, r, letter, shelf, h=7):
    """Виносний елемент: thin closed circle around the place, letter on a leader shelf (ГОСТ 2.305)."""
    k = cad.scale
    cad.layer(L.THIN)
    cad.cmd("circle", center=list(center), radius=r)
    ang = math.atan2(shelf[1] - center[1], shelf[0] - center[0])
    start = [center[0] + r * math.cos(ang), center[1] + r * math.sin(ang)]
    side = 1 if shelf[0] >= center[0] else -1
    cad.cmd("line", points=[start, list(shelf)])
    cad.cmd("line", points=[list(shelf), [shelf[0] + side * (h * 0.8 + 2) * k, shelf[1]]])
    cad.layer(L.TEXT)
    text(cad, shelf[0] + side * (h * 0.8 + 2) * k / 2, shelf[1] + (0.8 + h / 2) * k, letter, h)


def axes(cad, x, y, r, ext=3, diameter_paper=None):
    """Centre lines of a circle: dash-dot thin, 2–5 mm past the contour; circles under 12 mm on paper get
    solid thin centre lines (ГОСТ 2.303)."""
    k = cad.scale
    d = diameter_paper if diameter_paper is not None else 2 * r / k
    cad.layer(L.THIN if d < 12 else L.AXIS)
    e = ext * k
    cad.cmd("line", points=[[x - r - e, y], [x + r + e, y]])
    cad.cmd("line", points=[[x, y - r - e], [x, y + r + e]])


def hatch(cad, point, material="metal", spacing=1.5, angle=0):
    """Section hatching (ГОСТ 2.306): thin lines at 45°; metals single hatch (ANSI31), non-metals
    (plastics, composites, rubber) cross-hatch (ANSI37). spacing 1–10 mm on paper, same for one part
    in all its sections; adjacent parts get opposite direction (angle=90) or different spacing."""
    cad.layer(L.HATCH)
    pat = {"metal": "ANSI31", "nonmetal": "ANSI37", "composite": "ANSI37"}.get(material, "ANSI31")
    cad.cmd("hatch", points=[list(point)], pattern=pat, scale=round(spacing * cad.scale / 3.175, 4), angle=angle)


def tech_requirements(cad, x0, y_bottom, items, width=180, h=3.5):
    """Технічні вимоги (ГОСТ 2.316): numbered paragraphs above the title block, ≤185 mm wide, no heading."""
    body = "\\P".join(f"{i + 1}. {t}" for i, t in enumerate(items))
    lines = sum(1 + len(t) * h * 0.6 // (width - 5) for t in items)
    pitch = FONT_PARAMS["A"]["b"] * h            # ГОСТ 2.304: minimum line pitch, type A = 22/14·h
    top = y_bottom + (lines * pitch + 2) * cad.scale
    cad.layer(L.TEXT)
    mtext(cad, x0, top, body, h, width, "A")
    return top


def iso_note(cad, x, y, method="E", h=3.5):
    """For drawings made to ДСТУ ISO 128 (alternative to ЄСКД): the statement and the projection symbol
    that its national annex requires. Place it near the title block."""
    cad.layer(L.TEXT)
    text(cad, x, y, "Виконано за ДСТУ ISO 128", h, "ML")
    projection_symbol(cad, x + 60 * cad.scale, y, method, h)


# ------------------------------------------------------------------ аксонометрія (ГОСТ 2.317)
class Iso:
    """Rectangular isometric projection (ГОСТ 2.317), reduced coefficients = 1 (image ×1,22).

    Axes: z vertical, x and y at 30° to the horizontal; the viewer looks from (+x, +y, +z), so the
    +y face ("front"), the +x face and the top are visible. Circles in horizontal planes become
    ellipses with major axis horizontal: 1,22·d × 0,71·d.

    Hidden lines are removed with a painter's algorithm: every visible face is drawn as a WIPEOUT
    (masks what was drawn earlier) plus its outline. The caller draws objects from back to front
    (use .depth(x, y, z) to sort: smaller = farther).
    """
    C30 = math.cos(math.radians(30))

    def __init__(self, cad, origin=(0.0, 0.0), scale=1.0, layer=None):
        self.cad, self.ox, self.oy, self.s = cad, origin[0], origin[1], scale
        self.layer = layer or L.MAIN
        cad.cmd("wipeout", frames="off")
        cad.cmd("setvar", name="WIPEOUTFRAME", value=0)   # both are needed for frames to vanish in exports

    def P(self, x, y, z):
        return [round(self.ox + self.s * (y - x) * self.C30, 4), round(self.oy + self.s * (z - (x + y) / 2), 4)]

    @staticmethod
    def depth(x, y, z):
        return x + y + z

    def face(self, pts3, outline=True):
        pts = [self.P(*p) for p in pts3]
        self.cad.layer(L.THIN)
        self.cad.cmd("wipeout", points=pts)
        if outline:
            self.cad.layer(self.layer)
            self.cad.cmd("pline", vertices=pts, closed=True)

    def polyline(self, pts3, closed=False, layer=None):
        self.cad.layer(layer or self.layer)
        self.cad.cmd("pline", vertices=[self.P(*p) for p in pts3], closed=closed)

    def prism(self, poly, z0, z1, top_marks=()):
        """Extruded polygon (CCW list of (x, y)) between z0 and z1; top_marks = extra closed (x, y)
        outlines drawn on the top face (slots, holes)."""
        n = len(poly)
        vis, dirs = [], []
        for i in range(n):
            (ax, ay), (bx, by) = poly[i], poly[(i + 1) % n]
            nx, ny = by - ay, -(bx - ax)                 # outward normal of a CCW polygon
            vis.append(nx + ny > 1e-9)
            dirs.append(math.atan2(by - ay, bx - ax))
        # one mask per continuous run of visible sides, so the wipeout boundary runs only along
        # drawn lines (WIPEOUTFRAME is not saved in DWG: frames reappear when the file is reopened)
        runs, start = [], None
        first_hidden = next((i for i in range(n) if not vis[i]), None)
        if first_hidden is None:
            runs = [list(range(n))]
        else:
            for k in range(1, n + 1):
                i = (first_hidden + k) % n
                if vis[i] and start is None:
                    start = [i]
                elif vis[i]:
                    start.append(i)
                elif start is not None:
                    runs.append(start)
                    start = None
            if start:
                runs.append(start)
        for run_ in sorted(runs, key=lambda r: sum(sum(poly[i]) for i in r) / len(r)):
            chain = [poly[i] for i in run_] + [poly[(run_[-1] + 1) % n]]
            band = [(x, y, z0) for x, y in chain] + [(x, y, z1) for x, y in reversed(chain)]
            self.face(band, outline=False)
            self.polyline([(x, y, z0) for x, y in chain])  # lower edge (silhouette)
        # vertical edges only at silhouette changes and sharp corners — not between arc facets
        for i in range(n):
            prev = (i - 1) % n
            turn = abs((dirs[i] - dirs[prev] + math.pi) % (2 * math.pi) - math.pi)
            if vis[i] != vis[prev] or (vis[i] and turn > math.radians(25)):
                x, y = poly[i]
                self.polyline([(x, y, z0), (x, y, z1)])
        self.face([(x, y, z1) for x, y in poly])
        for mark in top_marks:
            self.polyline([(x, y, z1) for x, y in mark], closed=True)

    def box(self, center, half, R=None):
        """Box with half-sizes `half`, rotated by the 3x3 matrix R (columns = local axes in world)."""
        R = R or [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        col = lambda i: (R[0][i], R[1][i], R[2][i])
        cx, cy, cz = center

        def W(a, b, c):
            return (cx + a * R[0][0] + b * R[0][1] + c * R[0][2],
                    cy + a * R[1][0] + b * R[1][1] + c * R[1][2],
                    cz + a * R[2][0] + b * R[2][1] + c * R[2][2])

        h = half
        for i in range(3):
            for sgn in (-1, 1):
                nrm = [sgn * v for v in col(i)]
                if sum(nrm) <= 1e-9:
                    continue
                j, k = [a for a in range(3) if a != i]
                quad = []
                for sj, sk in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                    loc = [0, 0, 0]
                    loc[i], loc[j], loc[k] = sgn * h[i], sj * h[j], sk * h[k]
                    quad.append(W(*loc))
                self.face(quad)

    def _ell(self, x, y, z, r):
        c = self.P(x, y, z)
        return c, 1.224745 * r * self.s, 0.707107 * r * self.s

    def cylinder(self, x, y, z0, z1, r):
        """Vertical cylinder: masked silhouette, top ellipse, front half of the bottom ellipse, side lines."""
        (tc, a, b), (bc, _, _) = self._ell(x, y, z1, r), self._ell(x, y, z0, r)
        step = 6
        E = lambda c, t: [round(c[0] + a * math.cos(math.radians(t)), 4), round(c[1] + b * math.sin(math.radians(t)), 4)]
        top_upper = [E(tc, t) for t in range(0, 181, step)]
        bottom_lower = [E(bc, t) for t in range(180, 361, step)]
        self.cad.layer(L.THIN)
        self.cad.cmd("wipeout", points=top_upper + bottom_lower)
        # outlines through the same vertices as the mask, so its (unsaved) frame never shows
        self.cad.layer(self.layer)
        self.cad.cmd("pline", vertices=[E(tc, t) for t in range(0, 360, step)], closed=True)
        self.cad.cmd("pline", vertices=[[top_upper[-1][0], top_upper[-1][1]]] + bottom_lower + [[top_upper[0][0], top_upper[0][1]]])

    def circle_z(self, x, y, z, r, layer=None):
        """A horizontal circle as its isometric ellipse (no masking) — e.g. propeller discs."""
        c, a, b = self._ell(x, y, z, r)
        self.cad.layer(layer or self.layer)
        self.cad.cmd("ellipse", center=c, major=[a, 0], ratio=b / a)


def arc_points(cx, cy, r, a0, a1, step=6):
    """Points along an arc (degrees, CCW from a0 to a1) — for sampling bulges and fillets."""
    n = max(2, int(abs(a1 - a0) / step) + 1)
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / (n - 1))),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / (n - 1)))) for i in range(n)]


def rounded_rect(x0, y0, x1, y1, r):
    """CCW polygon of a rectangle with corner radius r."""
    pts = []
    pts += arc_points(x1 - r, y0 + r, r, -90, 0)
    pts += arc_points(x1 - r, y1 - r, r, 0, 90)
    pts += arc_points(x0 + r, y1 - r, r, 90, 180)
    pts += arc_points(x0 + r, y0 + r, r, 180, 270)
    return pts


def run(cad, out, pdf=True):
    return cad.run(out, pdf=pdf)


if __name__ == "__main__":  # smoke test: an A3 sheet with a plate
    cad = new_drawing()
    fr = frame(cad, "A3", extra_column="ТЕСТ.000.001")
    cad.layer(L.MAIN)
    cad.rect(60, 120, 180, 200)
    cad.cmd("circle", center=[120, 160], radius=15)
    axes(cad, 120, 160, 15)
    cad.layer(L.DIM)
    cad.cmd("dimlinear", p1=[60, 120], p2=[180, 120], at=[120, 108])
    cad.cmd("dimdiameter", center=[120, 160], point=[130.6, 170.6])
    position(cad, 1, [170, 190], [200, 215])
    tb = title_block(cad, fr, "Пластина", "ТЕСТ.000.001", "1:1", org="CADCraft", material="Сталь 20 ГОСТ 1050-88",
                     liter="У", mass="0,2", roles=[("Розроб.", "Claude", "07.11.26"), ("Перев.", "", "")])
    tech_requirements(cad, tb["x0"], tb["y1"] + 5, ["Невказані граничні відхилення розмірів — за ДСТУ ISO 2768-m.",
                                                     "Гострі кромки притупити."])
    sys.exit(run(cad, sys.argv[1] if len(sys.argv) > 1 else "dstu_smoke.dwg"))
