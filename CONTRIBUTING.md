# Contributing

Thanks for helping. This project is a skill for AI coding agents, plus tools that keep it in step with two upstream projects.

## Ground rules

- Every fact must trace to the pinned upstream repos. If you cannot trace it, mark it unverified.
- Do not add anything that helps access, track, unlock, or control someone else's vehicle, starts or moves a scooter, or transmits CAN frames. See `skills/ola-scooter-dev/references/safety.md`.
- Do not add Ola's code, assets, keys, passcodes, or decompiled sources.
- Do not change the upstream repos from here. Report upstream problems in an issue, or in the upstream project.
- Do not put personal data in the skill: no VINs, IP addresses, home paths, machine names, or account data.

## Before you open a pull request

```sh
python3 tools/validate_skill.py
skills/ola-scooter-dev/scripts/fetch-upstream.sh      # or pass OLA_SDK_DIR / OLA_CAN_DIR
python3 tools/sync.py --check
```

Upstream pins move on their own. `.github/workflows/upstream-sync.yml` runs `tools/update_pins.py`, regenerates the references, and releases a patch version, or opens a `needs-review` PR for a breaking change. To move the pins by hand, run `tools/update_pins.py --sdk DIR --can DIR` with checkouts at the new commits, then `tools/sync.py` in the same pull request, with a CHANGELOG note. Bump MINOR or MAJOR versions by hand with `tools/bump_version.py`.

## Style

- Keep `SKILL.md` under about 400 lines. Put depth in `references/`.
- Use plain, short sentences. State what is verified and what is not.
- Use `--` for unknown values in examples, not `0`.

## Licence

Contributions are accepted under the MIT licence of this repository.
