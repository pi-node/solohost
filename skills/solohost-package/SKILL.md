---
name: solohost-package
description: Build a SoloHost package — the docker-compose.yml + config_options.yml pair SoloHost needs to install an app from an already-published public Docker image onto someone's computer. Use this whenever the user wants to publish, package, ship, or list an app on SoloHost or Pi Desktop, mentions config_options.yml or a SoloHost install form, points at a Docker image and asks to turn it into an installable app, or asks why their SoloHost app fails validation or renders a blank tab — even when they never say the word "package". Not for building Docker images or writing app code.
---

# Build a SoloHost package

A **SoloHost package** is two text files:

| File | Role |
| --- | --- |
| `docker-compose.yml` | The runtime stack — which container(s) to run. |
| `config_options.yml` | The install form — the questions shown to the operator. |

The app already exists as a **public Docker image**. A package points at that image; it
never contains app source, and you never build an image. If the user has no published
image yet, say so plainly — that is out of scope here, and they need to publish one first.

The person you are working with is often not a developer. Ask them only product
decisions, in plain language, and handle everything technical yourself.

---

## Step 0 — Load the contract

`references/contract.md` in this skill directory is the full rule set. **Read it before
writing either file.** It is the source for every technical rule; never invent rules it
doesn't state, and don't enforce ones it doesn't state either.

The contract evolves as SoloHost does, so **fetch the current copy first**:

```bash
curl -fsS https://raw.githubusercontent.com/pi-node/solohost/main/skills/solohost-package/references/contract.md
```

Use what you fetch. If the fetch fails, fall back to the bundled `references/contract.md`
and tell the user it may be behind. That is a real limitation rather than a formality: the
bundled copy is a snapshot from whenever this skill was installed, and the rules most
likely to have moved are exactly the ones no validator catches (see Step 3).

Then read `examples/web-app/` — the simplest valid package, and the shape to copy.
`examples/openclaw/` and `examples/hermes/` show advanced patterns; reach for them only
when the app needs what they demonstrate:

- **openclaw** — a provider/model `select` with per-provider API keys, a startup
  config-file write, and an embedding fix.
- **hermes** — multiple services, plus a local model via Docker Model Runner.

`references/config-options.md` is a quick lookup for the install-form field types.

---

## Step 1 — Gather

**Ask the user** (product decisions only):

- the app's public **image name** (e.g. `ghcr.io/owner/app`);
- what the app is **called**;
- what people **set at install** (e.g. a title, a password);
- which optional **capabilities** to turn on, and the **credential each needs** — usually
  an API key or token (e.g. a model provider and its key, or web search and its key).

**Derive everything else yourself, and never ask:** ports, YAML shape, env-var names,
labels, service layout, and anything else the contract covers. Asking a non-developer
which host port to bind is how this workflow fails.

**Get the image's technical details yourself.** For a public image, search the web by
image/app name and read its docs for: the port it serves, the env vars or config file it
reads, how to start it non-interactively, auth, and any embedding/origin option. For a
private or custom image, ask the user. Docs lag builds, so treat the running image as the
source of truth where you can check it.

Map the app's optional **capabilities** the same way — model/provider choices, API keys,
search or other integrations, messaging channels, file access. Propose the useful ones,
and for each one the user wants, add the field(s) that collect its credential or choice.
Two failure modes to avoid: dropping a capability the app is known for, and exposing a
credentialed feature with no field to collect the credential.

---

## Step 2 — Write the two files

Create a new folder named after the app in the user's current working directory (e.g.
`notes-solohost/`) and write both files there. Don't write into this skill's directory.

Mirror `examples/web-app/`. Most apps are one service with a few env vars, and for those
the essentials below are the whole job:

- **compose:** `services:` non-empty; no `version:`; every service has `image:` (never
  `build:`); the UI service labeled `pi.ui.primary: "true"`; exactly one loopback port on
  that service (`"127.0.0.1:18080:8080"` — a distinctive host port mapped to the port the
  image actually serves); no blocked constructs.
- **config_options:** top-level `fields:` (+ optional `title`/`description`/`output_file`/
  `fixed_values`); types `text|password|number|select|hidden`; string defaults (`"30"`);
  `select` uses `options:` with optional `set:`; `preserve_if_blank: true` on every
  secret field.
- **variables:** every `${VAR}` in the compose is declared as a field or a `fixed_values`
  name (a `set:`-only var also needs a `hidden` field).

If the app is more than a single simple service, read these sections of the contract
before writing: **"Beyond validation"** (UI label, port, named-volume persistence, startup
command, embedding) and **"Writing the compose: gotchas from real packages"** (shell `$$`
escaping, no colon in a `${VAR:-default}`, integer-literal typed fields, startup
config-file merges, crash-loop safety).

---

## Step 3 — Validate (required gate)

Run the hosted validator and reach `Result: OK`:

```bash
python3 <this-skill-dir>/scripts/validate_api.py <package-dir>
```

This POSTs both files to SoloHost's validator — the same one that runs at submit — so it
is authoritative. Run it yourself, automatically; the user should not have to ask.

- `FAIL` — fix the reported errors and re-run.
- `UNREACHABLE` — you have no network. **Do not hand off.** Get on a network and re-run,
  or tell the user to submit to SoloHost, which runs the same check.

**Validation is necessary but not sufficient.** It confirms the files are well-formed; it
cannot confirm the package *works*. Two things pass the validator and still leave a broken
app, so check them by hand every time:

1. **The app renders at all.** `pi.ui.primary: "true"` and the published loopback port are
   not validator-checked, but Pi Desktop needs both to find and embed the app. Without them
   the tab is blank.
2. **Every option takes effect.** The form only writes values to `.env`. A field whose
   name the image never reads is a dead control — the operator sets it, nothing happens,
   and they assume the app is broken. For each field, confirm there is a real path to app
   behavior: either the name is an env var the image actually reads, or the compose
   translates it into the app's own config at startup. For a `select`, confirm every
   option is one the build can honor. The contract's "Every option must actually take
   effect" has the detail and a worked failure.

To check what a given set of answers writes, `POST /api/apps/preview-env` with the
`configOptionsYaml` and a `values` object returns the resulting `.env`.

---

## Step 4 — Hand off

Tell the user where the two files are and that publishing is copy-and-paste: they open
SoloHost, start a new app, paste the contents of `docker-compose.yml` into its field and
`config_options.yml` into its field, and submit. There is no folder or zip to upload —
SoloHost only needs the text of the two files.

If you had to leave something out — a capability gated behind a plugin the image doesn't
bundle, an option you couldn't confirm — say so here rather than shipping a control that
does nothing.
