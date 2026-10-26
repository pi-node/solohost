# SoloHost Package Skill

Publish your app on SoloHost. Your app already lives in a **public Docker image**; this
skill writes the two files SoloHost needs to install and run it on someone's computer:

- `docker-compose.yml` — which image to run.
- `config_options.yml` — the settings the installer asks people to fill in.

You don't need to be a developer, and you never write YAML. You answer a few plain
questions and paste two blocks of text into SoloHost.

> These files do **not** contain your app's design, screens, or code — just a pointer to
> your image and its install settings. Building a package is never about how your app looks.

---

## Install

Once, one command:

```bash
npx skills add pi-node/solohost
```

It detects your assistant and installs to the right place — Cursor, Claude Code, Codex,
Zed, Copilot and 70-odd others. Add `-g` to install globally rather than into the current
project, and run `npx skills update` later to pick up changes.

**Claude Code users** can install it as a plugin instead. Same skill; the plugin adds
version pinning and lets you hand it to a whole team through a project's
`.claude/settings.json`:

```bash
claude plugin marketplace add pi-node/solohost
```

```bash
claude plugin install solohost@solohost
```

Already inside Claude Code (or the Claude desktop app's Code tab)? Type the same thing as
slash commands instead:

```
/plugin marketplace add pi-node/solohost
/plugin install solohost@solohost
```

Then start a new session so the skill loads.

## Use

From any folder, tell your assistant what your image is:

> "Build a SoloHost package for my app. Its image is `ghcr.io/owner/notes`."

It takes over from there — asking what the app is called, whether people set a password,
which optional features to offer and the API key each one needs. It looks up your image's
technical details itself, writes both files into a new folder, and checks them against
SoloHost's own validator before handing them to you. It won't hand off until that passes.

## Publish

Copy-and-paste. Open SoloHost, start a new app, paste the contents of `docker-compose.yml`
into its field and `config_options.yml` into its field, then submit. There's no folder or
zip to upload — SoloHost only needs the text of the two files.

---

## What you need

- A **public Docker image for your app**, already published, e.g. `ghcr.io/owner/app`.
  (An "image" is your app packaged so any computer can run it. Most well-known apps
  already have one.) Creating an image is out of scope here.
- **An AI assistant** — Claude Code, Cursor 2.4+, or another that supports Agent Skills.

## Assistant that doesn't support skills?

Clone the repo, open it, and tell the assistant to follow
[`skills/solohost-package/SKILL.md`](skills/solohost-package/SKILL.md) — the same
instructions the skill uses. The tradeoff is that you work inside the clone rather than
your own folder, and you re-clone to pick up changes.

## Checking a package by hand

You don't need this — the skill runs it for you. But if you already have both files in a
folder and want to check them yourself, with [Python 3](https://www.python.org/downloads/):

```bash
python3 skills/solohost-package/scripts/validate_api.py path/to/your/folder
```

This is the real check against SoloHost's validator (needs internet, no install). It ends
with **"Result: OK"** or a list of things to fix. Point it at the **folder** holding both
files, not at one file.

---

## What's in here

| Path | What it's for |
| --- | --- |
| `skills/solohost-package/SKILL.md` | The procedure the assistant follows. |
| `skills/solohost-package/references/contract.md` | **The rules a valid package must follow.** The contract. |
| `skills/solohost-package/references/config-options.md` | Install-form field reference. |
| `skills/solohost-package/examples/` | Finished packages to copy. Start with `web-app` (Grafana, simplest); `openclaw` (provider keys, config write, embedding) and `hermes` (multi-service, local model) are the advanced ones. |
| `skills/solohost-package/scripts/validate_api.py` | The authoritative check against SoloHost's validator. |

---

*This is v0. The contract lists only the rules SoloHost enforces today; more will be added
over time.*
