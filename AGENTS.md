# Working on dstu-cadcraft

Read `README.md` for setup and `.agents/skills/dstu-drafting/SKILL.md` before creating or changing drafting
behavior. Each of `.agents/skills/dstu-drafting/`, `.claude/skills/dstu-drafting/`,
and `.agent/skills/dstu-drafting/` contains real skill files. Keep their `SKILL.md`
and `scripts/` contents identical when making changes; do not introduce symlinks.

Within each skill directory, use `scripts/dstu.py` for drafting conventions and `scripts/cadcraft_build.py` for
the bundled command builder. Keep geometry in model millimetres, annotations in
paper millimetres, drawing text in Ukrainian, and decimal commas in dimensions.
Preserve the skill's distinctions between verified text, figures, secondary
sources, and practice. Do not claim full standards compliance beyond that evidence.

After Python changes, run:

```sh
python3 -m compileall -q .agents/skills/dstu-drafting/scripts .claude/skills/dstu-drafting/scripts .agent/skills/dstu-drafting/scripts
```

For drawing changes, generate `output/dstu_smoke.dwg` with
`python3 .agents/skills/dstu-drafting/scripts/dstu.py output/dstu_smoke.dwg` (create `output/` first), inspect
the PNG, check the PDF, and report `cadcraft-cli info` entity counts. Follow the
delivery checklist in the selected skill’s `SKILL.md`. If the CLI is unavailable, report that limitation
and perform the checks that do not require it.

Keep generated drawings and Python caches out of commits. No dependency manager
or automated test suite is currently configured.
