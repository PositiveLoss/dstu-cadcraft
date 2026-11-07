---
name: dstu-drafting
description: Make engineering drawings that follow Ukrainian ДСТУ / ГОСТ ЄСКД / ISO drafting rules (оформлення креслень) with cadcraft-cli: A-series and additional sheet formats, the 20/10 mm frame, the основний напис (title block, form 1), ГОСТ 2.303 or ДСТУ ISO 128 line types, ГОСТ 2.304 lettering, dimensions with a decimal comma, ГОСТ 2.305 view/section/detail designations, position leaders, специфікація, технічні вимоги, ISO 5457 zones and centring marks, and ГОСТ 2.317 isometric views, all in Ukrainian. Use when the user asks for a drawing "за ДСТУ/ГОСТ/ЄСКД/ISO", a креслення, складальне креслення, a Ukrainian title block, or to rework a drawing to these standards. Builds on the `cadcraft` skill.
---

# ДСТУ / ГОСТ (ЄСКД) / ISO drawings with CADCraft

Library: `scripts/dstu.py`. It imports `Drawing` from the `cadcraft` skill, so read that skill for the CLI loop
(generate → render PNG → Read it → fix). Smoke test: `python3 scripts/dstu.py out.dwg`.

```python
import sys; sys.path.insert(0, ".claude/skills/dstu-drafting/scripts"); import dstu
cad = dstu.new_drawing(scale=1)                  # system="eskd" (ГОСТ lines) or "iso" (ДСТУ ISO 128 lines)
fr  = dstu.frame(cad, "A1", extra_column="АБВГ.000000.000 СК")   # also "A4x3", zones=True, centring_marks=True
tb  = dstu.title_block(cad, fr, "Виріб", "АБВГ.000000.000 СК", "1:1", doc_type="Складальне креслення", ...)
cad.layer(dstu.L.MAIN); ...                       # draw
dstu.run(cad, "out.dwg")                          # DWG + PNG + PDF
```

## Sources and how far each rule is verified

The skill started from a vseosvita.ua summary page (В. В. Попова, 2025:
https://vseosvita.ua/library/pravyla-oformlennia-kreslen-zghidno-standartamy-dstu-host-iso-958022.html). That page cites four
sources. I then checked each one against its original text (November 2026):

| Source on the page | Original found | What was verified |
|---|---|---|
| ГОСТ 2.301–2.305 (ЄСКД) | Full texts, 2007 edition with amendments: ru.wikisource.org — [2.301—68](https://ru.wikisource.org/wiki/ГОСТ_2.301—68), [2.302—68](https://ru.wikisource.org/wiki/ГОСТ_2.302—68), [2.303—68](https://ru.wikisource.org/wiki/ГОСТ_2.303—68), [2.304—81](https://ru.wikisource.org/wiki/ГОСТ_2.304—81), [2.305—2008](https://ru.wikisource.org/wiki/ГОСТ_2.305—2008); also [dnaop.com ГОСТ 2.303](https://dnaop.com/html/42364/doc-ГОСТ_2.303-68_) | Formats incl. additional formats and tolerances; the full scale series; s range, centre-line and dash-dot rules; the full font parameter tables; designations of views, cuts, sections and details. Only figure images were unreadable. |
| ДСТУ ISO 128:2005 | Ukrainian IDT texts on dnaop.com: [128-21](https://dnaop.com/html/61282/doc-ДСТУ_ISO_128-21_2005), [128-22](https://dnaop.com/html/62723/doc-ДСТУ_ISO_128-22_2005), [128-30](https://dnaop.com/html/61977/doc-ДСТУ_ISO_128-30_2005), [128-34](https://dnaop.com/html/62518/doc-ДСТУ_ISO_128-34_2005), [128-40](https://dnaop.com/html/61061/doc-ДСТУ_ISO_128-40_2005), [128-44](https://dnaop.com/html/61802/doc-ДСТУ_ISO_128-44_2005), [128-1 index](https://dnaop.com/html/62753_2.html) | CAD line elements (12d / 3d / 24d / 0,5d); leader dot, shelf and text gap; first-angle arrangement; cutting-plane line; the national-annex rule that ISO 128 drawings must say so and carry the projection symbol. **128-20, 128-24 and 128-50 were not found online.** ISO later replaced them with ISO 128-2:2020 and ISO 128-3:2022; this skill still follows the 2005 ДСТУ texts. |
| ДСТУ ISO 5457:2016 | Ukrainian text not public. ISO 5457:1999/Amd 1:2010 is paywalled. Secondary summary: [cadsetterout.com](https://cadsetterout.com/drawing-standards/grid-reference-frame/), [centring marks](https://cadsetterout.com/drawing-standards/centring-marks/) | 20 mm filing margin and 10 mm on the other sides; centring marks at mid-sides; 50 mm grid zones, I/O not used, field counts per format. **Secondary source only.** |
| Чернов Б.В. «Основи технічного креслення», М.: Академія, 2014 | **Not found** in any catalogue or search. It is probably not a real book; don't cite it. | — |

Legend in the rules below: **[текст]** = checked in the standard's text. **[рис.]** = only in a figure of the standard, or a value
shown in its table image. **[практика]** = common ЄСКД practice, not found in the texts above. **[2-е джерело]** = secondary summary.

## Rules to apply (and the helper that does it)

**Sheet** — `frame(cad, fmt, landscape, origin, margins, extra_column, centring_marks, zones)`
- Main formats [текст ГОСТ 2.301 табл. 1]: A0 841×1189, A1 594×841, A2 420×594, A3 297×420, A4 210×297. A5 148×210 is allowed "при необхідності".
- Additional formats [текст табл. 2]: the base short side is multiplied. Use `"A4x3"`, which is 297×630. The available sets are A0×2–3, A1×3–4, A2×3–5, A3×3–7 and A4×3–9. `format_size()` returns the exact table values; note that A3×5 is 1486, not 1485.
- Size tolerance [текст табл. 3]: ±1,5 up to 150 mm, ±2 up to 600 mm, ±3 above.
- The format is the outer thin frame [текст].
- Frame margins: 20 mm left (filing) and 10 mm on the other sides [source page; ISO 5457, 2-е джерело]. ЄСКД practice is 20/5 (`margins="gost"`) [рис. ГОСТ 2.104].
- Графа 26 [текст ГОСТ 2.104 — meaning; рис. — size]: a 70×14 box in the frame's top-left corner, with the designation rotated 180° (`extra_column=`).
- ISO 5457 extras [2-е джерело], for ISO drawings or on request:
  - `centring_marks=True`: thick marks at the middle of each side, from the trim edge to 5 mm inside the frame.
  - `zones=True`: 50 mm fields counted from the centring marks.
    - Numerals run along the top and bottom, letters down the left and right sides. I and O are not used.
    - Text is 3.5, grid lines are thin. On A4 only the top and left sides are zoned.
    - Field counts (long side × short side): A0 24×16, A1 16×12, A2 12×8, A3 8×6, A4 6×4.
  - Zones feed the specification's "Зона" column.

**Title block (основний напис)** — `title_block(...)`, form 1 [рис. ГОСТ 2.104], 55 mm high (11 rows × 5), bottom-right.
- Field meanings [текст ГОСТ 2.104]:
  - 1 name, 2 designation, 3 material, 4 літера, 5 mass, 6 scale;
  - 7 sheet number, 8 number of sheets, 9 organisation;
  - 10–13 role, surname, signature, date; 14–18 the changes table; 26 the rotated designation.
- **Left part:** columns 7 | 10 | 18 (23 at 185) | 15 | 10.
  - Rows 1–4: the changes table. Row 5: the captions Зм., Арк., № докум., Підпис, Дата.
  - Rows 6–11: Розроб., Перев., Т.контр., (blank), Н.контр., Затв.
  - Grid geometry is [рис.]: check it against the organisation's template.
- **Right part, 120 wide:**
  - Top: designation (графа 2), 15 high, h=7.
  - 70 wide: product name (h=5) with the document type under it; material below.
  - 50 wide: Літ. (3×5) / Маса 17 / Масштаб 18, then Аркуш / Аркушів, then the organisation.
- Width: 180 per the page and ISO 7200, 185 per ЄСКД (`width=185`).
- The scale in the title block is written "1:1; 1:2; 2:1" [текст ГОСТ 2.302 п. 5]. `title_block` rejects scales that are not in the series.
- Date format: "11.26" fits the 10 mm cell [практика]. Assembly drawing designation: `…000 СК`.

**Scales (ГОСТ 2.302)** — `dstu.SCALES`, `check_scale()` [текст]
- Reduction: 1:2; 1:2,5; 1:4; 1:5; 1:10; 1:15; 1:20; 1:25; 1:40; 1:50; 1:75; 1:100; 1:200; 1:400; 1:500; 1:800; 1:1000.
- Large objects and general plans: 1:2000…1:50000. Enlargement: 2:1; 2,5:1; 4:1; 5:1; 10:1; 20:1; 40:1; 50:1; 100:1, and (100·n):1.
- Any image at a scale other than the title block's must say so [текст ГОСТ 2.305 п. 4.5].
  - For a detail or section, put the scale in parentheses after the letter: `"А (2:1)"` [текст ГОСТ 2.305 п. 8.2; ДСТУ ISO 128-34].
  - For an unlabelled image (axonometry), write "М 1:2" [практика].
- Draw at 1:1 in model space. For a detail at N:1, draw it ×N and use `dstu.dimstyle(cad, "ДСТУ-2", lfac=1/N)`, then switch back to "ДСТУ".

**Lines** — layers in `dstu.L`; s = 0,5–1,4 mm depending on image size, complexity and format [текст ГОСТ 2.303 п. 5]. Default 0,7.

| Layer | ГОСТ 2.303 line [текст: name and purpose] | Thickness | Dash / gap |
|---|---|---|---|
| ОСНОВНА | суцільна товста основна — visible contour | s | — |
| ТОНКА | суцільна тонка — dims, extension lines, hatching, leaders, shelves, small axes | s/3–s/2 | — |
| ШТРИХОВА | штрихова — invisible contour | s/3–s/2 [рис.] | 2–8 / 1–2 [рис.]; used 5 / 1,5 |
| ОСЬОВА | штрихпунктирна тонка — axes, centre lines | s/3–s/2 | 5–30 / 3–5 [рис.]; used 15 / 4 |
| ШТРИХПУНКТИРНА_ПОТОВЩЕНА | thickened dash-dot — surfaces to treat or coat | s/2–2s/3 [рис.] | 3–8 / 3–4 [рис.] |
| ДВОТОЧКОВА | з двома точками — adjacent parts, extreme positions, fold lines | s/3–s/2 | 5–30 / 4–6 [рис.] |
| РОЗІМКНЕНА | розімкнена — cutting planes | s–1,5s [рис.] | strokes 8–20 [рис.] |

- [текст] Lines of the same type have the same thickness on all images at one scale.
- [текст] Dash length is chosen by image size. Dashes and gaps within a line are about equal.
- [текст] Dash-dot lines cross and end on dashes.
- [текст] When a circle or other figure is under 12 mm on the image, its centre lines are solid thin. `axes()` does this.
- [рис./практика] Centre lines extend 2–5 mm past the contour (`axes(ext=3)`). A break line with bends may extend 2–4 mm past the outline [текст ГОСТ 2.305 п. 9.10].
- **ISO mode** (`system="iso"`, ДСТУ ISO 128-20/-21 [текст 128-21]):
  - Thin = s/2. Elements are in multiples of the thin thickness d: dashed (02) 12d dash / 3d gap; long-dash dot (04) 24d / 3d / dot 0,5d; double-dot (05).
  - Lines too short for one pattern are drawn continuous: a 04 line needs ≥ 54,5d, a 02 line ≥ 27d.
- Hidden edges are dashed and axes dash-dot, all on the ГОСТ layers. Set LTSCALE to the drawing scale factor so dash lengths are true on paper.

**Lettering (ГОСТ 2.304)** — `dstu.text(cad, x, y, s, h)`, `dstu.mtext(...)` [текст]
- Sizes h (capital height): 2,5; 3,5; 5; 7; 10; 14; 20; 28; 40. The size 1,8 is "not recommended" and allowed for type Б only, so `text()` rejects it. Tolerance is ±0,5 mm.
- Type А: d = h/14. Type Б: d = h/10. Either may be upright or slanted at about 75°.
- Relative parameters in `FONT_PARAMS` (c = lowercase height, a = letter spacing, b = minimum line pitch, e = word spacing):
  - Type А: c 10/14·h, a 2/14·h, b 22/14·h, e 6/14·h.
  - Type Б: c 7/10·h, a 2/10·h, b 17/10·h, e 6/10·h; capital width about 6/10·h.
- `mtext()` and `tech_requirements()` set the CAD line spacing to the minimum pitch b.
- Use type А upright everywhere. CADCraft 0.18 can't set an oblique angle on TEXT, so the slanted 75° forms aren't usable consistently.
- Font: `detect_font()` prefers "GOST type A/B", ISOCPEUR or osifont, then Arial Narrow, then Arial. Cyrillic needs a TrueType font.

**Dimensions (ГОСТ 2.307 — not among the page's sources; values are [практика])** — the "ДСТУ" dimstyle
- Text is 3,5, placed above the line and aligned with it. Arrows are 3,5. Extension lines start at the contour and pass the dimension line by 2 mm (1–5).
- Decimal comma, no units, no trailing zeros. The first dimension line sits ≥ 10 mm from the contour, parallel ones ≥ 7 mm apart.
- Dimension lines don't cross other lines [source page].
- Signs: Ø `%%c`, R, □, S Ø, `2×45°`, `4 отв. Ø3,2`. On assembly drawings, mark reference dimensions `*` and add "* Розміри для довідок.".

**Views, cuts, sections, details (ГОСТ 2.305—2008 [текст] and ДСТУ ISO 128-30/-34/-40 [текст])**
- The main view is the most informative one, taking the working, manufacturing or installation position into account. Use as few views as possible and avoid hidden contours.
- **First angle (method E):** the top view goes **below** the main view, the left view to its **right**, the right view to its **left**, the bottom view above it. Views in projection relationship are **not labelled**.
- **A view out of projection:** an arrow by the view it is taken from, and the same capital letter over the arrow and over the view. A rotated view gets the "повернуто" sign.
- **Cut and section (ГОСТ):** `cut_line(...)` draws thick open strokes that must not cross the image outline. Arrows sit 2–3 mm from the stroke ends [текст п. 6.5]. The same capital letter goes at both ends, outside the arrows.
  - The image is labelled `"А–А"`; add `" (2:1)"` at another scale.
  - Don't designate a cut whose plane is the symmetry plane of the whole object when it's in direct projection [текст п. 6.7].
  - A symmetric displaced section on the extension of its trace gets only a thin dash-dot axis: no letters, no arrows [текст п. 7.3].
- **Section outlines:** displaced sections are drawn with the main line, superimposed ones with a thin line [текст п. 7.2].
- **Detail (виносний елемент):** `detail_mark(...)` draws a thin closed line (circle or oval) and puts a capital letter on a leader shelf. The enlarged image is labelled with its designation and scale, e.g. `"А (2:1)"`, placed close to its source [текст п. 8.2–8.3].
- **Letters:** capital Cyrillic. The ГОСТ text names no excluded letters. Avoid letters easily confused with digits (З, О, Ч) or with other letters (Й, Ь, Ґ, Є, І, Ї) [практика].
- **Letter height:** ISO 128-30/-40 require letters "larger than the other lettering by a factor"; the factor is unreadable in the OCR text. Use h = 7 when dimensions are 3,5 [практика].
- **Small elements** of 2 mm or less (holes, chamfers, grooves) may be drawn enlarged, off scale [текст п. 9.7].
- **ISO 128-40 differences** for ISO drawings:
  - The cutting plane is a thick long-dash-dot line (04.2), not the ГОСТ open line.
  - Arrows are thick, at 30° or 90°.
  - Letters are set upright relative to the bottom of the sheet.

**Hatching (ГОСТ 2.306 / ДСТУ ISO 128-50 — neither text found online; [практика])** — `hatch(cad, point, material, spacing)`
- Thin lines at 45°, 1–10 mm apart depending on the area. Use the same spacing and direction for one part in every section.
- Adjacent parts take the opposite direction or a different spacing. Adjacent parts drawn with the double-dot line are not hatched [текст ДСТУ ISO 128-34].
- Metals: ANSI31. Non-metals and composites: cross-hatch ANSI37.

**Position numbers (ГОСТ 2.109) drawn to ДСТУ ISO 128-22 [текст 128-22]** — `position(cad, n, target, shelf)`
- The leader is a thin line ending in a dot of **5 line thicknesses** inside the part's outline. It may instead end in an arrow on an outline, or with no mark on another line.
- The shelf is at least **20 line thicknesses** long, or as long as the text. The number sits above the shelf at a gap of **2 line thicknesses**.
- Leaders run at **more than 15°** to adjacent lines such as hatching and are never parallel to them. They don't cross each other, other shelves or dimension numbers.
- Position numbers are 1–2 sizes larger than dimension numbers [практика ГОСТ 2.109]. Line the shelves up in rows or columns and match the specification.

**Specification (ГОСТ 2.106 [практика])** — `specification(cad, x1, y0, rows, width=180)`
- Columns: Формат 6 | Зона 6 | Поз. 8 | Позначення 70 | Найменування 58 (63 at 185) | Кіл. 10 | Примітка 22. Header 15 high, rows 8.
- Sections, each with a centred heading row: Документація, Складальні одиниці, Деталі, Стандартні вироби, Інші вироби, Матеріали.

**Technical requirements (ГОСТ 2.316 [практика])** — `tech_requirements(...)`: numbered paragraphs above the title block or specification, no wider than 185 mm, no heading, with ГОСТ 2.304 line pitch.

**ISO 128 drawings** — `new_drawing(system="iso")`, `frame(..., zones=True, centring_marks=True)`, `iso_note(cad, x, y)`
- ДСТУ ISO 128 is in force on an alternative basis with ЄСКД, with equal legal force. A drawing made to it **must say so and show the projection-method symbol** per ДСТУ ISO 5456-2 [текст: national annex of every ДСТУ ISO 128 part].
- `iso_note()` writes "Виконано за ДСТУ ISO 128" and draws the method E symbol, with the end view to the right of the cone. The symbol's proportions are approximate [рис. ISO 5456-2].

**Axonometry (ГОСТ 2.317 — not among the page's sources)** — `Iso(cad, origin, scale)`
- **Projection:** rectangular isometric with reduced coefficients of 1, so the image is 1,22× the true size.
  - z is vertical; x and y run at 30° to the horizontal.
  - Horizontal circles become ellipses 1,22·d × 0,71·d, with the major axis horizontal.
  - The viewer looks from (+x, +y, +z).
- **Helpers:**
  - `iso.P(x, y, z)` projects a point.
  - `iso.prism(ccw_poly, z0, z1, top_marks)` draws plates and arms (`rounded_rect`, `arc_points`).
  - `iso.box(center, half, R)` takes an optional rotation matrix.
  - `iso.cylinder(x, y, z0, z1, r)` draws a vertical cylinder.
  - `iso.circle_z(...)` draws a reference ellipse; `iso.polyline(...)` draws marks on faces.
- **Hidden lines are removed with a painter's algorithm:** every visible face is a WIPEOUT plus its outline.
  - Draw back to front, sorting by `Iso.depth = x + y + z` (smaller first).
  - Go slab by slab for stacked parts, and draw large plates before the parts that sit on them.
- **WIPEOUTFRAME is not saved in the DWG.** The helpers make every mask boundary coincide with a drawn line; keep it that way for any new primitive.
- **Line types:** no hidden lines. Reference parts go on ДВОТОЧКОВА. Example: `make_fpv_drone_dstu.py --axo`.

## Checklist before delivering
1. **Sheet:** the format comes from ГОСТ 2.301 (or an additional format) with the right orientation. The frame is 20/10 (or 20/5), and every title-block field is filled in Ukrainian with a scale from the series.
2. **Views:** the main view was chosen deliberately, the other views are in first-angle projection without labels, and cuts, sections and details are labelled `А–А` / `Б (2:1)`.
3. **Lines:** types and weights are on the right layers, s is within 0,5–1,4, and centres under 12 mm are solid thin.
4. **Text:** heights come only from the ГОСТ 2.304 series, decimals use a comma, and multi-line text uses the ГОСТ line pitch.
5. **Dimensions:** ≥10 mm from the contour and ≥7 mm apart, not crossing. Reference dimensions on assemblies are marked `*`.
6. **Position leaders:** dot 5·d, shelf ≥20·d, text 2·d above the shelf, more than 15° to hatching, no crossings.
7. **ISO 128 drawing:** it carries the statement and the projection symbol, and optionally zones and centring marks.
8. Render the PNG, Read it, fix any overlaps, and report the entity counts from `cadcraft-cli info`.

## Known limits (CADCraft 0.18)
- TEXT oblique can't be set, so lettering is type А upright.
- Lineweights are stored in the DWG and PDF, but the PNG preview draws thin lines. Use pline `width` for the frame, cut strokes, centring marks and title-block outlines.
- The wavy break line isn't built in: use `spline` on ТОНКА, or `breakline` for the zig-zag break.
- WIPEOUTFRAME is not persisted in DWG (see Axonometry).
