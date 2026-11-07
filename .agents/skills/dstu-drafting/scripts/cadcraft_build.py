#!/usr/bin/env python3
"""Tiny builder for cadcraft-cli drawings.

    import sys; sys.path.insert(0, "<skill>/scripts")
    from cadcraft_build import Drawing
    cad = Drawing(metric=True)            # scale=50 for a 1:50 sheet drawn in real mm
    cad.standard_layers()
    cad.layer("OUTLINE"); cad.cmd("rectang", p1=[0, 0], p2=[100, 60], fillet=5)
    cad.layer("DIM");     cad.cmd("dimlinear", p1=[0, 0], p2=[100, 0], at=[50, -12])
    cad.run("part.dwg")   # also writes part.png; returns the exit code

Paper scale: with Drawing(scale=K) you draw geometry in real units (mm) and give every
annotation size in *paper* millimetres — text heights, sheet size, title block, table rows,
centre-mark overshoot. standard_layers() sets DIMSCALE=K and LTSCALE accordingly, and
cad.p(x) converts paper mm to drawing units (e.g. offsets for labels, hatch spacing).
"""
import json
import math
import subprocess
import sys

STANDARD_LAYERS = [  # name, colour, linetype, lineweight (mm)
    ("BORDER", 7, "Continuous", 0.7),
    ("OUTLINE", 7, "Continuous", 0.5),
    ("HIDDEN", 4, "HIDDEN", 0.25),
    ("CENTER", 1, "CENTER", 0.18),
    ("PHANTOM", 3, "PHANTOM", 0.25),
    ("HATCH", 8, "Continuous", 0.13),
    ("DIM", 2, "Continuous", 0.18),
    ("TEXT", 7, "Continuous", 0.25),
]


class Drawing:
    def __init__(self, metric=True, open_file=None, scale=1.0):
        self.metric = metric
        self.open_file = open_file
        self.scale = float(scale)  # drawing units per paper mm (50 for 1:50)
        self.cmds = []

    def p(self, paper_mm):
        """Paper millimetres -> drawing units."""
        return paper_mm * self.scale

    # -- raw ---------------------------------------------------------------
    def cmd(self, _id, **params):
        """Queue any engine command (see `cadcraft-cli commands`)."""
        self.cmds.append(f"{_id} {json.dumps(params)}")

    # -- conveniences -------------------------------------------------------
    def layer(self, name):
        self.cmd("layer.current", name=name)

    def layers(self, specs):
        """specs: [(name, colour, linetype, lineweight_mm), ...]; loads non-continuous linetypes."""
        for lt in sorted({s[2] for s in specs if s[2].lower() != "continuous"}):
            self.cmd("linetype", load=lt)
        for n, c, lt, lw in specs:
            self.cmd("layer.new", name=n, color=c, linetype=lt, lineweight=lw)

    def dimstyle(self, name="ISO-25", text=3.5, arrow=3.0, dec=1, ticks=False, lfac=1.0, current=True):
        """Dimension style in paper mm; DIMSCALE follows the drawing scale."""
        kw = dict(DIMTXT=text, DIMASZ=arrow, DIMDEC=dec, DIMSCALE=self.scale, DIMLFAC=lfac,
                  DIMEXE=1.5, DIMEXO=1.0)
        if ticks:
            kw["DIMTSZ"] = arrow * 0.5
        self.cmd("dimstyle", name=name, current=current, **kw)

    def standard_layers(self, dim_text=3.5, arrow=3.0, ltscale=0.5, extra=()):
        self.layers(STANDARD_LAYERS + list(extra))
        self.cmd("setvar", name="LTSCALE", value=ltscale * self.scale)
        self.dimstyle("ISO-25", text=dim_text, arrow=arrow, dec=1 if self.scale == 1 else 0,
                      ticks=self.scale >= 10)

    def text(self, x, y, s, h=3.5, justify="MC", rotation=0):
        """h is in paper mm."""
        self.cmd("text", at=[x, y], text=s, height=h * self.scale, justify=justify, rotation=rotation)

    def mtext(self, x, y, s, h=3.0, width=150):
        self.cmd("mtext", at=[x, y], text=s, height=h * self.scale, width=width * self.scale)

    def rect(self, x0, y0, x1, y1, **kw):
        self.cmd("rectang", p1=[x0, y0], p2=[x1, y1], **kw)

    def center_cross(self, x, y, r, ext=3.0, layer="CENTER"):
        e = ext * self.scale
        self.layer(layer)
        self.cmd("line", points=[[x - r - e, y], [x + r + e, y]])
        self.cmd("line", points=[[x, y - r - e], [x, y + r + e]])

    def sheet(self, w=841, h=594, origin=(0, 0), layer="BORDER"):
        """Trim edge + drawing frame (20 mm left margin, 10 mm elsewhere); w, h in paper mm.
        Returns the frame's (x0, y0, x1, y1) in drawing units."""
        k, (ox, oy) = self.scale, origin
        self.layer(layer)
        self.rect(ox, oy, ox + w * k, oy + h * k)
        f = (ox + 20 * k, oy + 10 * k, ox + (w - 10) * k, oy + (h - 10) * k)
        self.rect(*f, width=0.7 * k)
        return f

    def title_block(self, x1, y0, title, rows, width=200, row_h=14, layer="BORDER"):
        """Bottom-right anchored at (x1, y0) in drawing units; sizes in paper mm.
        rows: list of strings, drawn top-down under a title row."""
        k = self.scale
        w, rh = width * k, row_h * k
        x0 = x1 - w
        self.layer(layer)
        self.rect(x0, y0, x1, y0 + rh * (len(rows) + 1))
        for i in range(1, len(rows) + 1):
            self.cmd("line", points=[[x0, y0 + i * rh], [x1, y0 + i * rh]])
        self.layer("TEXT")
        self.text(x0 + w / 2, y0 + rh * (len(rows) + 0.5), title, 5)
        for i, r in enumerate(reversed(rows)):
            self.text(x0 + 3 * k, y0 + rh * (i + 0.5), r, 3, "ML")

    def grid_table(self, x0, y0, col_x, rows, row_h=8, h=3, title=None):
        """Line-and-text table, top-left at (x0, y0) in drawing units; col_x (column
        boundaries from 0), row_h and h are paper mm."""
        k = self.scale
        cx = [c * k for c in col_x]
        rh = row_h * k
        self.layer("TEXT")
        if title:
            self.text(x0, y0 + 3 * k, title, 5, "BL")
        for i in range(len(rows) + 1):
            self.cmd("line", points=[[x0, y0 - i * rh], [x0 + cx[-1], y0 - i * rh]])
        for c in cx:
            self.cmd("line", points=[[x0 + c, y0], [x0 + c, y0 - len(rows) * rh]])
        for i, r in enumerate(rows):
            for j, val in enumerate(r):
                self.text(x0 + cx[j] + 2 * k, y0 - i * rh - rh / 2, str(val), h, "ML")

    @staticmethod
    def polar(cx, cy, ang_deg, r):
        a = math.radians(ang_deg)
        return [round(cx + r * math.cos(a), 4), round(cy + r * math.sin(a), 4)]

    # -- run ---------------------------------------------------------------
    def run(self, out, png=True, pdf=False, extra_args=()):
        args = ["cadcraft-cli", "run"]
        if self.open_file:
            args.append(self.open_file)
        elif self.metric:
            args.append("--metric")
        for c in self.cmds:
            args += ["--cmd", c]
        args += ["--save", out]
        if png:
            args += ["--export", out.rsplit(".", 1)[0] + ".png"]
        args += list(extra_args)
        res = subprocess.run(args, capture_output=True, text=True)
        for line in res.stderr.splitlines():
            print(line, file=sys.stderr)
        if res.returncode == 0 and pdf:
            res = subprocess.run(["cadcraft-cli", "convert", out, out.rsplit(".", 1)[0] + ".pdf"])
        return res.returncode


if __name__ == "__main__":  # smoke test: a 1:50 room on an A3 sheet
    cad = Drawing(scale=50)
    cad.standard_layers()
    cad.sheet(420, 297, origin=(-2000, -2000))
    cad.layer("OUTLINE")
    cad.rect(0, 0, 6000, 4000)
    cad.rect(-200, -200, 6200, 4200)
    cad.layer("DIM")
    cad.cmd("dimlinear", p1=[0, 0], p2=[6000, 0], at=[3000, cad.p(-10)])
    cad.layer("TEXT")
    cad.text(3000, 2000, "ROOM 24 m²", 5)
    cad.title_block(-2000 + cad.p(410), -2000 + cad.p(10), "SMOKE TEST ROOM", ["SCALE 1:50  UNITS mm"])
    sys.exit(cad.run(sys.argv[1] if len(sys.argv) > 1 else "smoke.dwg"))
