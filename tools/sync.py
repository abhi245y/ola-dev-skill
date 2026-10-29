#!/usr/bin/env python3
"""Regenerate skill references from the pinned upstream repos.

Writes:
  skills/ola-scooter-dev/references/contract.md     from contract/vehicle.slint (ola-dash-sdk)
  the GENERATED key-ids block in references/can-bus.md, from the catalog JSON (ola-can-reference)

Usage:
  tools/sync.py [--check] [--sdk DIR] [--can DIR]

DIR defaults to $OLA_SDK_DIR / $OLA_CAN_DIR, else the cache written by
skills/ola-scooter-dev/scripts/fetch-upstream.sh. Every DIR must be a git checkout
at the commit pinned in skills/ola-scooter-dev/upstream.json.

--check regenerates in memory and exits 1 if a generated file is stale.
Standard library only.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ola-scooter-dev"
PIN = json.loads((SKILL / "upstream.json").read_text(encoding="utf-8"))
CONTRACT_OUT = SKILL / "references" / "contract.md"
CAN_OUT = SKILL / "references" / "can-bus.md"
BEGIN = "<!-- BEGIN GENERATED: key-ids -->"
END = "<!-- END GENERATED: key-ids -->"

CACHE = Path(os.environ.get("OLA_UPSTREAM_DIR", Path.home() / ".cache" / "ola-scooter-dev" / "upstream"))

# Hand-written reading of each key ID. Names, directions and signals come from the catalog.
KEY_IDS = [
    ("0x120", "Overall battery state of charge (%)."),
    ("0x140", "Battery current (A). Sign convention to confirm on a real ride."),
    ("0x143", "Vehicle mode. Body not recovered: map only from callbacks and raw captures."),
    ("0x144", "BCM lock state enum. Lock feedback, not a ride-ready signal."),
    ("0x150", "Bus (pack) voltage (V)."),
    ("0x153", "Power-button status. The source name says DCDC_VOLTAGE, but it is not a voltage."),
    ("0x15B", "Requested drive mode (DriveModes enum)."),
    ("0x160", "Effective, minimum and maximum battery temperature (degC)."),
    ("0x223", "Motor current, torque and trip raw values. Units unresolved: do not label."),
    ("0x224", "Vehicle direction raw bit. Meaning of each value not established."),
    ("0x313", "Vehicle speed (km/h, scale 0.1), MCU and motor temperature, motor RPM."),
    ("0x352", "Displayed state of charge (%), integer."),
    ("0x354", "Displayed speed (km/h), integer. The value the stock dash shows."),
    ("0x356", "Odometer in metres (32-bit). Cumulative, not a trip meter."),
    ("0x61D", "IMU X axis, raw integer minus 2000. Units unknown."),
    ("0x64D", "IMU Z axis, raw integer minus 2000. Units unknown."),
    ("0x683", "Vehicle safety state: fall, tow/theft, regen availability, hill hold, tamper wakeup."),
    ("0x68B", "Custom-mode range (km)."),
    ("0x6AE", "Passcode window active flag."),
    ("0x6C0", "HMI command acknowledgement (received)."),
    ("0x6D0", "Vehicle command byte (received). Vocabulary in the enum tables."),
    ("0x6F4", "Range per mode: eco, sport, normal, hyper (km)."),
    ("0x643", "TRANSMIT. Touch-activity report from the head unit. Never transmit (safety.md)."),
    ("0x6BC", "TRANSMIT. HMI command. Never transmit (safety.md)."),
]

UNIT_SUFFIXES = [("-kmh", "km/h"), ("-km", "km"), ("-pct", "%"), ("-c", "°C"), ("-a", "A"), ("-v", "V")]


def git_head(path: Path) -> str:
    out = subprocess.run(["git", "-C", str(path), "rev-parse", "HEAD"],
                         capture_output=True, text=True, check=False)
    if out.returncode != 0:
        raise SystemExit(f"error: {path} is not a git checkout")
    return out.stdout.strip()


def check_pin(path: Path, pinned: str, label: str) -> None:
    head = git_head(path)
    if head != pinned:
        raise SystemExit(f"error: {label} at {path} is {head}, pinned {pinned}. Run scripts/fetch-upstream.sh.")


# ---------- contract ----------

PROP = re.compile(r"^\s*(in|out)?\s*property\s*<([^>]+)>\s*([\w-]+)\s*(?::\s*([^;]+))?;")
CALLBACK = re.compile(r"^\s*callback\s+([\w-]+)\s*(\(([^)]*)\))?\s*;")
ENUM = re.compile(r"^export enum (\w+)\s*\{([^}]*)\}")
GLOBAL = re.compile(r"^export global (\w+)\s*\{")
STRUCT = re.compile(r"^export struct (\w+)\s*\{")
VERSION = re.compile(r"out property <int> contract-version:\s*(\d+)")


def unit_for(name: str) -> str:
    for suffix, unit in UNIT_SUFFIXES:
        if name.endswith(suffix):
            return unit
    return ""


def parse_contract(text: str) -> dict:
    lines = text.splitlines()
    header = []
    for line in lines:
        if line.startswith("//"):
            header.append(line[2:].strip())
        elif line.strip():
            break
    version = VERSION.search(text)
    if not version:
        raise SystemExit("error: contract-version not found in contract/vehicle.slint")

    enums, globals_, structs = [], [], []
    pending: list[str] = []
    current = None  # (kind, name, rows)
    for line in lines:
        stripped = line.strip()
        if current is not None and line.startswith("}"):
            (globals_ if current[0] == "global" else structs).append((current[1], current[2]))
            current = None
            pending = []
            continue
        if not stripped:
            pending = []
            continue
        if stripped.startswith("//"):
            pending.append(stripped[2:].strip())
            continue
        m = ENUM.match(stripped)
        if m and current is None:
            values = [v.strip() for v in m.group(2).split(",") if v.strip()]
            enums.append((m.group(1), values, " ".join(pending)))
            pending = []
            continue
        m = GLOBAL.match(stripped)
        if m and current is None:
            current = ("global", m.group(1), [])
            pending = []
            continue
        m = STRUCT.match(stripped)
        if m and current is None:
            current = ("struct", m.group(1), [])
            pending = []
            continue
        if current is not None:
            note = " ".join(pending)
            pending = []
            p = PROP.match(line)
            if p:
                direction = p.group(1) or "in"
                if current[0] == "struct":
                    continue
                current[2].append({
                    "kind": "property", "direction": direction, "type": p.group(2).strip(),
                    "name": p.group(3), "default": (p.group(4) or "").strip(), "note": note,
                })
                continue
            c = CALLBACK.match(line)
            if c:
                current[2].append({
                    "kind": "callback", "direction": "callback", "type": f"({c.group(3) or ''})",
                    "name": c.group(1), "default": "", "note": note,
                })
                continue
            # struct field: `id: string,`
            f = re.match(r"^\s*([\w-]+)\s*:\s*([\w\[\]]+),?\s*$", line)
            if f and current[0] == "struct":
                current[2].append({"kind": "field", "direction": "", "type": f.group(2),
                                   "name": f.group(1), "default": "", "note": note})
        else:
            pending = []
    return {"version": version.group(1), "header": header, "enums": enums,
            "globals": globals_, "structs": structs}


def render_contract(data: dict, sha: str) -> str:
    out = [
        "# Theme contract reference",
        "",
        "<!-- GENERATED by tools/sync.py from contract/vehicle.slint. Do not edit by hand. -->",
        f"<!-- Source: ola-dash-sdk at {sha}. contract-version {data['version']}. -->",
        "",
        f"The contract is `contract-version: {data['version']}`. Themes read `in` properties and invoke the callbacks listed here. The host writes `in` properties. Themes must never assign to them.",
        "",
        "Units come from name suffixes: `-kmh` km/h, `-km` km, `-pct` %, `-c` degC, `-a` A, `-v` V. `-1` means not reported yet. Show `--`.",
        "",
        "## Header comment of the contract file",
        "",
    ]
    out += [f"> {h}" if h else ">" for h in data["header"]]
    out += ["", "## Enums", ""]
    for name, values, note in data["enums"]:
        out.append(f"### `{name}`")
        out.append("")
        if note:
            out.append(note)
            out.append("")
        out.append(", ".join(f"`{v}`" for v in values))
        out.append("")
    for name, rows in data["globals"]:
        out += [f"## `{name}` global", "", "| Member | Direction | Type | Default | Unit | Notes |",
                "|---|---|---|---|---|---|"]
        for r in rows:
            if r["kind"] == "property":
                unit = unit_for(r["name"])
                default = f"`{r['default']}`" if r["default"] else "type default"
                out.append(f"| `{r['name']}` | {r['direction']} | `{r['type']}` | {default} | {unit} | {r['note']} |")
            else:
                out.append(f"| `{r['name']}{r['type']}` | callback | | | | {r['note']} |")
        out.append("")
    for name, rows in data["structs"]:
        out += [f"## `struct {name}`", "", "| Field | Type | Notes |", "|---|---|---|"]
        out += [f"| `{r['name']}` | `{r['type']}` | {r['note']} |" for r in rows]
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------- CAN key IDs ----------

def render_key_ids(catalog: dict) -> str:
    by_id = {f["id"].upper(): f for f in catalog["frames"]}
    rows = ["| ID | Dec | Names | Direction | Curated signals (unit) | Meaning |",
            "|---|---|---|---|---|---|"]
    for hex_id, meaning in KEY_IDS:
        frame = by_id.get(hex_id.upper())
        if frame is None:
            raise SystemExit(f"error: {hex_id} is not in the catalog")
        names = ", ".join(frame["names"])
        direction = ", ".join(frame["directions"])
        sigs = "; ".join(f"`{s['name']}` ({s.get('unit') or 'unit unknown'})" for s in frame.get("signals", []))
        rows.append(f"| `{frame['id']}` | {frame['decimal_id']} | {names} | {direction} | {sigs or 'none curated'} | {meaning} |")
    return "\n".join(rows)


def replace_block(text: str, body: str) -> str:
    if BEGIN not in text or END not in text:
        raise SystemExit(f"error: markers missing in {CAN_OUT}")
    head, rest = text.split(BEGIN, 1)
    _, tail = rest.split(END, 1)
    return f"{head}{BEGIN}\n<!-- Generated from the pinned catalog by tools/sync.py. Do not edit by hand. -->\n\n{body}\n{END}{tail}"


# ---------- main ----------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="fail if generated files are stale")
    ap.add_argument("--sdk", type=Path, default=Path(os.environ.get("OLA_SDK_DIR", CACHE / "ola-dash-sdk")))
    ap.add_argument("--can", type=Path, default=Path(os.environ.get("OLA_CAN_DIR", CACHE / "ola-can-reference")))
    args = ap.parse_args()

    sdk_pin = PIN["upstreams"]["ola-dash-sdk"]
    can_pin = PIN["upstreams"]["ola-can-reference"]
    check_pin(args.sdk, sdk_pin["commit"], "ola-dash-sdk")
    check_pin(args.can, can_pin["commit"], "ola-can-reference")

    contract_text = (args.sdk / "contract" / "vehicle.slint").read_text(encoding="utf-8")
    data = parse_contract(contract_text)
    if int(data["version"]) != sdk_pin["contract_version"]:
        raise SystemExit(f"error: contract-version {data['version']} != pinned {sdk_pin['contract_version']}")
    contract_out = render_contract(data, sdk_pin["commit"])

    catalog_path = args.can / can_pin["catalog"]
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    if catalog.get("profile") != can_pin["catalog_profile"]:
        raise SystemExit(f"error: catalog profile {catalog.get('profile')} != pinned {can_pin['catalog_profile']}")
    can_out = replace_block(CAN_OUT.read_text(encoding="utf-8"), render_key_ids(catalog))

    stale = []
    for path, text in ((CONTRACT_OUT, contract_out), (CAN_OUT, can_out)):
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != text:
            stale.append(path)
            if not args.check:
                path.write_text(text, encoding="utf-8")
    if args.check:
        if stale:
            for p in stale:
                print(f"stale: {p.relative_to(ROOT)} (run tools/sync.py)", file=sys.stderr)
            return 1
        print("generated references are up to date")
    else:
        print("wrote " + ", ".join(str(p.relative_to(ROOT)) for p in stale) if stale else "nothing to change")
    return 0


if __name__ == "__main__":
    sys.exit(main())
