# Dash SDK: architecture, build, preview, logs

Source: `ola-dash-sdk` at the pinned commit (see `upstream.json`). It is GPL-3.0-or-later. The SDK is experimental, runs on one rooted test scooter, and has no stability guarantee before 1.0.

## Architecture

```
Ola vehicle-parser service (stock)
   | AIDL callbacks (clean-room interface, sdk/vehicle-interface)
   v
VehicleBridge.java      keep-alive, session logs, debug test channel
   | JNI
   v
Rust host (liboladash.so, Slint runtime)
   |- theme loader        themes/<id>/main.slint, loaded at runtime
   |- contract globals    Vehicle, Battery, Ride, Media, Navigation, Plugins, Actions
   |- safety overlay      host/ui/overlay.slint, painted above every theme
   '- plugin data         JSON snapshot from PluginHost
        ^ AIDL IDashPlugin / IDashHost
   plugin APKs (display-only, owner-enabled)
```

- The host writes the contract's `in` properties. Themes read them and never assign them.
- Theme callbacks come back to the host, which decides what they do.
- **Theme load tiers:** the active theme, then the bundled fallback (a copy of `themes/default`), then a last-resort placeholder. A failed compile is logged under the logcat tag `OlaDash`. The app does not crash.
- **Keep-alive:** a one-second tick, the same cadence as the stock `WakeLockNotifier`. The reason is `touch`, `media`, or `none`. Media counts only when the built-in source is playing in PARK or while charging, as the stock HMI does. A plugin's `publishMedia` never counts.
- The unlock path runs on a separate worker, so it cannot block the keep-alive.

## Repository layout

| Path | What it is |
|---|---|
| `contract/vehicle.slint` | The only API a theme sees |
| `host/` | Android host: Rust, Java bridge, overlay, unlock module, build script |
| `sdk/plugin-api/aidl/` | Plugin API v1 (AIDL) |
| `sdk/vehicle-interface/` | Clean-room parser interface and `SPEC.md` |
| `plugins/example-sysinfo/` | Example plugin (GPL). Read it for shape, do not copy |
| `themes/default`, `themes/minimal` | Bundled themes |
| `sim/` | Desktop runner with mock data |
| `tools/check-themes.sh` | Validate every theme |

## Build

**Desktop (themes and sim) needs:** stable Rust, plus fontconfig development files (`fontconfig-devel` on Fedora, `libfontconfig1-dev` on Debian or Ubuntu). The live window also needs `libxkbcommon-dev`. The sim pins `slint` and `slint-interpreter` to `=1.18.1`.

**Host APK needs:** JDK 17 with `javac` (a runtime alone is not enough), Android SDK platform `android-34`, build-tools `34.0.0`, NDK r27c (`27.2.12479018`), Rust with target `aarch64-linux-android`, and the same Slint `=1.18.1`. The NDK's clang does the linking. Gradle and cargo-ndk are not used.

`host/build.sh` cross-compiles the crate, compiles the AIDL with `aidl --lang=java`, runs `javac --release 8` and `d8`, links with `aapt2`, zipaligns, and signs with the debug key. The output is `host/out/ola-dash-debug.apk`.

**Build on the owner's machine or a build host the owner chooses.** Do not build on a machine you have not been asked to use.

Install and uninstall commands change the scooter. Run them only with the owner's approval and an authorised adb session.

```sh
adb install -r host/out/ola-dash-debug.apk
adb shell am start -n dev.olatool.dash/.MainActivity
adb uninstall dev.olatool.dash
```

The current APK is debug-signed and sets `android:debuggable="true"`. That enables the test channel. A release flavour is on the roadmap.

## Preview without a scooter

```sh
# Live window, mock data (needs a display)
cargo run --release --manifest-path sim/Cargo.toml -- themes/default

# Headless PNG at sim time 75 s, deterministic
mkdir -p sim/out
cargo run --release --manifest-path sim/Cargo.toml -- themes/default --screenshot sim/out/default-t75.png --at 75

# Validate every bundled theme (manifest and full compile)
tools/check-themes.sh
```

- The sim loop is 120 s. From 0 to 60 s the mock vehicle rides, cycling eco, normal, sport, and hyper every 15 s, and the battery falls from 100 to 60. From 60 to 120 s it charges. Useful times: 5, 20, 50, and 75 s.
- `sim` looks for the contract at `<theme>/../../contract`. Override with `--contract <dir>`.
- `SIM_PLUGINS=1` adds mock plugin widgets and a navigation card.

## Logs

On the device, session logs live in the app's external files directory:

```
/sdcard/Android/data/dev.olatool.dash/files/logs/
  calls-<yyyyMMdd-HHmmss>.log   every vehicle callback with its arguments, plus host events
  can-<yyyyMMdd-HHmmss>.log     raw vcan0 traffic from a read-only candump
```

- Pull without root: `adb pull /sdcard/Android/data/dev.olatool.dash/files/logs ./logs`. Pull into a git-ignored folder such as `tmp/`.
- The folder is capped at 1 GiB. The oldest files go first.
- Test-channel events are prefixed `TEST`.
- Logs contain vehicle identifiers and state history. Redact before sharing.

## Test channel (debug builds only)

`host/test/inject.sh <cb> <method> [args]` runs one parser callback as if the vehicle had sent it. `inject.sh off` ends test mode and replays the real parser state. Test mode shows a TEST DATA banner, disables the real keypad submission, and never sends commands or changes unlock state. It needs a root or DUMP-permitted shell.

Never ship the test channel in a release. Never use it to fake a real vehicle state for a user.

## Home-screen swap (development only)

`host/test/hmi-swap.sh dash` makes the host the home activity. `hmi-swap.sh stock` restores the stock HMI. It needs a root adb session. Always restore the stock HMI before uninstalling.

## Keep-alive and the stock rule

The stock rule is touch-driven. The SDK adds one exception that matches the stock HMI: built-in media playing in PARK or while charging. Do not add to these rules, and do not write a loop that holds the vehicle awake.

## Contributing to the SDK

Read `CONTRIBUTING.md` upstream before you propose a change. Do not commit to the upstream repos from this skill.
