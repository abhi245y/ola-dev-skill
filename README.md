# Ola Dev Skill

An [Agent Skill](https://agentskills.io) that teaches an AI coding agent to build apps, themes, widget plugins, and read-only analysis tools for the **Ola S1 Pro Gen 1** electric scooter dash. It works with Claude Code, OpenAI Codex, Gemini CLI, Cursor, and any agent that can read a folder of instructions.

It packages what two public projects have learned:

- [Ola Dash SDK](https://github.com/abhi245y/ola-dash-sdk) (GPL-3.0-or-later): a Slint dash platform with runtime themes, plugin API v1, a theme contract, and a clean-room vehicle-parser interface.
- [Ola CAN Reference](https://github.com/abhi245y/ola-can-reference) (MIT): a catalog of CAN IDs, signals, and enums for Gen 1 firmware HVDP 5.0.0.

## What an agent can build with it

- **Themes** for the dash: layout, colour, fonts, and motion, rendered in a desktop preview before anything touches a scooter.
- **Widget plugins** that show a value card on the dash.
- **Navigation and media plugins** that feed turn-by-turn or now-playing data.
- **Ride-log and CAN analysis tools** that read captures and explain them, with confidence labels.
- **Contract extensions**, following the SDK's additive rules.

Everything is display-only. The skill refuses code that starts, moves, unlocks, or controls a vehicle, transmits CAN frames by default, or touches updates. See `skills/ola-scooter-dev/references/safety.md`.

## Install

The skill is one folder: `skills/ola-scooter-dev/`. Copy it, or link it, into your agent's skills location.

**Claude Code**

```sh
# for all projects
mkdir -p ~/.claude/skills && cp -r skills/ola-scooter-dev ~/.claude/skills/
# or for one project
mkdir -p .claude/skills && cp -r skills/ola-scooter-dev .claude/skills/
```

**OpenAI Codex**

```sh
mkdir -p ~/.codex/skills && cp -r skills/ola-scooter-dev ~/.codex/skills/
```

Or add a pointer to your project's `AGENTS.md`: "For Ola scooter work, read `skills/ola-scooter-dev/SKILL.md` first."

**Gemini CLI and other agents**

Copy the folder anywhere the agent can read, then point the agent at `SKILL.md`. For Gemini CLI, add a line to `GEMINI.md` that says the same. Check your agent's documentation for its current skills path, since these change.

## Fetch the upstream sources

The skill points at the upstream repos at pinned commits. Fetch them once:

```sh
skills/ola-scooter-dev/scripts/fetch-upstream.sh          # pinned commits (default)
skills/ola-scooter-dev/scripts/fetch-upstream.sh --latest # newest, not pinned
```

They land in `~/.cache/ola-scooter-dev/upstream` unless you pass `--dir`.

## Pinned upstream versions

| Upstream | Commit | Licence | Version |
|---|---|---|---|
| Ola Dash SDK | `7e3f339b2cde5ccc7adbb3061edf5e0924991e10` | GPL-3.0-or-later | 0.1 experimental, contract v5, plugin API v1 |
| Ola CAN Reference | `7b13d086380cb7bb17be670642e26dd6853ee7ea` | MIT | profile `gen1-hvdp-5.0.0` |

The pins live in `skills/ola-scooter-dev/upstream.json`.

## Maintainer checks

```sh
python3 tools/validate_skill.py    # frontmatter, links, JSON, theme template
python3 tools/sync.py --check      # generated references match the pinned upstream
```

`tools/sync.py` needs both upstream checkouts at the pinned commits. Point it at them with `--sdk` and `--can`, or run `scripts/fetch-upstream.sh` first.

## Disclaimer

This is an **unofficial, community project**. It is not affiliated with, endorsed by, sponsored by, or supported by Ola Electric. "Ola" and "S1" are trademarks of Ola Electric, used only to describe compatibility.

- Use it only on a scooter you own.
- Installing a custom dash may affect your warranty or the scooter's behaviour. You accept that risk.
- The upstream software is experimental and has been tested on one scooter. Treat its output as information, not as a safety system. Do not rely on a custom dash for warnings. The scooter's own indicators are the reference.
- Do not use the dash for anything beyond glanceable information while riding.
- The authors provide this without warranty. See `LICENSE`.

## Licence

MIT. See [LICENSE](LICENSE). The skill's references describe GPL-3.0-or-later and MIT upstream projects. The skill does not copy their code, except where a template is written fresh for it.
