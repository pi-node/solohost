# Solohost App Starter Kit

Use this repository to build a valid **SoloHost package**: the set of files SoloHost
needs to install and run your app on someone's computer. Clone and hand this repo off
to an **AI coding assistant**, follow the flow, and produce:

- `docker-compose.yml`: which app to run.
- `config_options.yml`: the settings the installer will ask people to fill in.

You don't need to be a developer to follow this. At the end, you paste the contents of
the two files into SoloHost to publish your app.

**Important:** these files do **not** contain your app's design, screens, or code.
Your app already lives inside a **Docker image**; these files just tell SoloHost how to
run that image. So building a package is never about how your app looks. It's about
pointing at your image and listing its install settings.

---

## Before you start: what you need

- [ ] **This repo.** Get it in Step 1 below.
- [ ] **An AI coding assistant**, such as [Claude Code](https://claude.com/claude-code)
      or [Cursor](https://cursor.com).
- [ ] **A public Docker image for your app** that's already published. Have its name
      ready, e.g. `ghcr.io/owner/app`. (Most well-known apps already have one. An
      "image" is your app packaged so any computer can run it.)

---

## Step 1. Get your own copy of this repo

You just need this repo's files on your computer. Easiest: click **Code → Download
ZIP** and unzip it. (Prefer your own GitHub copy? Use **"Use this template" → Create a
new repository**, or **Fork**, then open that.)

---

## Step 2. Open it in your AI assistant

Point your assistant (Claude Code or Cursor) at the folder. Once it has the repo, it
has the built-in instructions that tell it the rules for a valid package, so you won't
have to explain them. It won't start on its own or ask you about your app; you kick
things off in the next step.

---

## Step 3. Ask the assistant to build your package

Start with one line giving your image name. From there **the assistant asks you the
rest in plain language.** It already knows, from this repo, what to ask, and handles
anything technical on its own.

> "Build a SoloHost package for my app. Its image is `ghcr.io/owner/notes`."

Then answer its questions, things like what the app should be called, whether people
should set a password, and which optional features to offer (for example web search, if
your app supports it) along with any API key those features need. You never have to
mention ports, YAML, or anything technical.

You don't need to track down any technical docs yourself. For a well-known app, the
assistant looks up its documentation on its own to get details like the port and
settings right. For a niche or custom image with no public docs, it may ask you a couple
of quick questions instead.

---

## Step 4. Get your files and check them

The assistant creates a new folder with your two files (`docker-compose.yml` and
`config_options.yml`) and automatically checks them against SoloHost's own validator, the
same one used when you publish. It won't hand the package over until that check passes, so
you know up front it will be accepted. You don't have to run anything or ask for this.
If the check finds problems, just tell the assistant "fix the failures" and it will.

---

## Step 5. Publish

Your package is just the text of the two files, so publishing is copy-and-paste:

1. Open the folder the assistant made in Step 4 (it will tell you where it is), or ask
   it to print the contents of both files in the chat.
2. Copy the full contents of `docker-compose.yml`.
3. In your browser, open SoloHost, start a new app, and paste that into the
   `docker-compose.yml` field.
4. Do the same with `config_options.yml`, pasting it into its field.
5. Submit. SoloHost runs the real, final validation at that point and, if it passes,
   publishes your app.

You don't upload the folder or a zip. SoloHost only needs the text of the two files.

---

## Optional: check a package yourself

You don't need this if you use the assistant, since it runs the check for you. But if
you already have the two files and want to check them by hand, put both
(`docker-compose.yml` and `config_options.yml`) together in a folder, install
[Python 3](https://www.python.org/downloads/), and from inside the repo folder run:

```bash
python3 scripts/validate_api.py path/to/your/folder
```

This is the real check against SoloHost's validator (needs internet; no extra install).
It ends with **"Result: OK"** or a list of things to fix. Point it at the **folder** (both
files together), not a single file.

---

## What each file in this repo does

You'll mostly only touch the output from Step 4. Here's what everything is:

| File / folder | What it's for |
| --- | --- |
| `README.md` | This guide, the tutorial for you. |
| `SOLOHOST.md` | The rules a valid package must follow. The assistant reads this. |
| `AGENTS.md` | The **technical guide the assistant follows** (loaded automatically). You don't need to read it. |
| `CLAUDE.md` | Same, for Claude Code specifically. Loaded automatically. |
| `examples/` | Finished example packages the assistant copies from. Start with `web-app` (Grafana, the simplest); `openclaw` (OpenClaw AI; cloud) and `hermes` (Hermes Agent; multi-service, local-model-capable) show advanced patterns. |
| `schema/` | A reference for the install-form field types. |
| `scripts/validate_api.py` | The real check against SoloHost's validator; the assistant runs this on your files. |
| `LICENSE`, `CONTRIBUTING.md` | Standard housekeeping; ignore. |

---

*This is v0. `SOLOHOST.md` currently lists only the rules SoloHost enforces today; more
will be added over time.*
