#!/usr/bin/env python3
"""Check the skill and the repo: SKILL.md frontmatter, markdown links, JSON files, theme manifest.

Usage: tools/validate_skill.py   (exit 1 on any problem). Standard library only.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
SKIP_DIRS = {".git", "tmp"}
errors: list[str] = []


def md_files():
    for path in ROOT.rglob("*.md"):
        if not SKIP_DIRS.intersection(path.relative_to(ROOT).parts):
            yield path


def check_frontmatter(skill_dir: Path) -> None:
    skill_md = skill_dir / "SKILL.md"
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        errors.append(f"{skill_md}: missing opening frontmatter ---")
        return
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"{skill_md}: missing closing frontmatter ---")
        return
    fields = {}
    for line in lines[1:end]:
        if ":" in line and not line.startswith(" "):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    name = fields.get("name", "")
    desc = fields.get("description", "")
    if not NAME_RE.match(name) or len(name) > 64:
        errors.append(f"{skill_md}: name {name!r} must be lowercase-hyphen, at most 64 characters")
    if name != skill_dir.name:
        errors.append(f"{skill_md}: name {name!r} must equal the folder name {skill_dir.name!r}")
    if not desc:
        errors.append(f"{skill_md}: description is empty")
    elif len(desc) > 1024:
        errors.append(f"{skill_md}: description is {len(desc)} characters, max 1024")
    body_lines = len(lines) - end - 1
    if body_lines >= 400:
        errors.append(f"{skill_md}: body is {body_lines} lines, keep it under about 400")


def check_links() -> None:
    for path in md_files():
        for target in LINK_RE.findall(path.read_text(encoding="utf-8")):
            if re.match(r"^[a-z]+:", target) or target.startswith("#"):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            if not (path.parent / target_path).exists():
                errors.append(f"{path.relative_to(ROOT)}: broken link {target}")


def check_json() -> None:
    for path in ROOT.rglob("*.json"):
        if SKIP_DIRS.intersection(path.relative_to(ROOT).parts):
            continue
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"{path.relative_to(ROOT)}: invalid JSON ({exc})")


def check_theme_template() -> None:
    theme = SKILLS / "ola-scooter-dev" / "templates" / "theme"
    manifest = json.loads((theme / "theme.json").read_text(encoding="utf-8"))
    for key in ("id", "name", "version", "author", "license", "contract", "entry", "description"):
        if key not in manifest:
            errors.append(f"{theme}/theme.json: missing {key}")
    if manifest.get("id") != theme.name and not re.match(r"^[a-z0-9-]+$", str(manifest.get("id", ""))):
        errors.append(f"{theme}/theme.json: bad id")
    if not (theme / manifest.get("entry", "main.slint")).exists():
        errors.append(f"{theme}/theme.json: entry file missing")


def check_version() -> None:
    # One version, three places: upstream.json (source), README marker, CHANGELOG heading.
    version = json.loads((SKILLS / "ola-scooter-dev" / "upstream.json").read_text(encoding="utf-8")).get("skill_version", "")
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        errors.append(f"upstream.json: skill_version {version!r} is not X.Y.Z")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    marker = re.search(r"<!-- skill-version -->([^<]*)<!-- /skill-version -->", readme)
    if not marker or marker.group(1) != version:
        errors.append(f"README.md: skill-version marker must read {version!r}")
    if f"## [{version}]" not in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"):
        errors.append(f"CHANGELOG.md: no entry for {version}")


def main() -> int:
    for skill_dir in sorted(p for p in SKILLS.iterdir() if (p / "SKILL.md").exists()):
        check_frontmatter(skill_dir)
    check_links()
    check_json()
    check_theme_template()
    check_version()
    for line in errors:
        print(line, file=sys.stderr)
    if errors:
        return 1
    print("skill, links, JSON and theme template: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
