# `config_options.yml` field reference

Quick lookup for the install-form schema. Authoritative rules are in `SOLOHOST.md` §2;
this matches the known-good example shape.

## Top level

The recognized top-level keys are a **closed set** — any other key is rejected
(`config.additionalProperties`). They are: `title`, `eyebrow`, `description`,
`footer_hint`, `output_file`, `after_save`, `fixed_values`, `fields`.

```yaml
title: <shown above the form>
eyebrow: <small label above the title>      # optional
description: <short text under the title>
footer_hint: <small text under the form>    # optional
output_file: .env                 # file the answers are written to
after_save: <message shown after saving>    # optional
fixed_values:                     # written to output_file, never shown
  - name: <ENV_KEY>
    detect: uid                   # uid | gid | pi_username
  - name: <ENV_KEY>
    value: "constant"             # ...or a literal value instead of detect
fields:                           # the visible inputs
  - name: <ENV_KEY>
    label: <shown to the operator>
    type: text                    # text | password | number | select | hidden
    required: true                # optional
    help: <hint under the field>  # optional
    default: "..."                # optional; strings only ("30", not 30)
    preserve_if_blank: true       # optional; keep saved value if re-saved blank
    env_comment: <comment written above this key in .env>   # optional
```

## Field types

`text`, `password`, `number`, `select`, `hidden`. Each field's `name` is the `.env`
key it writes.

## Supported vs rejected keys

- Supported per field: `name`, `label`, `type`, `required`, `help`, `default`,
  `options` (select), `set` (inside a select option), `visible_if`,
  `preserve_if_blank`, `env_comment`.
- **Rejected:** `placeholder`, `min`, `max`.
- `help` is the hint (there is no `placeholder`). Defaults must be strings.
- **`preserve_if_blank: true`** keeps the saved value when the form is re-saved with the
  field left blank — put it on every `password`/secret field so re-saving does not wipe
  stored keys/passwords.
- **`env_comment`** writes a comment line above that key in the generated `.env`.

## `select` with `options` and `set`

```yaml
  - name: MODEL_PROVIDER
    type: select
    label: Model provider
    default: local
    options:
      - value: local
        label: Local model
      - value: openai
        label: OpenAI
        set:                       # extra .env keys applied when chosen
          BASE_URL: https://api.openai.com/v1
```

> If a `set:` key is referenced as `${VAR}` in `docker-compose.yml`, also declare it as
> a `hidden` field — the undeclared-variable check does not count `set:` keys.

## Conditional fields

```yaml
  - name: OPENAI_API_KEY
    type: password
    label: OpenAI API key
    visible_if:
      field: MODEL_PROVIDER
      in: [openai]
```

## Auto-resolved values (`fixed_values`)

Each entry uses either `detect:` (resolved at install) or a literal `value:`.

```yaml
fixed_values:
  - name: UID
    detect: uid                   # uid | gid | pi_username
  - name: APP_MODE
    value: "production"           # a constant string, written as-is
```

`pi_username` is for attribution/display only — it is PII, never authentication,
ownership, or access control.

## The rule that ties compose to the form

Every `${VAR}` used in `docker-compose.yml` must be declared here as a **field name**
or a **`fixed_values` name**.
