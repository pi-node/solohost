#!/usr/bin/env python3
"""
AUTHORITATIVE validation for a SoloHost package, via the hosted SoloHost API.

This is the REAL check and the required gate before a package ships: it calls the
same validator SoloHost runs at submit, so `Result: OK` here means the package will
be accepted. The agent runs this automatically before handing a package off; a human
can also run it, but does not have to.

Endpoint (public, no token):
  POST {HOST}/api/apps/validate   {composeYaml, configOptionsYaml}  -> {ok, errors?}
Override the host with the SOLOHOST_API env var if it moves.

Usage:
  python3 scripts/validate_api.py <package-dir> [<package-dir> ...]
  python3 scripts/validate_api.py                # defaults to every dir under examples/

Each package dir must contain docker-compose.yml and config_options.yml.
Exit codes: 0 all OK | 1 a package failed validation | 2 usage/IO error |
            3 could not reach the API (after retries).
Needs only the Python 3 standard library.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

HOST = os.environ.get(
    "SOLOHOST_API",
    "https://solohost-nohcqud24xwnsmna.staging.piappengine.com",
).rstrip("/")
VALIDATE_URL = HOST + "/api/apps/validate"

# The API can 502 for a few seconds on a cold start; retry so a transient blip
# never blocks a ship. These are transport/5xx retries, not validation retries.
RETRIES = 4
BACKOFF_SECONDS = 8


def _post(url, payload):
    """POST JSON, retrying on 5xx / transport errors. Returns a parsed dict."""
    data = json.dumps(payload).encode("utf-8")
    last_err = None
    for attempt in range(1, RETRIES + 1):
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code >= 500 and attempt < RETRIES:
                last_err = "HTTP %s" % e.code
                time.sleep(BACKOFF_SECONDS)
                continue
            # A non-5xx HTTP error may still carry a JSON validation body.
            try:
                return json.loads(body)
            except ValueError:
                raise RuntimeError("HTTP %s from API: %s" % (e.code, body[:200]))
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = str(getattr(e, "reason", e))
            if attempt < RETRIES:
                time.sleep(BACKOFF_SECONDS)
                continue
            raise RuntimeError("could not reach API (%s)" % last_err)
    raise RuntimeError("API kept returning errors (%s)" % last_err)


def _read(pkg_dir):
    compose = os.path.join(pkg_dir, "docker-compose.yml")
    config = os.path.join(pkg_dir, "config_options.yml")
    for f in (compose, config):
        if not os.path.isfile(f):
            raise FileNotFoundError("missing %s" % f)
    with open(compose, encoding="utf-8") as fh:
        compose_txt = fh.read()
    with open(config, encoding="utf-8") as fh:
        config_txt = fh.read()
    return compose_txt, config_txt


def validate(pkg_dir):
    compose_txt, config_txt = _read(pkg_dir)
    return _post(VALIDATE_URL, {"composeYaml": compose_txt, "configOptionsYaml": config_txt})


def main(argv):
    dirs = argv[1:]
    if not dirs:
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ex = os.path.join(here, "examples")
        dirs = sorted(
            os.path.join(ex, d) for d in os.listdir(ex)
            if os.path.isdir(os.path.join(ex, d))
        ) if os.path.isdir(ex) else []
        if not dirs:
            print("usage: validate_api.py <package-dir> [...]", file=sys.stderr)
            return 2

    print("SoloHost validation (authoritative) via %s\n" % VALIDATE_URL)
    any_fail = False
    for d in dirs:
        try:
            result = validate(d)
        except FileNotFoundError as e:
            print("  [ERROR] %s: %s" % (d, e), file=sys.stderr)
            return 2
        except RuntimeError as e:
            print("  [UNREACHABLE] %s: %s" % (d, e), file=sys.stderr)
            return 3
        if result.get("ok"):
            print("  [OK]   %s" % d)
        else:
            any_fail = True
            print("  [FAIL] %s" % d)
            for err in result.get("errors", []) or []:
                rule = err.get("rule") or err.get("code") or ""
                msg = err.get("message") or json.dumps(err)
                print("           - %s  (%s)" % (msg, rule))
            if not result.get("errors"):
                print("           - %s" % json.dumps(result)[:300])

    print()
    if any_fail:
        print("Result: FAIL — fix the errors above, then re-run. Not ready to ship.")
        return 1
    print("Result: OK — passes the authoritative validator; ready to paste into SoloHost.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
