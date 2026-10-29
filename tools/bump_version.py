#!/usr/bin/env python3
"""Bump the skill version and cut a Keep a Changelog entry.

Usage: tools/bump_version.py {patch,minor,major} [--summary FILE] [--date YYYY-MM-DD]

  --summary FILE  the JSON printed by tools/update_pins.py. Its pin changes become
                  bullets under "### Changed" in the new entry.

Updates, in place:
  skills/ola-scooter-dev/upstream.json   "skill_version"
  README.md                              the <!-- skill-version --> marker
  CHANGELOG.md                           "## [Unreleased]" becomes "## [X.Y.Z] - DATE",
                                         and a fresh empty "## [Unreleased]" goes above it.
Prints the new version on stdout. Standard library only.
"""
import argparse
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PIN_FILE = ROOT / "skills" / "ola-scooter-dev" / "upstream.json"
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
PIN_VERSION = re.compile(r'("skill_version":\s*")([^"]+)(")')
README_MARK = re.compile(r"(<!-- skill-version -->)[^<]*(<!-- /skill-version -->)")


def fail(msg: str) -> None:
    raise SystemExit(f"error: {msg}")


def bumped(version: str, level: str) -> str:
    m = VERSION.match(version)
    if not m:
        fail(f"skill_version {version!r} is not X.Y.Z")
    major, minor, patch = (int(x) for x in m.groups())
    if level == "major":
        return f"{major + 1}.0.0"
    if level == "minor":
        return f"{major}.{minor + 1}.0"
    return f"{major}.{minor}.{patch + 1}"


def pin_bullets(summary: dict) -> list[str]:
    bullets = []
    if summary["sdk"]["old"] != summary["sdk"]["new"]:
        bullets.append(f"- Dash SDK pin `{(summary['sdk']['old'] or 'none')[:7]}` -> `{summary['sdk']['new'][:7]}`.")
    if summary["can"]["old"] != summary["can"]["new"]:
        bullets.append(f"- CAN reference pin `{(summary['can']['old'] or 'none')[:7]}` -> `{summary['can']['new'][:7]}`.")
    if summary["contract"]["old"] != summary["contract"]["new"]:
        bullets.append(f"- Theme contract v{summary['contract']['old']} -> v{summary['contract']['new']}.")
    if summary["plugin_api"]["old"] != summary["plugin_api"]["new"]:
        bullets.append(f"- Plugin API v{summary['plugin_api']['old']} -> v{summary['plugin_api']['new']}.")
    return bullets


def section_end(lines: list[str], start: int) -> int:
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## ["):
            return i
    return len(lines)


def edit_changelog(text: str, version: str, date: str, bullets: list[str]) -> str:
    lines = text.split("\n")
    unreleased = next((i for i, line in enumerate(lines) if line.strip() == "## [Unreleased]"), None)
    if unreleased is None:
        # No pending section: insert a fresh one above the newest release.
        first = next((i for i, line in enumerate(lines) if line.startswith("## [")), len(lines))
        block = [f"## [{version}] - {date}", "", "### Changed", "", *bullets, ""] if bullets else [f"## [{version}] - {date}", ""]
        lines[first:first] = block
        return "\n".join(lines)

    end = section_end(lines, unreleased)
    lines[unreleased] = f"## [{version}] - {date}"
    lines[unreleased:unreleased] = ["## [Unreleased]", ""]
    end += 2
    if bullets:
        section = lines[unreleased + 2:end]
        heading = next((i for i, line in enumerate(section) if line.strip() == "### Changed"), None)
        if heading is not None:
            at = unreleased + 2 + heading + 1
            # skip the blank line after the heading, then add the bullets
            if at < len(lines) and lines[at].strip() == "":
                at += 1
            lines[at:at] = bullets
        else:
            last = end
            while last > unreleased and lines[last - 1].strip() == "":
                last -= 1
            lines[last:last] = ["", "### Changed", "", *bullets]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("level", choices=["patch", "minor", "major"])
    ap.add_argument("--summary", type=Path, help="JSON from tools/update_pins.py")
    ap.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d"))
    args = ap.parse_args()

    pin_text = PIN_FILE.read_text(encoding="utf-8")
    m = PIN_VERSION.search(pin_text)
    if not m:
        fail("skill_version not found in upstream.json")
    new = bumped(m.group(2), args.level)
    PIN_FILE.write_text(PIN_VERSION.sub(lambda x: x.group(1) + new + x.group(3), pin_text, count=1), encoding="utf-8")

    readme = README.read_text(encoding="utf-8")
    if not README_MARK.search(readme):
        fail("README.md has no <!-- skill-version --> marker")
    README.write_text(README_MARK.sub(lambda x: x.group(1) + new + x.group(2), readme, count=1), encoding="utf-8")

    bullets = pin_bullets(json.loads(args.summary.read_text(encoding="utf-8"))) if args.summary else []
    CHANGELOG.write_text(edit_changelog(CHANGELOG.read_text(encoding="utf-8"), new, args.date, bullets), encoding="utf-8")

    print(new)
    print(f"bumped {m.group(2)} -> {new}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
