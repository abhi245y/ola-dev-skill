# Troubleshooting

Each entry gives the symptom, the cause, and the fix. Entries marked *unverified* come from maintainer notes or general practice, not from the pinned source repos.

## Preview and themes

- **The theme shows nothing, or the host falls back to the default theme.** Check for a compile or import-guard failure under logcat tag `OlaDash`. Run `sim --check themes/<id>` to reproduce it on the desktop.
- **`sim` shows no values.** Keep `export component Dash inherits Window` and use the pinned sim. It wraps `Dash` and re-exports contract globals; the theme need not re-export them (`host/src/theme_root.rs` `ROOT`, `sim/src/main.rs` `load` upstream).
- **The host rejects a theme.** Check `theme.json`: `id` must equal the folder name, `contract` must not exceed the host's contract version, and `entry` must be a relative path inside the folder with no `..`.
- **`import guard: ...`.** Imports may reach only the theme folder and contract. Remove symlinks and banned source words, even in comments. Keep font imports inside the theme folder; no absolute font paths or `..` segments. Fonts named `OlaDash Host` or over 16 MiB are refused. Full list: `themes.md`.
- **A theme compiles but keeps crashing at start.** After two crashing starts, the bad-theme guard selects `default` on the third start and lists the theme in `files/themes/bad`. Strikes live in `files/themes/strikes`. Start-up wiring still needs a manual device test (`docs/architecture.md`, `docs/testing.md` upstream).
- **My theme font does not change host text.** Expected. Telltales, alerts and lock-screen text use the host font `OlaDash Host`. Lock-screen `sans` uses it too. Do not ship a font with that name.
- **Writing `Vehicle.*` does not change the overlay.** Expected. The overlay and lock screen read host-owned `HostState` copies. Those writes only break the theme's own drawing. Do not write contract inputs or import host UI.
- **A high `z` does not cover the overlay.** Expected. The host wrapper keeps `Dash` below it. Do not work around this rule.
- **Overlay or lock colours are not the ones I set.** The host checks contrast (4.5:1 for the strip and keypad text, 3:1 for accents) and falls back to its own colours. It logs the rejection under `OlaDash`. `sim` prints it to stderr. Pick colours that pass.
- **Telltales are in the wrong place.** Check `overlay-placement` in the theme and the `--placement` you previewed with. The host clamps placement to the screen, and it does not let a theme hide the strip.
- **The trunk key does nothing.** That is expected when a host guard refuses. Check the calls log for `trunk request: refused <reason>` (the reasons in `TrunkGate.refusal` are `test mode`, `repeat within 3 s`, `no commander`, `scooter not unlocked`, `not in park`, `speed not reported`, `moving`, `trunk state not reported`, and `already open`). A theme cannot override the gate. Do not add a retry loop.
- **Apps or themes keys do nothing.** `Actions.open-apps()` and `Actions.open-themes()` need contract 7. The contract says they are ignored unless parked. At the pin they only log calls; host screens are not wired yet. Host screens and app launches need `HostState.parked`; its readers are not wired yet (`docs/contract.md`, `CHANGELOG.md` Unreleased upstream).
- **Night colours never appear on the device.** The host does not set `Display.night` yet. Use contract 7 and `sim --night` to preview a theme that reads it (`docs/contract.md` upstream).
- **Path shape is squashed or offset.** `Path` scales to its bounding box. Set `viewbox-width` and `viewbox-height` to the element's size.
- **A rotated element does not rotate.** `transform-rotation` is ignored by the renderer. Build the shape with rotated coordinates.
- **A glow or shadow is missing.** `drop-shadow-*` is not drawn. Use a radial gradient or a wide translucent stroke.
- **A stroke has one flat colour.** Path stroke gradients use the first stop. Use a solid stroke.
- **Something hangs or the frame rate drops.** A binding with `animation-tick()` redraws every frame. Remove unneeded ones.
- **An animated value stops changing.** Animating a property built from another eased property restarts each step and stalls. Animate the source directly.
- **The desktop render differs from the device.** The sim uses the software renderer. The device uses GL, which the SDK has not tested. Check on the device.
- **Screenshots from the sim look different across runs.** They should not. The same `--at` gives the same frame. If they differ, check the sim time you passed.

## Build

- **`javac` not found, or `d8` fails.** The JDK must include `javac`. A Java runtime alone is not enough. The SDK expects JDK 17.
- **`aidl` rewrote my input files.** `aidl` without `--lang=java` rewrites its inputs in place. Copy the AIDL to a scratch directory first.
- **`import "vehicle.slint"` not found when compiling by hand.** Pass an absolute include path: `slint-compiler -I /abs/path/to/contract -f llr -o out.llr main.slint`. A relative `-I` was not resolved in testing.
- **Build fails on the Slint version.** The SDK pins `slint` and `slint-interpreter` to `=1.18.1`. Use the same version in `sim` and `slint-compiler`.
- **Desktop build fails on fonts.** Install fontconfig development files (`fontconfig-devel` on Fedora, `libfontconfig1-dev` on Debian or Ubuntu). The live window also needs `libxkbcommon-dev`.
- **Contributors without vendor classes cannot build the host.** `CONTRIBUTING.md` says the host needs vendor classes. `docs/building.md` and `host/README.md` say the clean-room interface in `sdk/vehicle-interface/` is enough. Use the clean-room interface. Do not add vendor files.
- **The APK is too large.** The Slint Android backend links Skia, so the `.so` is about 23 MB. That is expected.

## Device and adb

- **`adb devices` shows `offline`.** Reconnect the device, then run `adb kill-server` and `adb start-server` (*unverified in the source repos, general adb practice*).
- **More than one device attached.** Set `ADB_SERIAL` for the SDK scripts, or pass `-s` to adb.
- **The stock HMI came back after a reboot.** The swap is a development step. Run `hmi-swap.sh dash` again, or reinstall. Do not leave the stock HMI disabled without telling the owner.
- **`hmi-swap.sh` says permission denied.** It needs a root adb session.
- **The dash shows stale values or NO DATA.** Parser loss, or no real vehicle callback for 5 s while in drive, sets `Vehicle.data-stale` and the host's red NO DATA badge. Values keep their last state. Check the calls log. Callbacks resuming or parser resubscription clear it. TEST DATA hides the badge, and injected events do not refresh real data (`CHANGELOG.md` Unreleased upstream).

## Logs

- **Logs are missing.** The app's external files directory is `/sdcard/Android/data/dev.olatool.dash/files/logs/`. Check the path. The folder is capped at 1 GiB, and the oldest files go first.
- **A run created many small session files.** A power-button wake recreates the activity, which splits the log. This is expected. The real session is the longer file.
- **A logged `TEST` event appears on a real run.** Test mode was on. Run `inject.sh off`, then check that real state was replayed.

## Plugins

- **The plugin is installed but shows nothing.** The owner has not enabled it. Check `files/plugins/enabled` and the slot.
- **A widget is missing or its text is cut.** Check the limits: 4 widgets per plugin, 6 in total, and 16 characters for value and unit.
- **The plugin dies and comes back late.** The host rebinds with backoff, from 2 s up to 30 s. That is expected.
- **Media shows nothing.** The owner has not granted notification-listener access to `StockMediaService`.

## Safety-related symptoms

- **An alert or telltale is hidden or covered.** This is a critical bug. Stop and report it. Do not work around it.
- **The unlock screen never completes.** The host accepts only the service's answer. It never fakes success or retries an in-flight verification. Check the profile service's reply in the calls log. Do not add a way to skip the check.
- **The vehicle does not sleep.** The keep-alive is holding it awake. Check the keep-alive reason in the calls log. Do not add a timer that defeats sleep.

## CAN

- **Decoder output has `unknown` units.** That is the catalog's answer, not a bug. The unit is not established.
- **A frame's values look wrong.** Check `payload_status` and `raw_runtime_validation`. A `partial` or unverified frame may be missing fields. Do not fill in a guess.
- **Repeated callbacks disagree with a frame's period.** The catalog says repeated callbacks do not establish a CAN period.
