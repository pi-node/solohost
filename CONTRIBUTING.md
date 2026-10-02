# Contributing

This repo is the SoloHost package **contract** and the **skill** that builds packages
against it. It contains no production validation logic — the authoritative validator is
hosted by SoloHost.

## Making a package

You usually don't contribute here. You install the skill and use it (see `README.md`).
Open an issue if you want an app packaged.

## Changing the contract or examples

The contract is `skills/solohost-package/references/contract.md`. It is the **v0 contract:
only rules enforced today**. Do not add a rule unless the SoloHost backend or Pi Desktop
actually checks it; put anything proposed under its "Not in v0" section instead.

Any example you add or edit must pass the authoritative validator with no `FAIL`s:

```bash
python3 skills/solohost-package/scripts/validate_api.py skills/solohost-package/examples/<dir>
```

With no argument it checks every example at once.

Contract edits reach installed skills immediately — the skill fetches the contract from
`main` at runtime — so they do **not** need a version bump. Bump the version only when
`SKILL.md`, the examples, or the scripts change — in both `.claude-plugin/plugin.json` and
the plugin entry in `.claude-plugin/marketplace.json`, kept equal — and validate the
manifests with `claude plugin validate .`.

## Ground rules

- The contract is the source of truth, pending final reconciliation with the Container
  Compatibility Spec.
- `skills/solohost-package/scripts/validate_api.py` calls the authoritative SoloHost
  validator and is the required gate, and the only validation the skill relies on.
