#!/usr/bin/env python3
"""Build the release zip and SHA256SUMS for the skill.

Usage: tools/package.py [--out DIR] [--notes-out FILE]

  DIR/ola-scooter-dev-<version>.zip   the folder skills/ola-scooter-dev as ola-scooter-dev/
                                      (SKILL.md at ola-scooter-dev/SKILL.md)
  DIR/SHA256SUMS                      sha256sum format, one line for the zip
  --notes-out FILE                    the CHANGELOG section for this version, for release notes

DIR defaults to dist/ at the repo root. The zip is deterministic: sorted entries, fixed
timestamps, fixed modes and create_system. Standard library only.
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "skills" / "ola-scooter-dev"
PIN_FILE = SKILL / "upstream.json"
CHANGELOG = ROOT / "CHANGELOG.md"
FIXED_TIME = (1980, 1, 1, 0, 0, 0)
SKIP_PARTS = {"__pycache__", ".DS_Store"}


def fail(msg: str) -> None:
    raise SystemExit(f"error: {msg}")


def skill_files() -> list[tuple[str, Path]]:
    if not (SKILL / "SKILL.md").is_file():
        fail(f"{SKILL / 'SKILL.md'} missing")
    entries = []
    for path in SKILL.rglob("*"):
        rel = path.relative_to(SKILL)
        if path.is_dir() or path.suffix == ".pyc" or SKIP_PARTS.intersection(rel.parts):
            continue
        entries.append((f"ola-scooter-dev/{rel.as_posix()}", path))
    return sorted(entries)


def write_zip(dest: Path, entries: list[tuple[str, Path]]) -> None:
    with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for arcname, path in entries:
            info = zipfile.ZipInfo(arcname, date_time=FIXED_TIME)
            info.create_system = 3  # unix, so the output does not depend on the build OS
            mode = 0o755 if path.stat().st_mode & 0o111 else 0o644
            info.external_attr = (0o100000 | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, path.read_bytes())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def changelog_section(version: str) -> str | None:
    lines = CHANGELOG.read_text(encoding="utf-8").split("\n")
    start = next((i for i, line in enumerate(lines) if line.startswith(f"## [{version}]")), None)
    if start is None:
        return None
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## [")), len(lines))
    return "\n".join(lines[start + 1:end]).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=ROOT / "dist")
    ap.add_argument("--notes-out", type=Path)
    args = ap.parse_args()

    version = json.loads(PIN_FILE.read_text(encoding="utf-8"))["skill_version"]
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    zip_path = out / f"ola-scooter-dev-{version}.zip"
    write_zip(zip_path, skill_files())
    (out / "SHA256SUMS").write_text(f"{sha256(zip_path)}  {zip_path.name}\n", encoding="utf-8")

    if args.notes_out:
        section = changelog_section(version)
        if section is None:
            print(f"warning: no CHANGELOG section for {version}", file=sys.stderr)
            section = f"See CHANGELOG.md for version {version}.\n"
        args.notes_out.write_text(section, encoding="utf-8")

    print(zip_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
