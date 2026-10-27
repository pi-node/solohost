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

These examples are patterns, not finished answers. Each one covers only what it
demonstrates, so even when the app you're packaging is one of them, don't treat its
example as the complete package. Research the app's current capabilities in Step 1 either
way.

`references/config-options.md` is a quick lookup for the install-form field types.

---

## Step 1 — Gather

Start by asking for the app's public **image name** (e.g. `ghcr.io/owner/app`) and what
the app is **called**. Then do the research below before asking anything else, because
the remaining questions depend on what the app can do.

**Get the image's technical details yourself.** For a public image, search the web by
image/app name and read its docs for: the port it serves, the env vars or config file it
reads, how to start it non-interactively, auth, and any embedding/origin option. For a
private or custom image, ask the user. Docs lag builds, so treat the running image as the
source of truth where you can check it.

**Derive everything else yourself, and never ask:** ports, YAML shape, env-var names,
labels, service layout, and anything else the contract covers. Asking a non-developer
which host port to bind is how this workflow fails.

**Map every optional capability.** From the app's current docs, not from a bundled
example, list everything the package could turn on: model or provider choices, search and
other integrations, messaging channels such as Telegram or Discord, file access, and so
on. For each one, work out what it needs to actually work in a SoloHost install. Often
that's just an API key or token, but sometimes it's more, and the operator only ever gets
the app's web UI, never a shell inside the container. If a feature needs a step after
install, check whether that step can be done in the app's web UI, or avoided with a
different mode. For example, if a messaging integration requires approving each new
contact, check whether that can be done in the web UI or avoided with an allowlist whose
identifier can be collected at install.

Don't treat a documented CLI command as proof that the operator needs a shell. Find out
what the command does: inspect the config schema or source, whether the image already
contains the required plugin, and whether the command merely writes a config file. If the
same setup can be expressed through environment variables, a startup config-file merge,
or an idempotent non-interactive startup command, the package can automate it. Mark a
capability unavailable only after confirming there is no such route and no setup route in
the web UI. This is technical research for you to resolve; don't ask the user whether you
should "attempt config-file wiring" or choose another implementation strategy.

### Gate: the capability table

**Don't start Step 2 until the user has answered this.** When you're close to finishing,
it's tempting to pick sensible features yourself and move on, and that's exactly how a
capability the app is known for disappears without anyone deciding to drop it. Which
features ship is the user's decision, not yours.

Print a table that covers every capability you found, including the ones you recommend
leaving out:

| Capability | What it does | What you'd need to provide | Recommendation |
| --- | --- | --- | --- |
| Telegram | Chat with the assistant from Telegram | A bot token from @BotFather and your Telegram user ID | Include |
| *(every other capability)* | | | Include, or Exclude and why |

Write it in plain language, and give every Exclude a reason the user can follow, such as
"needs a setup step that can't be done from SoloHost". A non-developer usually can't name
an app's integrations from memory, which is why an open "which features do you want?"
doesn't work and the table does.

Keep it short enough to read in a minute, roughly 10–15 rows. Give the capabilities most
people would want their own rows. Group the long tail, such as regional chat apps, niche
networks and admin-only features, into a few rows, and name every item in each group so
nothing disappears from view. Never collapse the app's defining capability into one
catch-all row. If messaging is a core function, for example, list major channels
separately when their setup differs. Grouping is only for making the table readable; it
must not hide individual choices in the questions that follow. Put everything confirmed
not to work on SoloHost into one unavailable group with the reason. Features that are
always on and need no decision can go in one line above the table.

Then ask the user to choose:

- **Ask which named capabilities the package should offer**, not how to implement them.
  Every capability that you confirmed can be packaged must appear by name as a selectable
  option, even if it shared a row in the table. A recommendation or an "Exclude" label
  never substitutes for asking.
- **If the app has more than one known integration, use structured questions**: your
  assistant's multiple-choice question tool if it has one (`AskUserQuestion` in Claude
  Code, the equivalent in Cursor or others). Use one multi-select per category — model providers,
  messaging channels, search integrations, and so on — and split a category across
  questions if the tool limits option count. If an app supports several packageable
  messaging channels, for example, ask "Which messaging channels should the install form
  configure?" and offer every confirmed channel individually.
- The creator is choosing what the install form will **offer**, which is different from
  what one operator will activate later. Use multi-select when the form can offer several
  model providers even if the operator will choose one provider from a `select` at
  install time. Use single-select only when the package itself can include exactly one
  choice.
- **Don't pre-select anything.** Your recommendation belongs in the table; the choice is
  theirs.
- Don't offer a capability you confirmed cannot work, but don't silently turn uncertainty
  into "unavailable" either — finish the technical research first. Show truly unavailable
  capabilities in the table with the concrete blocker.
- If your assistant has no structured question tool, ask the same named choices in chat
  and wait for the reply.
- **If you can't ask at all**, for example in a non-interactive run, stop after the table
  and say you need their choices. Don't decide for them.

For each capability they pick, add the field(s) that collect its credential or choice. A
credentialed feature with no field for its credential is a control that can never work.
Also ask what people **set at install** (e.g. a title or a password).

---

## Step 2 — Write the two files

Only start once the user has answered the capability question at the end of Step 1.

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
- `RATE LIMITED` (exit 4) — wait a minute and re-run. Don't change the package.
- `UNREACHABLE` — you have no network. **Do not hand off.** Get on a network and re-run,
  or tell the user to submit to SoloHost, which runs the same check.

**Validation is necessary but not sufficient.** `Result: OK` means the files are
well-formed, not that the app shows up in Pi Desktop. Several mistakes pass the validator
and still leave a blank tab, so don't stop at the first OK.

### Install checklist (after `Result: OK`, every time)

Go through the **Install checklist** section of the contract you fetched in Step 0, every
time, and fix any miss. Re-run the validator after a fix.

### Local run (when Docker is available)

If `docker info` works (Docker is installed and running), start the package once before
handing off. This is the only check that proves the app actually serves its UI.

1. Write a throwaway `.env` exactly as the install form would:
   `python3 <this-skill-dir>/scripts/validate_api.py --preview-env <package-dir> KEY=dummy ...`
   Use placeholder values only (e.g. `TELEGRAM_BOT_TOKEN=dummy`), never the user's real
   keys. Real values go only into the Pi Desktop install form.
2. `docker compose -p solohost-check -f docker-compose.yml --env-file .env config` must
   succeed.
3. Check the host port is free first (`lsof -i :HOST` or `netstat -an`). If it isn't, the
   app may already be installed in Pi Desktop; tell the user and don't stop their copy.
4. `docker compose -p solohost-check -f docker-compose.yml --env-file .env up -d`
5. Wait for the healthcheck (or up to ~2 minutes), then
   `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:HOST/`. 2xx/3xx is up, and so
   is 401/403 when the app has its own login. 404, 5xx or no answer is a failure: read
   `docker compose -p solohost-check logs` and fix the package.
6. Always clean up, even on failure: `docker compose -p solohost-check down -v`, and
   delete `<package-dir>/.env` so it can't be committed next to the package.

If Docker isn't installed or running, skip this and say so in the hand-off, so the user
knows the package was checked but never started.

---

## Step 4 — Hand off

Tell the user where the two files are and that publishing is copy-and-paste: they open
SoloHost, start a new app, paste the contents of `docker-compose.yml` into its field and
`config_options.yml` into its field, and submit. There is no folder or zip to upload —
SoloHost only needs the text of the two files.

Say whether the local run passed or was skipped because Docker wasn't available.

Then recap the capabilities: which ones the package includes, and which were left out and
why. That covers both the ones the user chose to skip and any you couldn't make work after
all, such as a capability gated behind a plugin the image doesn't bundle or an option you
couldn't confirm. Say so here rather than shipping a control that does nothing.
