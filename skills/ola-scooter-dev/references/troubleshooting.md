# Troubleshooting

Each entry gives the symptom, the cause, and the fix. Entries marked *unverified* come from maintainer notes or general practice, not from the pinned source repos.

## Preview and themes

- **The theme shows nothing, or the host falls back to the default theme.** The theme failed to compile. Check the logcat tag `OlaDash` for the diagnostic. Then run `sim --check themes/<id>` to reproduce it on the desktop.
- **`sim` shows no values.** The entry file does not re-export the globals. Add `export { Vehicle, Media, Actions, DriveMode }` (plus any others you use).
- **The host rejects a theme.** Check `theme.json`: `id` must equal the folder name, `contract` must not exceed the host's contract version, and `entry` must be a relative path inside the folder with no `..`.
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
- **The dash shows stale values.** Check the calls log for the callback. If the callback is absent, it is a parser or bus question, not a theme question.

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
