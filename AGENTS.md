# Working on dstu-cadcraft

Read `README.md` for setup and `SKILL.md` before creating or changing drafting
behavior. The root `SKILL.md` and `scripts/` are canonical; agent skill directories
link to them. Edit the originals and preserve the relative links.

Use `scripts/dstu.py` for drafting conventions and `scripts/cadcraft_build.py` for
the bundled command builder. Keep geometry in model millimetres, annotations in
paper millimetres, drawing text in Ukrainian, and decimal commas in dimensions.
Preserve the skill's distinctions between verified text, figures, secondary
sources, and practice. Do not claim full standards compliance beyond that evidence.

After Python changes, run:

```sh
python3 -m py_compile scripts/cadcraft_build.py scripts/dstu.py
```

For drawing changes, generate `output/dstu_smoke.dwg` with
`python3 scripts/dstu.py output/dstu_smoke.dwg` (create `output/` first), inspect
the PNG, check the PDF, and report `cadcraft-cli info` entity counts. Follow the
delivery checklist in `SKILL.md`. If the CLI is unavailable, report that limitation
and perform the checks that do not require it.

Keep generated drawings and Python caches out of commits. No dependency manager
or automated test suite is currently configured.
