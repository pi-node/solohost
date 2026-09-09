# AGENTS.md — Operating guide for the AI agent

You are an AI coding agent (Claude Code, Cursor, or similar) working in a copy of the
`pi-node/solohost` repo. Your job: produce a valid **SoloHost package** — the two files
`docker-compose.yml` and `config_options.yml` — for an app that **already has a public
Docker image**. In v0 you do **not** build images or write app code.

The creator follows `README.md` (the plain tutorial); you follow this.

---

## Where truth lives

- **`SOLOHOST.md`** — the contract and THE source for every technical rule. Follow it;
  never invent rules. Where this guide is brief, SOLOHOST.md has the full version.
- **`examples/web-app/`** — the simplest valid package; copy its shape. For advanced
  patterns see **`examples/openclaw/`** (provider/model `select` + API keys, a startup
  config-write, an embedding fix) and **`examples/hermes/`** (multi-service, plus a local
  model via Docker Model Runner).
- **`schema/config_options.reference.md`** — install-form field reference.
- **`scripts/validate_api.py`** — the authoritative check you must pass before shipping
  (calls SoloHost's hosted validator). It is the only validation this repo relies on.

---

## What you ask vs. what you derive

**Ask the creator** (product decisions only, in plain language):

- the app's public **image name** (e.g. `ghcr.io/owner/app`);
- what the app is **called**;
- what people **set at install** (e.g. a title, a password);
- which optional **capabilities** to turn on, and the **credential each needs** — usually
  an API key or token (e.g. a model provider and its key, or web search and its key).

**Derive everything else yourself, never ask:** ports, YAML shape, env-var names,
labels, service layout, and anything else covered by SOLOHOST.md.

---

## Procedure

**Step 0 — Load context.** Read `SOLOHOST.md` and `examples/web-app/`.

**Step 1 — Gather.** Ask the creator the questions above. Then get the image's technical
details **yourself**: for a public image, search the web by image/app name and read its
docs (port, env/config, how to start non-interactively, auth, embedding/origin option);
for a private/custom image, ask the creator. Docs can lag the build, so treat the running
image as the source of truth.

Map the app's optional **capabilities** the same way (docs if public, creator if custom):
model/provider choices, API keys, search or other integrations, messaging channels, file
access, and so on. Propose the useful ones to the creator, and for each they want, add the
field(s) that collect its credential/choice. Don't drop a capability the app is known for,
and don't expose a credentialed feature without a field to collect the credential.

**Step 2 — Write the two files**, mirroring `examples/web-app/`. Most apps are one service
with a few env vars, so the essentials below are all you need. The rest of SOLOHOST.md
only applies if your app does more (multiple services, a config file, provider keys,
embedding quirks).

Essentials:

- **compose:** `services:` non-empty; no `version:`; every service has `image:` (never
  `build:`); the UI service labeled `pi.ui.primary: "true"`; exactly one loopback port
  (`"127.0.0.1:8080:8080"`, distinctive host port); no blocked constructs (listed in
  SOLOHOST.md).
- **config_options:** top-level `fields:` (+ optional `title`/`description`/`output_file`/
  `fixed_values`); types `text|password|number|select|hidden`; string defaults (`"30"`);
  `select` uses `options:` with optional `set:`; `detect:` is `uid`/`gid` only. Exact
  shape and full rules: SOLOHOST.md and `schema/config_options.reference.md`.
- **variables:** every `${VAR}` in the compose is declared as a field or `fixed_values`
  name (a `set:`-only var also needs a `hidden` field).
- **effective:** each field must actually change the app — an env var the image reads, or
  a value written into the app's config at startup — and every `select` option must be one
  the build can honor. Detail: SOLOHOST.md "Every option must actually take effect."

If the app is more than a single simple service, also read in SOLOHOST.md: **"Beyond
validation"** (UI label, port, named-volume persistence, startup command, embedding) and
**"Writing the compose: gotchas from real packages"** (shell `$$` escaping, no colon in a
`${VAR:-default}`, integer-literal typed fields, startup config-file merges, crash-loop
safety).

**Step 3 — Validate (required).** Run `python3 scripts/validate_api.py <your-package-dir>`
and reach `Result: OK`. This POSTs both files to SoloHost's hosted validator — the same
one that runs at submit — so it is the authoritative check and a **mandatory gate**: do
not proceed to Step 4 until it passes. Do this yourself, automatically; the creator does
not have to ask. If it prints `FAIL`, fix the reported errors and re-run. If it prints
`UNREACHABLE`, you have no network — do not ship; get on a network and re-run (or have the
creator submit to SoloHost, which runs the same check).

Validation does not confirm that options take **effect**, so also confirm each field
reaches the app (SOLOHOST.md "Every option must actually take effect"). To sanity-check
what a field writes, `POST /api/apps/preview-env` returns the `.env` a set of answers
produces (see SOLOHOST.md "Hosted validation API").

**Step 4 — Hand off.** Tell the creator where the two files are and that they paste
**both** into SoloHost to submit.

---

## Guardrails

- `SOLOHOST.md` wins. If unsure, re-read it, and don't add or enforce rules it doesn't state.
- The app must already have a public image; image creation is out of scope in v0.
- Name each field after the exact env var the image reads (e.g. `GF_SECURITY_ADMIN_PASSWORD`),
  or a name your startup command translates into the app's config (see SOLOHOST.md
  "Every option must actually take effect").
