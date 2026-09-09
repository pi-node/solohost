# SOLOHOST.md — The SoloHost Package Contract (v0)

This is the contract for a **SoloHost package**: the two files a publisher pastes into
SoloHost so Pi Desktop can install and run their app.

| File | Role |
| --- | --- |
| `docker-compose.yml` | The runtime stack — which container(s) to run. |
| `config_options.yml` | The install form — the questions shown to the operator. |

No app source lives in a package; it points at a pre-built, public image.

> **v0 scope & status.** This documents what SoloHost enforces **today**, matched to
> known-good example files. Rules that are proposed/planned but not yet enforced are
> under [Not enforced yet](#not-enforced-yet). Pending final reconciliation with the
> Container Compatibility Spec.

---

## How a package is installed

Publishing is content-based: the publisher pastes the two files; SoloHost stores them
and Pi Desktop, at install, fetches them, **pulls** the image (never builds), renders
`config_options.yml` as a form, writes the answers to the file named by `output_file`
(e.g. `.env`), and runs `docker compose up -d`.

---

## 1. `docker-compose.yml`

Example:

```yaml
services:
  web:
    image: ghcr.io/your-org/your-app:latest   # a pushed, public image
    restart: unless-stopped
    labels:
      pi.ui.primary: "true"                    # REQUIRED for Desktop to surface + embed this service
    ports:
      - "127.0.0.1:18080:8080"                 # loopback 127.0.0.1:HOST:CONTAINER — distinctive host port -> the port the image serves
```

To pass the operator's settings to the app, add an `environment:` block that
interpolates `${VAR}` (see `examples/web-app/`). Every `${VAR}` must be declared in
`config_options.yml`, and each should be named after an environment variable your
image actually reads.

Rules (all **enforced today** unless noted):

- **`services:` present and non-empty.** (A top-level `version:` is obsolete and simply
  ignored — omit it; the validator does not reject it.)
- **Every service has an `image:`.** `build:` is **not supported** — Desktop pulls,
  never builds. The image must be public/pullable *(image reachability itself is not
  checked yet — see below)*. **Use an immutable, versioned tag** (e.g. `name:1.2.3`) rather
  than `:latest` when the image publishes one — the examples here do. `:latest` is mutable,
  so different installs can resolve to different images depending on when each was pulled,
  and it can jump a major version and break a setup that previously worked. (The validator
  still accepts `:latest`, but pin your tag.)
- **Mark the UI service with `pi.ui.primary: "true"`.** This is how Pi Desktop finds
  the one service to surface, read the port from, and embed. It is *not checked by the
  validator*, but without it Desktop can't detect your app — the "Bound to" / "Serving
  on" fields stay blank and nothing renders. Set it on exactly one service.
- **Publish exactly one port on the UI service, loopback-bound**, in the form
  `127.0.0.1:HOST:CONTAINER` — for example `ports: - "127.0.0.1:18080:8080"`. `CONTAINER`
  is the port the image actually serves; `HOST` is the port SoloHost reaches it on and
  **does not have to equal** `CONTAINER`. Follow the Hermes reference package: map a
  **distinctive, high, unlikely-to-clash host port to the container's real port** (Hermes
  uses `18642:8642` and `18787:8787`) rather than reusing the container port on the host.
  This rule is scoped to the **UI service** (`pi.ui.primary`): publish exactly one port
  there. Ports on *other* services are allowed and ignored by Desktop — that is why the
  Hermes gateway service can publish its own port alongside the Web UI's.
  Note: if you redeploy and hit "Host port already in use," it's a leftover container from
  a previous deploy still holding that port — stop/remove it (or fully uninstall the app)
  before reinstalling; that's a SoloHost cleanup gap, not a problem with this line.
- **Blocked constructs (rejected):** `privileged`; `cap_add`; `security_opt`; `extends`;
  host networking (`network_mode: host`); container networking
  (`network_mode: container:...`); `userns_mode: host`; host namespaces
  (`pid`/`ipc`/`uts`/`cgroup: host`); `devices`; bind mounts / unsafe mounts; host-driver
  networks; top-level `include`; top-level bind-backed volumes; file-backed
  `secrets`/`configs`.
- `restart:` is allowed. `container_name:` and `restart:` policy are **not enforced**
  (avoid `container_name:` anyway — it collides on reinstall).

### Local models: Docker Model Runner

If your package runs a model **on the node** (rather than calling a cloud API), do it
through Compose's Docker Model Runner (DMR) integration: a top-level `models:` element
names the model, and a per-service `models:` mapping injects DMR's OpenAI-compatible
endpoint and resolved model name into environment variables the app reads (see
`examples/hermes/`, and `examples/openclaw/` for a cloud-only contrast). This requires
**Docker Model Runner to be enabled on the host** — it serves the model with host
acceleration; there is no in-container GPU path. If DMR is not enabled, the local-model
options will not work, so state that requirement in the field `help`/`after_save` text
for any local option (as the examples do). Two DMR gotchas that bite in practice: the
top-level model reference cannot use a `${VAR:-default}` whose default contains a colon
(an image/model tag like `ai/gemma4:E4B` trips SoloHost's variable parser — give the var
a declared default and reference it plainly), and typed fields such as `context_size:`
must be integer literals, not interpolated.

---

## 2. `config_options.yml`

Example (this is the exact shape — copy it):

```yaml
title: My App Configurator
eyebrow: SoloHost App          # small label shown above the title
description: Short text shown above the install form.
footer_hint: Need help? ...    # small text shown under the form
output_file: .env
after_save: >                  # message shown after the operator saves
  Saved. Reinstall to apply.
# Values always written to output_file, never shown as inputs.
fixed_values:
  - name: UID
    detect: uid            # auto-resolved: uid | gid | pi_username
  - name: APP_MODE
    value: "production"    # or a literal constant instead of detect:
fields:
  - name: APP_PASSWORD
    label: Admin password
    type: password          # text | password | number | select | hidden
    required: true
    preserve_if_blank: true # on re-save, keep the saved secret if left blank
    help: Shown as a hint under the field.
    env_comment: Written as a comment above this key in .env.
  - name: MODEL_PROVIDER
    label: Model provider
    type: select
    default: local
    options:
      - value: local
        label: Local model
      - value: openai
        label: OpenAI
        set:                # extra .env keys applied when this option is picked
          BASE_URL: https://api.openai.com/v1
  - name: OPENAI_API_KEY
    label: OpenAI API key
    type: password
    visible_if:             # only shown for the openai option
      field: MODEL_PROVIDER
      in: [openai]
```

Rules (**enforced today**):

- **Top level (closed set).** The recognized top-level keys are `title`, `eyebrow`,
  `description`, `footer_hint`, `output_file`, `after_save`, `fixed_values`, and
  `fields`. The schema is strict: **any unrecognized top-level key is rejected**
  (`config.additionalProperties`), so do not invent keys. `fields:` is the list of
  inputs; `eyebrow`/`footer_hint` are small labels above/below the form; `after_save` is
  a message shown once the operator saves.
- **Field types:** `text`, `password`, `number`, `select`, `hidden`. Each field's
  `name` is the `.env` key it writes.
- **`help`** is the hint text. **`placeholder`, `min`, and `max` are NOT supported and
  are rejected.**
- **`preserve_if_blank: true`** keeps the previously-saved value when the operator
  re-saves the form with the field left blank. **Put it on every `password`/secret
  field** — otherwise re-saving the install form wipes the stored API keys and passwords.
- **`env_comment`** writes a comment line above that key in the generated `.env`.
- **Defaults are strings** — `default: "30"`, not `default: 30` (a bare number is
  ignored). Plain string values like `default: local` are fine.
- **`select`** uses `options:` — a list of `{value, label}`, each optionally with a
  `set:` block of extra `.env` keys applied when chosen.
- **`fixed_values`** are written to `.env` without being shown. Each has a `name` and
  either a `detect:` of `uid`, `gid`, or `pi_username`, **or** a literal `value:` (a
  constant string written as-is).
- **`visible_if`** (`{field, in: [...]}`) conditionally shows a field.

### Variables must be declared

Every `${VAR}` used in `docker-compose.yml` must be declared in `config_options.yml`
as a **field name** or a **`fixed_values` name**.

> **Known `set:` limitation.** Keys written only via a `select` `set:` block are **not**
> counted as declared by the undeclared-variable check. If the compose references such
> a key, also declare it as a `hidden` field, or install fails.

### Every option must actually take effect (not validator-checked)

The install form only *collects* values — it writes them to `output_file` and stops. It
is on the package to make each value actually change the running app. A field that
validates but that the app never reads is a dead control: the operator sets it, sees no
effect, and assumes the app is broken. For every field you expose, there must be a real
path from the form to app behavior:

- **Reaches the app.** Either the field's `name` is an environment variable the image
  *actually reads*, or the compose translates it at startup into the app's own config
  (e.g. a `command:` that writes the value into the app's config file — see
  `examples/openclaw/`). Naming a field after a variable the image ignores does nothing.
- **Every choice is real.** If a field offers a set of options (a `select` of providers,
  modes, models), each option must map to something the app's build can actually honor.
  Do not offer a choice the app can't fulfill. *Concrete failure:* OpenClaw's form let the
  operator pick "Anthropic," but on its own that only wrote a preference — the app booted
  with no Anthropic model registered, so the picker showed nothing usable. The fix was a
  startup step that maps the chosen provider to a real, supported model ref (confirmed via
  the app's own `/model list`, not from docs) and activates it. Offer only options the app
  can deliver, and wire the choice through to the thing that makes it live.
  An option can be satisfied one of two ways: the package **explicitly wires it** (a
  startup mapping like the above), or the **app's own built-in default already handles
  that choice** (e.g. the option matches the provider/mode the image defaults to, so it
  works once the credential is supplied). Both are valid, but the second is an edge case
  worth confirming: verify the app's default actually covers the option, and prefer
  explicit wiring where practical, since a default that isn't pinned can change between
  image versions and silently stop covering it.
- **Verify by running, not by reading.** Confirm the selected option is actually live in
  the app after install (the model is selected, the feature is on, the credential is
  accepted) — not merely present in `.env`. Docs can lie about what a build supports;
  the running app is the source of truth.

### `detect: pi_username`

`detect: uid`, `detect: gid`, and `detect: pi_username` are all accepted by the
validator. Use `pi_username` only for **attribution/display** — a Pi username is PII and
is never authentication, payout, ownership, or access control. Do not gate any privilege
on it.

---

## Beyond validation — making the app actually render

Passing the validator only means the files are well-formed. For the app to install
*and work in the App tab*, also get these right (none are validator-checked):

- **UI service + port (above).** Exactly one service labeled `pi.ui.primary: "true"`,
  publishing one loopback port in the `127.0.0.1:HOST:CONTAINER` form. Without them
  Desktop can't surface the app.
- **Persistence — use a named volume, not a bind mount.** Two different things
  "persist", and only one needs a volume:
  - *Operator-entered settings* (the `config_options.yml` fields — tokens, API keys,
    choices) are written to `.env` at install and **re-applied on every start**. They
    stay stable **without** a volume; the operator sets them once in the install form.
  - *Data the app generates itself* (its database, sessions, device pairings, settings
    changed inside the app's own UI) lives on disk in the container and is **lost on
    restart unless** you mount a named volume. Declare it at the top level. Host bind
    mounts are blocked.
  The publisher/agent decides whether a volume is needed (does the app store state?) —
  it's not something the operator chooses.

  ```yaml
  services:
    web:
      # ...
      volumes:
        - myapp_data:/data        # named volume (allowed); NOT a host path like ./data
  volumes:
    myapp_data:
  ```

- **Startup command if the image needs one.** Some images won't start unattended (they
  expect a setup wizard, a subcommand, or a flag). Set it explicitly:

  ```yaml
      command: ["the-app", "serve", "--no-interactive"]
  ```

- **Embedding.** If the tab loads blank or says the origin is rejected, the app guards
  which origin may connect (frame-blocking, CORS, an allowed-origins list, or a
  base/root-URL setting). Important reality: **Desktop reaches the app on the loopback
  host port you published** (`127.0.0.1:HOST`), which is a different origin from the one
  the app assumes internally (`localhost:CONTAINER`) — so an app that only trusts its own
  fixed origin will reject the proxied origin, and you can't always reach its settings to
  fix it (that's origin-gated too).
  For such apps, look in the image's docs for a setting that accepts a proxied origin —
  "allow embedding", "allowed origins", a **host-header / origin fallback**, or a
  base/root-URL option — and set it via `environment:` or, if it's config-file-only, by
  having the container write a minimal config at startup (see `examples/openclaw/` for
  the pattern). Apps that don't police origins (whoami, most static UIs) need none of
  this.

---

## Writing the compose: gotchas from real packages

Practical traps hit while packaging real images. They are general (not tied to one
specific app), but each applies only when its situation comes up — every bullet leads
with that condition. If a bullet's condition doesn't match your app (no `command:`, no
config file, no local model, no optional feature), skip it; don't go looking for
something to verify. None are caught by the pre-flight validator.

- **Start from the image's own docs (when public).** For a published image, its
  documentation is the source for: the port it serves, the environment variables or
  config it reads, how to start it non-interactively, auth, and any embedding/origin
  option. Reference those docs when they exist. If it is your own custom image, you
  already know these. Either way, confirm against the actual image: published docs often
  lag the build (renamed tags, config keys the build no longer accepts, features that
  moved), so treat the running image as the source of truth.

- **Escape shell variables inside `command:` as `$$`.** Docker Compose interpolates
  `$VAR` / `${VAR}` throughout the compose file, including inside a `command:` string. A
  variable meant for the container's shell at runtime must be written `$$VAR`, or Compose
  consumes it at parse time and the shell sees an empty value.

- **Do not put a colon in a `${VAR:-default}` default.** SoloHost's variable parser
  mis-reads a default value that contains `:` (for example an image/model tag like
  `owner/name:tag`) and reports "referenced variable is not declared." Instead give the
  variable a declared field (or `fixed_values`) default and reference it as plain
  `${VAR}`.

- **Typed compose fields must be literals, not interpolated.** Any field the Compose
  schema types as a number (or other non-string) has to be a literal, e.g.
  `context_size: 65536`. Interpolation always yields a string, so `context_size:
  ${SOME_VAR}` makes `docker compose config` fail. Interpolate string fields only.

- **File-configured apps: write the config at startup.** If the app is configured by a
  JSON/YAML file rather than by environment variables, a `command:` can read that file,
  merge in the operator's values from the environment, write it back, then `exec` the
  app (see `examples/openclaw/` and `examples/hermes/` for the pattern). Merge rather
  than overwrite so settings the app writes itself survive a restart, and remove any key
  a previous boot wrote that the current version no longer wants.

- **A bad config value can crash-loop the app.** An invalid config key, or pinning a
  provider/feature the image does not actually have, can make the app exit and restart
  repeatedly. Because a startup config-write persists into the named volume, a bad key
  written once keeps crashing on every boot until it is removed. Prefer values you have
  confirmed the image accepts, and only enable a feature (or pin a provider) when its
  credential or dependency is actually present, so an empty or absent one cannot take the
  app down.

- **A feature can need more than a key.** Some images gate a capability behind a plugin
  or provider the base image does not bundle; supplying an API key alone will not switch
  it on. After install, confirm the feature is actually available (the tool or command
  appears, the model is listed), not just that the key was written. If a feature is gated
  behind a plugin the image does not include, tell the creator rather than shipping a
  control that does nothing.

- **Only if an option runs a model on the node: size the app to that model's limits.**
  Skip this entirely for apps that don't run a local model. A small on-device model has a
  far smaller context window than a cloud model, and an app that assumes a large window
  can fail at runtime (e.g. context-management or compaction steps that reserve more
  tokens than the window holds). So when a local-model option is present, set the app's
  context/reserve limits from that model's actual window rather than leaving cloud-sized
  defaults, and, where the app supports it, gate tool-use on whether the chosen model is
  large enough. (`examples/hermes/` runs a local model this way.)

---

## Enforcement status

| Enforced today | Not enforced yet | Proposed (needs new work) |
| --- | --- | --- |
| blocked compose constructs (above); supported field types; `placeholder`/`min`/`max` rejected; published-port required; undeclared-variable check | `container_name`; `restart` policy; loopback-binding rule; healthcheck presence/quality; image availability/public reachability | mandatory single UI service (`pi.ui.primary`); exactly-one published port on the UI service; healthcheck-based readiness gating; image digest pinning + update/rollback |

> **Important — validation is not enough.** `pi.ui.primary` and the UI service's
> published loopback port are **not checked by the validator**, but they are **required
> for the app to actually work**: Desktop uses the label to find your UI service and
> reads the **published host port** from the running container (via `docker compose ps`)
> to reach and embed it — it does **not** assign a port for you, so you must publish one.
> A package can *pass validation and still render nothing* (blank "Bound to" / "Serving
> on") if either is missing. Always include both. There are **no** `pi.ui.port` or
> `pi.health.path` labels — the port comes from the binding. Legal terms (code of
> conduct, indemnity, removal) are policy, not validated.

## Not enforced yet

The proposed column above is intentionally out of v0. Notably: `:latest` tags are
currently accepted (digest pinning is a future improvement), and healthchecks are not
required.

## Validation

**The hosted validation API is authoritative and is the required gate before a package
ships.** It runs the same validator SoloHost uses at submit, so `ok: true` there is the
real answer, and it is the only validation this repo relies on.

### Hosted validation API

`POST https://solohost-nohcqud24xwnsmna.staging.piappengine.com/api/apps/validate`
(staging). Public — no login or token. Send the contents of both files as JSON:

```json
{
  "composeYaml": "<contents of docker-compose.yml>",
  "configOptionsYaml": "<contents of config_options.yml>"
}
```

The response is `{"ok": true}` when the package passes, or `{"ok": false, "errors": [...]}`
with the failing rule(s) when it does not (e.g. adding `privileged: true`, or referencing
a `${VAR}` not declared in `config_options.yml`, returns the matching rule).

`scripts/validate_api.py <package-dir>` wraps this: it reads both files from the folder,
POSTs them, prints the result, and exits non-zero on failure (needs only the Python
standard library — no extra packages). With no argument it checks every dir under
`examples/`.

```bash
python3 scripts/validate_api.py examples/web-app
```

A freshly-woken API instance can return HTTP 502 for a few seconds on a cold start;
`validate_api.py` retries transient 5xx/transport errors automatically, so a blip does
not read as a validation failure. If you call the endpoint by hand and get a 502, wait
~30s and retry.

**Preview the generated `.env`.** `POST /api/apps/preview-env` with the same
`configOptionsYaml` plus a `values` object of operator answers returns the `.env` that
those answers would produce — useful for confirming a field (or a `select` `set:`)
actually writes the key you expect.

The authoritative validators also run again at submit/install (backend + Pi Desktop). The
long-term path remains shared conformance fixtures so all validators stay in sync.
