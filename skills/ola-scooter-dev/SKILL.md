---
name: ola-scooter-dev
description: Build themes, widget plugins, and read-only analysis tools for the Ola S1 Pro Gen 1 electric scooter dash (Ola Dash SDK, Slint themes, plugin API v1, vehicle data contract, CAN reference). Use for Ola, S1, S1 Pro, scooter, dash, Slint theme, dash plugin, head unit, vehicle data, CAN bus, ride log, or sim preview requests. Display-only by design: refuses to write code that commands the vehicle.
---

# Ola scooter development

Orientation for building on the Ola S1 Pro Gen 1 dash. This is an unofficial community skill. It is not affiliated with Ola Electric. It applies to a scooter the user owns.

## Scope and pins

- **Generation:** Gen 1 (S1 Pro Gen 1) only. Gen 2 and other models are unknown. Say so instead of guessing.
- **Pins:** `upstream.json` in this folder. Dash SDK 0.1 (experimental, no stability guarantee), theme contract v5, plugin API v1, CAN profile `gen1-hvdp-5.0.0`.
- **Traceability:** every fact in `references/` comes from the pinned SDK or CAN repo. Anything that cannot be traced is marked unverified. Keep it that way.
- **Upstream is read-only for you.** If you find a doc error or a gap, report it. Do not edit the upstream repos.

## Hard rules (never break these)

1. **Owner's own scooter only.** Never help access, track, unlock, or control someone else's vehicle.
2. **Never write code that starts the scooter, selects drive or ride mode, or commands motion.** No power-button, mode-button, or ignition injection. Dash code reads state and shows it.
3. **Unlock only through the owner's existing passcode and the stock profile service.** Never bypass, brute-force, reset, or shorten the attempt limit or cooldown.
4. **Themes and plugins are display-only.** Add no vehicle-command path to the plugin API or a theme. Themes may call only the allowed callbacks in `contract/vehicle.slint`.
5. **The safety overlay must never be hidden, covered, or obscured.** Telltales and alerts stay host-owned. Leave the top 48 px empty.
6. **No raw CAN transmission by default.** Reading and logging are fine. A CAN write needs an explicit owner request, a parked and stationary vehicle, a stated risk, and stock service APIs first. Never while riding.
7. **Never trigger, stage, or interfere with firmware or OTA updates.** Do not touch update-surface components. Reject any contribution that does.
8. **Keep-alive follows the stock rule** (touch-driven, plus the stock media exception). Never hold the vehicle awake indefinitely.
9. **Test data is marked on screen and off by default.** Show a TEST DATA banner. Never ship a test channel or a debuggable build as a release.
10. **Clean-room only.** Do not copy or redistribute Ola's code, assets, keys, passcodes, or decompiled sources. Use the clean-room interface in `sdk/vehicle-interface` as the SDK does.
11. **Glanceable UI while riding.** No menus, text entry, pairing, or settings while moving.

Full rationale: `references/safety.md`.

## Decision tree

| The user wants to... | Read first | Then |
|---|---|---|
| Change the look (layout, colours, fonts) | `references/themes.md` | `templates/theme/` |
| Show extra data (a widget, media, navigation) | `references/plugins.md` | `templates/plugin/` |
| Know what values a theme can read | `references/contract.md` | `references/vehicle-interface.md` |
| Know what the parser sends and what it means | `references/vehicle-interface.md` | `references/can-bus.md` |
| Decode or analyse a CAN frame or capture | `references/can-bus.md` | `references/recipes.md` |
| Build, install, preview, or read logs | `references/dash-sdk.md` | `references/recipes.md` |
| Add a contract field or contribute a finding | `references/recipes.md` | `references/safety.md` |
| Understand the head unit | `references/platform-gen1.md` | |
| Something is broken | `references/troubleshooting.md` | |
| Anything near unlock, ignition, OTA, or raw CAN writes | `references/safety.md` | Stop and ask the owner |

## Workflow

1. Run `scripts/fetch-upstream.sh`. It clones both upstream repos at the pinned commits into a cache directory. Use `--latest` only when the user asks for it, and say that you did.
2. Read the reference for the task. Check that the commit you cite matches `upstream.json`.
3. Start from a template. Keep the code display-only and inside the contract.
4. Preview before the device: `sim` renders a theme headlessly with mock data. Run the SDK's `tools/check-themes.sh`.
5. In the final report, separate what you verified (rendered, compiled, unit-tested, or seen on a real scooter) from what you did not verify.

## Facts that are often wrong

- **Eco.** The wire reports Eco as `LIMPHOME` (ordinal 6). The host maps it to contract `eco`, which the maintainer confirmed on a ride. `PARK_ASSIST` maps to `easy-park`. Plain reverse was not seen on the bus. Do not assume `ECO` maps to Eco.
- **0x153 is not a voltage.** The name `DCDC_VOLTAGE` is a source label. Byte 1 is the power-button status.
- **`-1` means not reported.** Show `--`, not `0`.
- **Odometer and trip.** `onOdoValueChangedInMeters` (0x356) is the cumulative odometer in metres. The contract's `trip-km` is distance since unlock, computed by the host. Do not treat any single CAN field as a trip meter.
- **Units.** Speed (0x354, 0x313), SOC (0x120, 0x352), range (0x68B, 0x6F4), and temperatures carry inferred or static units. Motor current and torque (0x223), IMU values (0x61D, 0x63D, 0x64D), and brightness (0x362) have **no established units**.
- **Enum order is the wire.** Never reorder enum constants. The contract is additive only.
- **Plugin limits.** Four widgets per plugin, six shown in total. Strings are cut at fixed lengths. See `references/plugins.md`.
- **Plugin status in the docs disagrees.** Some SDK docs say the plugin host is in progress, others say it is implemented. Check the pinned commit's code before you rely on either.

## Pointers

- `references/platform-gen1.md`: head unit facts, what is known and unknown
- `references/dash-sdk.md`: architecture, build, sim, logs, test channel
- `references/contract.md`: generated list of every contract field, enum, and callback
- `references/themes.md`: theme anatomy, `theme.json`, renderer limits, design for glanceable use
- `references/plugins.md`: plugin API v1, manifest, enablement, lifecycle, limits
- `references/vehicle-interface.md`: the parser binder service, key callbacks and their values
- `references/can-bus.md`: catalog format, confidence fields, decoder, key IDs table
- `references/recipes.md`: step-by-step recipes
- `references/safety.md`: hard rules with rationale
- `references/troubleshooting.md`: known pitfalls
- `templates/theme/`: starter theme (compiles against contract v5)
- `templates/plugin/`: minimal widget plugin
- `scripts/fetch-upstream.sh`: clone the pinned upstream repos
