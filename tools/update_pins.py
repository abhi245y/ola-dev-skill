#!/usr/bin/env python3
"""Move the upstream pins in upstream.json to the checkouts' current HEAD.

Reads from each checkout:
  ola-dash-sdk       HEAD sha; contract-version from contract/vehicle.slint;
                     plugin API version from the "plugin API v<N>" header of
                     sdk/plugin-api/aidl/dev/olatool/dash/plugin/IDashHost.aidl.
                     If host/java/.../PluginHost.java declares API_VERSION, it must agree.
  ola-can-reference  HEAD sha; profile of the pinned catalog file; the set of
                     profiles of every catalog/**/*.json (catalog_profiles).

Writes skills/ola-scooter-dev/upstream.json only when a pin changed (pinned_on is set
to today, UTC). Prints one JSON object on stdout:
  {"changed", "breaking", "sdk", "can", "contract", "plugin_api", "catalog_profiles"}
breaking = contract-version or plugin API version changed, or the catalog profile set changed.

Usage: tools/update_pins.py [--sdk DIR] [--can DIR]
DIR defaults to $OLA_SDK_DIR / $OLA_CAN_DIR, else the fetch-upstream cache.
Idempotent. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN_FILE = ROOT / "skills" / "ola-scooter-dev" / "upstream.json"
CACHE = Path(os.environ.get("OLA_UPSTREAM_DIR", Path.home() / ".cache" / "ola-scooter-dev" / "upstream"))

CONTRACT_FILE = "contract/vehicle.slint"
CONTRACT_VERSION = re.compile(r"out property <int> contract-version:\s*(\d+)")
PLUGIN_AIDL = "sdk/plugin-api/aidl/dev/olatool/dash/plugin/IDashHost.aidl"
PLUGIN_API = re.compile(r"plugin API v(\d+)\b")
HOST_JAVA = "host/java/dev/olatool/dash/plugin/PluginHost.java"
HOST_API = re.compile(r"static final int API_VERSION = (\d+);")


def fail(msg: str) -> None:
    raise SystemExit(f"error: {msg}")


def head_sha(path: Path) -> str:
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        fail(f"{path} is not a git checkout")
    return out.stdout.strip()


def search_file(path: Path, pattern: re.Pattern, what: str) -> int:
    if not path.is_file():
        fail(f"{what}: {path} not found")
    m = pattern.search(path.read_text(encoding="utf-8"))
    if not m:
        fail(f"{what}: pattern not found in {path}")
    return int(m.group(1))


def sdk_facts(sdk: Path) -> dict:
    commit = head_sha(sdk)
    contract =search_file(sdk / CONTRACT_FILE, CONTRACT_VERSION, "contract-version")
    plugin_api = search_file(sdk / PLUGIN_AIDL, PLUGIN_API, "plugin API version")
    host_java = sdk / HOST_JAVA
    if host_java.is_file():  # the host must report the same API version it documents
        host_api = search_file(host_java, HOST_API, "host API_VERSION")
        if host_api != plugin_api:
            fail(f"plugin API v{plugin_api} in IDashHost.aidl but host API_VERSION is {host_api}")
    return {"commit": commit, "contract_version": contract, "plugin_api_version": plugin_api}


def can_facts(can: Path, pinned_catalog: str) -> dict:
    commit = head_sha(can)
    catalog = can / pinned_catalog
    if not catalog.is_file():
        fail(f"pinned catalog {pinned_catalog} not found in {can}")
    profiles = set()
    for path in sorted((can / "catalog").glob("**/*.json")):
        profile = json.loads(path.read_text(encoding="utf-8")).get("profile")
        if not profile:
            fail(f"{path} has no profile")
        profiles.add(profile)
    return {
        "commit": commit,
        "catalog_profile": json.loads(catalog.read_text(encoding="utf-8"))["profile"],
        "catalog_profiles": sorted(profiles),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sdk", type=Path, default=Path(os.environ.get("OLA_SDK_DIR", CACHE / "ola-dash-sdk")))
    ap.add_argument("--can", type=Path, default=Path(os.environ.get("OLA_CAN_DIR", CACHE / "ola-can-reference")))
    args = ap.parse_args()

    pins = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    old_sdk = pins["upstreams"]["ola-dash-sdk"]
    old_can = pins["upstreams"]["ola-can-reference"]

    sdk = sdk_facts(args.sdk)
    can = can_facts(args.can, old_can["catalog"])

    new_sdk = {**old_sdk, **sdk}
    new_can = {**old_can, **can}
    new_pins = {**pins, "upstreams": {"ola-dash-sdk": new_sdk, "ola-can-reference": new_can}}
    changed = new_pins["upstreams"] != pins["upstreams"]

    old_profiles = set(old_can.get("catalog_profiles") or [old_can["catalog_profile"]])
    breaking = (
        old_sdk.get("contract_version") != new_sdk["contract_version"]
        or old_sdk.get("plugin_api_version") != new_sdk["plugin_api_version"]
        or old_profiles != set(new_can["catalog_profiles"])
    )

    if changed:
        new_pins["pinned_on"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        PIN_FILE.write_text(json.dumps(new_pins, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"updated {PIN_FILE.relative_to(ROOT)}", file=sys.stderr)
    else:
        print("pins already match the checkouts", file=sys.stderr)

    summary = {
        "changed": changed,
        "breaking": breaking,
        "sdk": {"old": old_sdk.get("commit"), "new": new_sdk["commit"]},
        "can": {"old": old_can.get("commit"), "new": new_can["commit"]},
        "contract": {"old": old_sdk.get("contract_version"), "new": new_sdk["contract_version"]},
        "plugin_api": {"old": old_sdk.get("plugin_api_version"), "new": new_sdk["plugin_api_version"]},
        "catalog_profiles": {"old": sorted(old_profiles), "new": new_can["catalog_profiles"]},
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
