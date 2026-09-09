# CLAUDE.md

This file is loaded automatically by Claude Code. The full agent brief lives in
`AGENTS.md`; it is imported below so there is a single source of truth.

@AGENTS.md

## Claude Code specifics

- Task: given an app that **already has a public Docker image**, produce a valid
  SoloHost package (`docker-compose.yml` + `config_options.yml`). Read `SOLOHOST.md`
  and `examples/web-app/` first, and mirror the example (see `openclaw`/`hermes` for
  advanced patterns).
- Ask the creator only for product decisions (image name, app name, install settings);
  handle everything technical yourself.
- Definition of done: `python3 scripts/validate_api.py <package-dir>` prints `Result: OK`.
  This hosted check is authoritative and **required before you hand the package off** —
  run it yourself. Then the creator pastes both files into SoloHost.
- v0 is image-exists only — do not build images or write app code.
