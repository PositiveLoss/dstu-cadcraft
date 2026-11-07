# ДСТУ drafting with CADCraft

An agent skill and Python helpers for Ukrainian engineering drawings using
`cadcraft-cli`. It supports ДСТУ / ГОСТ (ЄСКД) and ISO drawing conventions:
sheet formats, frames, Ukrainian title blocks, line types, lettering, dimensions,
sections, specifications, technical requirements, and isometric views.

[SKILL.md](.agents/skills/dstu-drafting/SKILL.md) contains the drafting rules, source provenance, API examples,
and delivery checklist. It distinguishes verified standard text from figures,
secondary sources, and common practice; consult those qualifications when choosing
rules for a drawing.

## Requirements

- Python 3 (the helpers use only the standard library).
- `cadcraft-cli` on `PATH`, configured and able to create, render, and convert
  drawings. The skill documents behavior and limitations for CADCraft 0.18.
- A TrueType font with Ukrainian Cyrillic glyphs. The helper searches for GOST,
  ISOCPEUR, osifont, Arial Narrow, then Arial fonts.

The bundled `scripts/cadcraft_build.py` provides the `Drawing` builder. A sibling
`cadcraft/scripts` directory, if present, takes precedence in the current import
logic. The companion `cadcraft` skill is useful for the engine's full command
reference and rendering workflow, but is not required to import the bundled helpers.

## Quick start

From this repository's root:

```sh
command -v cadcraft-cli
mkdir -p output
python3 .agents/skills/dstu-drafting/scripts/dstu.py output/plate.dwg
```

The smoke example generates `output/plate.dwg`, `output/plate.png`, and
`output/plate.pdf`. Inspect the PNG for overlaps and the PDF for lineweights.

To build your own drawing, run this Python code from the repository root:

```python
import sys
sys.path.insert(0, ".agents/skills/dstu-drafting/scripts")
import dstu

cad = dstu.new_drawing(scale=1)
fr = dstu.frame(cad, "A3")
dstu.title_block(cad, fr, "Пластина", "ТЕСТ.000.001", "1:1", org="CADCraft")
cad.layer(dstu.L.MAIN)
cad.rect(60, 120, 180, 200)
raise SystemExit(dstu.run(cad, "plate.dwg"))
```

Geometry is in model millimetres; annotation sizes are in paper millimetres.
`scale=K` means a 1:K drawing. Use `system="iso"` for ISO line conventions and
follow the ISO note and projection-symbol requirements in the skill.

## Codex, Claude Code, and Antigravity

Opening this checkout as a workspace exposes the same `dstu-drafting` skill to
all three tools through self-contained skill directories:

| Agent | Skill location | Repository guidance |
| --- | --- | --- |
| Codex | `.agents/skills/dstu-drafting/` | `AGENTS.md` |
| Claude Code | `.claude/skills/dstu-drafting/` | `CLAUDE.md` |
| Antigravity | `.agents/skills/dstu-drafting/` (also `.agent/skills/dstu-drafting/` for compatibility) | `.agent/rules/dstu-cadcraft.md` |

Each directory contains real copies of `SKILL.md` and `scripts/`, with no
symlinks. Keep all three copies in sync when changing the skill.

To install into another project, clone this repository outside that project and
copy the appropriate skill directory into the project's matching directory:

```sh
git clone https://github.com/PositiveLoss/dstu-cadcraft.git /tmp/dstu-cadcraft

# Codex or current Antigravity (run from your project's root)
mkdir -p .agents/skills
cp -R /tmp/dstu-cadcraft/.agents/skills/dstu-drafting .agents/skills/

# Claude Code
mkdir -p .claude/skills
cp -R /tmp/dstu-cadcraft/.claude/skills/dstu-drafting .claude/skills/

# Antigravity versions using the legacy directory
mkdir -p .agent/skills
cp -R /tmp/dstu-cadcraft/.agent/skills/dstu-drafting .agent/skills/
```

Choose the command for your agent and use a destination that does not already
contain this skill. Restart or reload your agent after installation if needed,
then ask, for example:

> Use dstu-drafting to create an A3 drawing of a 120 × 80 mm steel plate with a
> central Ø30 hole, Ukrainian title block, dimensions, and DWG/PNG/PDF outputs.

Discovery conventions: [Codex skills](https://developers.openai.com/codex/skills),
[Claude Code skills](https://code.claude.com/docs/en/skills), and
[Antigravity skills](https://antigravity.google/docs/skills).

## Development

```sh
python3 -m compileall -q .agents/skills/dstu-drafting/scripts .claude/skills/dstu-drafting/scripts .agent/skills/dstu-drafting/scripts
mkdir -p output
python3 .agents/skills/dstu-drafting/scripts/dstu.py output/dstu_smoke.dwg
cadcraft-cli info output/dstu_smoke.dwg
```

For changes affecting drawings, render and inspect the PNG, check PDF lineweights,
and follow the checklist in the skill’s `SKILL.md`. Report missing engine or font dependencies
and any unverified rules. Keep generated files in `output/`.
