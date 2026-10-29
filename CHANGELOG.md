# Changelog

All notable changes are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - unreleased

### Added

- `ola-scooter-dev` skill: `SKILL.md` (orientation, hard rules, decision tree) and references for the platform, Dash SDK, theme contract, themes, plugins, vehicle-parser interface, CAN reference, recipes, safety, and troubleshooting.
- Starter theme template (compiles against contract v5) and a minimal widget plugin template (MIT).
- `scripts/fetch-upstream.sh` to clone the pinned upstream repos.
- `tools/sync.py` to regenerate `contract.md` and the CAN key-IDs table from the pinned upstream, with `--check`.
- `tools/validate_skill.py` to check frontmatter, links, JSON, and the theme manifest.
- Pins: Dash SDK commit `7e3f339` (contract v5, plugin API v1) and CAN reference commit `7b13d08` (profile `gen1-hvdp-5.0.0`).
