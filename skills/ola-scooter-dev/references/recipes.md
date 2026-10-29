# Recipes

Each recipe is short. Stop and ask the owner at any step that touches a rule in `safety.md`.

## 1. A new theme

1. `scripts/fetch-upstream.sh` so the contract and the bundled themes are on disk.
2. Copy `templates/theme/` to `themes/<id>/` in your own folder. Set `id` in `theme.json` to the folder name.
3. Keep `export component Dash inherits Window`, the 1280 x 768 size, and the top 48 px empty.
4. Use only the contract's read-only values and the allowed callbacks (`themes.md`).
5. Compile and check: `tools/check-themes.sh themes/<id>` in the SDK, or `sim --check`.
6. Render: `sim themes/<id> --screenshot out-20.png --at 20`, and at 50 and 75 s. Look at the PNGs.
7. Report what you rendered and what you did not check on the device.

## 2. A widget plugin

1. Read `plugins.md`. Pick slots: a widget plugin needs only `widgets`.
2. Copy `templates/plugin/` to your own folder. Rename the package. Keep the action `dev.olatool.dash.plugin.PLUGIN`.
3. Build the AIDL from the pinned upstream: `aidl --lang=java -I <upstream>/sdk/plugin-api/aidl -o gen <upstream>/sdk/plugin-api/aidl/dev/olatool/dash/plugin/*.aidl`. Copy the AIDL first, because `aidl` without `--lang=java` rewrites its inputs in place.
4. Publish within the limits: 4 widgets, 32-char id, 32-char title, 16-char value and unit.
5. Tell the owner how to enable it. Do not write `files/plugins/enabled` for them without agreement.
6. Test with a debug host, or report that you did not.

## 3. A navigation or media plugin

Same as recipe 2, with `media` or `navigation` in `slots`. The owner must also grant notification-listener access for media. Keep strings within the limits (48 characters for media and navigation text). Never publish a control that changes the vehicle.

## 4. Read and analyse a ride log

Logs are `calls-*.log` (one line per callback with its arguments, plus host events) and `can-*.log` (raw `vcan0` traffic). Pull them into a git-ignored folder.

1. `adb pull /sdcard/Android/data/dev.olatool.dash/files/logs ./tmp/ride-logs`. Use `tmp/` only.
2. Open one file and read its line format before you parse it. Do not assume a format from this skill.
3. Group by callback name. For each domain, list the values seen and their timestamps.
4. Compare against `vehicle-interface.md`. Note any callback you cannot explain. Do not invent a meaning.
5. For CAN, decode frames with `tools/decode.py` in the CAN repo, then mark each result with its confidence fields.
6. Redact before you share: remove VIN, odometer values you do not need, location, and any account identifiers.
7. Write up what you observed and what you did not establish.

## 5. Decode a CAN capture

1. Match the frame ID to `can-bus.md` key IDs or the catalog.
2. If the ID has no curated signals, say so. Do not infer a field from a neighbouring one.
3. Run the decoder on the payload hex. Report raw values and the unit confidence.
4. Compare with a callback at the same time in `calls-*.log`. A callback alone is not correlation (see `can-bus.md`).
5. Record the conditions: parked, riding, charging, button, and repeat count.

## 6. Add a contract field

The contract is additive only. Follow the SDK's `CONTRIBUTING.md` upstream. In order:

1. Add the field or enum value to `contract/vehicle.slint`. Append enum values at the end. Choose a unit suffix in the name, such as `-kmh`, `-km`, `-pct`, `-c`, `-a`, `-v`.
2. Bump `contract-version` and add a line to the history comment at the top.
3. Set the value from the host. Find where the bridge receives the callback (`VehicleBridge.java`), map it, and pass it to Rust with JNI. Add the Rust slot (`host/src/lib.rs`).
4. Set the value in `sim`, so themes can be previewed.
5. Update the CHANGELOG under Unreleased, and `docs/contract.md`.
6. Run `tools/check-themes.sh`. Both bundled themes must still pass.
7. In this skill, run `tools/sync.py` to regenerate `contract.md`, after you have pinned the new upstream commit.

## 7. Contribute a CAN finding

1. Follow the evidence rules in `can-bus.md`. Mark anything you did not establish as unknown.
2. Use the upstream `New signal / frame` or `Correction` template.
3. Keep it passive: a capture, not a transmit test.
4. Redact, then open the issue or pull request in the CAN repo. Do not commit to it from this skill.

## 8. Report the outcome

Every recipe ends with a short report: what was done, the commit you used, the commands you ran and their result, what you checked on a device or in sim, and what you did not check.
