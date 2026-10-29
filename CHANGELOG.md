# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-10-30

### Added

- Release pipeline. `.github/workflows/upstream-sync.yml` runs every 6 hours and on `sdk-updated` / `can-updated` dispatches. It moves the pins, regenerates and checks the references, validates, then either releases a patch version or, for a breaking upstream change, opens a `needs-review` PR.
- `.github/workflows/release.yml` releases a manually pushed `v*` tag.
- `tools/update_pins.py` (pins from the upstream HEADs, with a JSON summary), `tools/bump_version.py` (SemVer bump plus a CHANGELOG entry), and `tools/package.py` (deterministic release zip and `SHA256SUMS`).
- `install.sh` installs a release for Claude Code, Codex, Gemini CLI, Cursor, or AGENTS.md. It verifies the checksum, backs up what it replaces, and supports `--project`, `--version`, `--uninstall`, and `--from-file`.
- `upstream-notifier/`: template workflow for the upstream repos that sends the dispatch to this repo.
- `skill_version` in `upstream.json`, shown in the README.

### Changed

- `upstream.json` records `catalog_profiles`, the profile set that decides whether an upstream change is breaking.
- `tools/validate_skill.py` checks that the version matches in `upstream.json`, the README, and this file.

### Skill

- `ola-scooter-dev` skill: `SKILL.md` (orientation, hard rules, decision tree) and references for the platform, Dash SDK, theme contract, themes, plugins, vehicle-parser interface, CAN reference, recipes, safety, and troubleshooting.
- Starter theme template (compiles against contract v5) and a minimal widget plugin template (MIT).
- `scripts/fetch-upstream.sh` to clone the pinned upstream repos.
- `tools/sync.py` to regenerate `contract.md` and the CAN key-IDs table from the pinned upstream, with `--check`.
- `tools/validate_skill.py` to check frontmatter, links, JSON, and the theme manifest.
- Pins: Dash SDK commit `7e3f339` (contract v5, plugin API v1) and CAN reference commit `7b13d08` (profile `gen1-hvdp-5.0.0`).
