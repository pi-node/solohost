# Contributing

This repo is the SoloHost package **starter** and **contract**: the shared answer
key for what a valid package looks like. It contains no production validation logic.

## Making a package

You usually don't contribute here. You copy the repo and use it to build your own
package (see `README.md`). Open an issue with the "New app request" template if you
want an app packaged.

## Changing the contract or examples

- `SOLOHOST.md` is the **v0 contract: only rules enforced today**. Do not add a
  rule unless the SoloHost backend or Pi Desktop actually checks it; put anything
  proposed under the "Not in v0" section instead.
- Any example you add or edit must pass the authoritative validator with no `FAIL`s:

  ```bash
  python3 scripts/validate_api.py examples/<dir>
  ```

## Ground rules

- The contract (`SOLOHOST.md`) is the source of truth, pending final reconciliation
  with the Container Compatibility Spec.
- `scripts/validate_api.py` calls the authoritative SoloHost validator and is the
  required gate, and the only validation this repo relies on.
