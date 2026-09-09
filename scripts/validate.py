#!/usr/bin/env python3
"""
Lightweight, NON-AUTHORITATIVE pre-flight check for a SoloHost package.

It mirrors the SoloHost validator's *currently enforced* rules as closely as we can,
so an author or agent can catch obvious problems locally. It is NOT the real
validator — the SoloHost backend and Pi Desktop validators are authoritative, and a
`PASS` here does not guarantee acceptance. When in doubt, submit to SoloHost.

Checks (enforced-today, per the contract):
  files.present     both docker-compose.yml and config_options.yml exist and parse
  compose.services  top-level `services:` present and non-empty
  compose.image     every service has an `image:`; `build:` is not supported
  compose.blocked   blocks privileged, host/container network modes, host namespaces,
                    userns_mode: host, devices, bind mounts, host-driver networks,
                    top-level include, bind-backed volumes, file-backed secrets/configs
  compose.ports     at least one service publishes a port
  config.schema     config_options has a `fields:` list (+ optional `fixed_values:`)
  config.fields     supported field types only; placeholder/min/max are rejected
  config.detect     fixed_values detect is one of uid | gid
  env.declared      every ${VAR} in the compose is declared in config_options
                    (a field name or a fixed_values name; note: select `set:` keys do
                    NOT count as declared — declare them as a hidden field too)

Usage:
  python3 scripts/validate.py <package-dir> [<package-dir> ...]
  python3 scripts/validate.py            # defaults to every dir under examples/

Requires PyYAML:  pip install pyyaml
"""

import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.stderr.write("This check needs PyYAML. Install it with:  pip install pyyaml\n")
    sys.exit(2)

COMPOSE = "docker-compose.yml"
CONFIG = "config_options.yml"
FIELD_TYPES = {"text", "password", "number", "select", "hidden"}
UNSUPPORTED_FIELD_KEYS = {"placeholder", "min", "max"}
DETECT_VALUES = {"uid", "gid"}   # v0: pi_username is not accepted by the validator yet
HOST_NAMESPACE_KEYS = ("pid", "ipc", "uts", "cgroup")
VAR_RE = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)")


class Report:
    def __init__(self):
        self.fails = 0

    def ok(self, rule, msg):
        print(f"  [PASS] {rule}: {msg}")

    def fail(self, rule, msg):
        self.fails += 1
        print(f"  [FAIL] {rule}: {msg}")


def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)


def find_vars(node, acc):
    if isinstance(node, str):
        for m in VAR_RE.finditer(node):
            acc.add(m.group(1))
    elif isinstance(node, dict):
        for v in node.values():
            find_vars(v, acc)
    elif isinstance(node, list):
        for v in node:
            find_vars(v, acc)


def is_bind_mount(vol):
    """True if a service `volumes:` entry is a host bind mount (blocked)."""
    if isinstance(vol, str):
        src = vol.split(":", 1)[0]
        return src.startswith(("/", "./", "../", "~"))
    if isinstance(vol, dict):
        return vol.get("type") == "bind"
    return False


def check_compose(compose, r):
    if not isinstance(compose, dict):
        r.fail("compose.services", "docker-compose.yml is not a mapping")
        return
    services = compose.get("services")
    if not isinstance(services, dict) or not services:
        r.fail("compose.services", "top-level `services:` is missing or empty")
        return
    r.ok("compose.services", f"{len(services)} service(s) declared")

    # image / build
    img_ok = True
    for name, svc in services.items():
        svc = svc or {}
        if "build" in svc:
            r.fail("compose.image", f"service `{name}` uses `build:` (not supported — use a pushed image)")
            img_ok = False
        if not svc.get("image"):
            r.fail("compose.image", f"service `{name}` has no `image:`")
            img_ok = False
    if img_ok:
        r.ok("compose.image", "every service references a published image; no `build:`")

    # blocked service-level fields
    blocked = []
    for name, svc in services.items():
        svc = svc or {}
        if svc.get("privileged"):
            blocked.append(f"{name}: privileged")
        nm = str(svc.get("network_mode", ""))
        if nm == "host" or nm.startswith("container:"):
            blocked.append(f"{name}: network_mode={nm}")
        if str(svc.get("userns_mode", "")) == "host":
            blocked.append(f"{name}: userns_mode=host")
        for k in HOST_NAMESPACE_KEYS:
            if str(svc.get(k, "")) == "host":
                blocked.append(f"{name}: {k}=host")
        if svc.get("devices"):
            blocked.append(f"{name}: devices")
        for vol in svc.get("volumes", []) or []:
            if is_bind_mount(vol):
                blocked.append(f"{name}: bind mount {vol!r}")

    # blocked top-level constructs
    if "include" in compose:
        blocked.append("top-level include")
    for vname, vdef in (compose.get("volumes") or {}).items():
        opts = (vdef or {}).get("driver_opts", {}) if isinstance(vdef, dict) else {}
        if str(opts.get("type", "")) == "none" or str(opts.get("o", "")).find("bind") >= 0:
            blocked.append(f"bind-backed volume `{vname}`")
    for nname, ndef in (compose.get("networks") or {}).items():
        if isinstance(ndef, dict) and str(ndef.get("driver", "")) == "host":
            blocked.append(f"host-driver network `{nname}`")
    for section in ("secrets", "configs"):
        for sname, sdef in (compose.get(section) or {}).items():
            if isinstance(sdef, dict) and "file" in sdef:
                blocked.append(f"file-backed {section[:-1]} `{sname}`")

    if blocked:
        r.fail("compose.blocked", "blocked construct(s): " + "; ".join(blocked))
    else:
        r.ok("compose.blocked", "no blocked compose constructs")

    # published ports required
    if any((svc or {}).get("ports") for svc in services.values()):
        r.ok("compose.ports", "at least one service publishes a port")
    else:
        r.fail("compose.ports", "no published port found (a UI service must publish one)")


def collect_declared(config):
    """Declared .env keys = field names + fixed_values names. (set: keys do NOT count.)"""
    declared, set_keys = set(), set()
    if not isinstance(config, dict):
        return declared, set_keys
    for fv in config.get("fixed_values", []) or []:
        if isinstance(fv, dict) and fv.get("name"):
            declared.add(fv["name"])
    for f in config.get("fields", []) or []:
        if isinstance(f, dict) and f.get("name"):
            declared.add(f["name"])
        for opt in (f.get("options", []) or []) if isinstance(f, dict) else []:
            if isinstance(opt, dict):
                for k in (opt.get("set", {}) or {}).keys():
                    set_keys.add(k)
    return declared, set_keys


def check_config(config, r):
    if not isinstance(config, dict):
        r.fail("config.schema", "config_options.yml is not a mapping")
        return
    fields = config.get("fields")
    if not isinstance(fields, list) or not fields:
        r.fail("config.schema", "missing a non-empty `fields:` list")
        return
    r.ok("config.schema", f"{len(fields)} field(s); top-level shape looks right")

    # field types + unsupported keys
    fields_ok = True
    for f in fields:
        if not isinstance(f, dict):
            r.fail("config.fields", "a field entry is not a mapping")
            fields_ok = False
            continue
        t = f.get("type")
        if t not in FIELD_TYPES:
            r.fail("config.fields", f"field `{f.get('name')}` has unsupported type `{t}`")
            fields_ok = False
        bad = UNSUPPORTED_FIELD_KEYS & set(f.keys())
        if bad:
            r.fail("config.fields", f"field `{f.get('name')}` uses unsupported key(s): {', '.join(sorted(bad))}")
            fields_ok = False
    if fields_ok:
        r.ok("config.fields", "all field types supported; no unsupported keys")

    # detect values
    detect_ok = True
    for fv in config.get("fixed_values", []) or []:
        if isinstance(fv, dict) and "detect" in fv and fv["detect"] not in DETECT_VALUES:
            r.fail("config.detect", f"fixed_value `{fv.get('name')}` has unknown detect `{fv['detect']}`")
            detect_ok = False
    if detect_ok:
        r.ok("config.detect", "fixed_values detect values are valid")


def check_package(pkg):
    print(f"\n== {pkg}")
    r = Report()
    cpath, gpath = os.path.join(pkg, COMPOSE), os.path.join(pkg, CONFIG)

    missing = [n for n, p in ((COMPOSE, cpath), (CONFIG, gpath)) if not os.path.isfile(p)]
    if missing:
        r.fail("files.present", f"missing file(s): {', '.join(missing)}")
        return r
    try:
        compose = load_yaml(cpath) or {}
        config = load_yaml(gpath) or {}
    except yaml.YAMLError as e:
        r.fail("files.present", f"YAML parse error: {e}")
        return r
    r.ok("files.present", "both files exist and parse")

    check_compose(compose, r)
    check_config(config, r)

    # env declared (backend ignores select set: keys, so we do too)
    used = set()
    find_vars(compose, used)
    declared, set_keys = collect_declared(config)
    undeclared = sorted(v for v in used if v not in declared)
    if undeclared:
        hint = ""
        if set(undeclared) & set_keys:
            hint = " (some are only in a select `set:` — declare them as a hidden field too)"
        r.fail("env.declared", f"${{VAR}} used in compose but not declared in {CONFIG}: {', '.join(undeclared)}{hint}")
    else:
        r.ok("env.declared", "every ${VAR} in the compose is declared")
    return r


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    args = sys.argv[1:]
    if args:
        pkgs = args
    else:
        ex = os.path.join(root, "examples")
        pkgs = sorted(os.path.join(ex, d) for d in os.listdir(ex)
                      if os.path.isdir(os.path.join(ex, d)))

    print("SoloHost pre-flight check (non-authoritative — see SOLOHOST.md)")
    total = 0
    for pkg in pkgs:
        total += check_package(pkg).fails
    print(f"\nSummary: {total} FAIL across {len(pkgs)} package(s).")
    if total:
        print("Result: FAIL — fix the items above, then submit to SoloHost for the real check.")
        sys.exit(1)
    print("Result: OK (pre-flight only) — submit to SoloHost for the authoritative check.")
    sys.exit(0)


if __name__ == "__main__":
    main()
