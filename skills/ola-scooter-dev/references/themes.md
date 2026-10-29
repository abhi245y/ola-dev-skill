# Themes

A theme is a folder with `main.slint` (the entry) and `theme.json` (the manifest). The host loads it at runtime through `slint-interpreter`, so a theme needs no Rust and no rebuild. Read `contract.md` first: a theme sees only that API.

## Manifest: `theme.json`

```json
{
  "id": "my-theme",
  "name": "My Theme",
  "version": "0.1.0",
  "author": "Your name or handle",
  "license": "MIT",
  "contract": 5,
  "entry": "main.slint",
  "description": "One sentence about the look."
}
```

| Key | Rule |
|---|---|
| `id` | Required. Only `a-z`, `0-9`, `-`. Must equal the folder name. |
| `name` | Required. Display name. |
| `version` | Required. For example `0.1.0`. |
| `author` | Required. |
| `license` | Required. SPDX identifier. The bundled themes are `GPL-3.0-or-later`. Your theme may use any licence you choose, but it must be compatible with the fonts and any SDK code you copy. |
| `contract` | Required. Integer, at least 1, at most the SDK's `contract-version` (5 at the pin). Declare the lowest you need. |
| `entry` | Required. Relative path inside the folder, no `..`, must exist. |
| `description` | Required. One sentence. |

`tools/check-themes.sh` checks these keys and a full compile. The host rejects a theme whose `contract` is higher than its own.

## Entry file

```slint
import { Vehicle, Battery, Ride, Media, Actions, DriveMode, VehicleState, Navigation, Plugins } from "vehicle.slint";
export { Vehicle, Media, Actions, DriveMode, Navigation, Plugins }   // re-export for sim

export component Dash inherits Window {
    width: 1280px;
    height: 768px;
    background: #05070b;
}
```

- The root is exported as `Dash`, sized 1280 x 768 logical px in landscape.
- **Keep `inherits Window`.** The bundled themes and `host/README.md` both use it, and the host embeds the theme in its own root window. `docs/themes.md` still carries an old open question on this. Follow the bundled themes.
- **Re-export the globals you use.** `sim` sets values on the root instance, so the exports must be present. The host re-exports on its own, but keep the line.
- **Import the contract as `"vehicle.slint"`.** The host and `sim` put the contract directory on the include path, so do not copy it into your theme. For a standalone compile, use `slint-compiler -I <contract-dir>`.
- Use the contract's globals only. Do not write to `in` properties.

## Reserved area

The top 48 px belong to the host's telltale bar, drawn over every theme. Keep that strip plain background. Nothing important goes there.

## What a theme may show

- Speed, battery, range, mode, clock, trip, odometer, media, and the buttons. Touch targets at least 64 px.
- Telltales and safety alerts: **none.** The host draws them. The exception is the optional turn arrow inside the gauge.
- High beam, headlight, and locked state are drawn by the host overlay. A theme may ignore them.
- `DriveMode.unknown` is valid. Show it with a neutral accent.
- `-1` values show `--`.

## Callbacks allowed

`Media.play-pause()`, `Media.next()`, `Media.previous()`, `Actions.open-android-auto()`, `Actions.open-settings()`, and `Plugins.widget-clicked(id)`. Nothing else. Never add a callback that can change vehicle state.

## Fonts

Bundle fonts. Do not rely on the device's fonts:

```slint
import "fonts/Inter-Regular.ttf";
```

Ship the font's licence file next to it. The default theme uses Inter under the SIL Open Font License 1.1.

## Size budget

- Theme folder under 2 MB in total. The default theme is about 1.2 MB, almost all of it fonts.
- No bitmap over 200 KB. Prefer `Path`, gradients, and `opacity`.
- No video and no Lottie-style animation.
- Reviewers check the budget by hand. The check script does not enforce it.

## Install (by hand, for now)

A theme lives at `files/themes/<id>/` in the app's private directory. Set the active theme by writing its name to `files/themes/active`. For a debug host, `run-as` writes those files. A theme store is on the roadmap. Themes are not part of the APK.

## Renderer limits

Checked in the software renderer that `sim` uses. The device uses a GL renderer that has not been tested, so re-check on the device.

- `Path` coordinates scale to the bounding box unless `viewbox-*` is set. Set `viewbox-width` and `viewbox-height` to the element size.
- Path arcs (`A`) render. Build them from a `commands` string bound to animated values.
- `transform-rotation` is ignored. Do not rely on rotation.
- `drop-shadow-*` is not drawn. Fake a glow with a radial gradient or a wide translucent stroke.
- Path stroke gradients come out flat (the first stop). Use solid strokes.
- Radial and conic gradients, `clip`, `border-radius`, `opacity`, and `letter-spacing` work.
- `parent` cannot be used in a root element. Use fixed sizes there.
- `ArcTo` takes `radius-x` and `radius-y`. Path coordinates are plain floats.

## Motion

- `animate` eases a property whenever its value changes, including when its binding changes. Use it on readings and on the mode accent.
- Do not animate a property built from another eased property. Each change restarts the animation and it stalls. The default theme gives the mode pills the accent directly for this reason.
- `animation-tick()` in a binding (blink, breathing, sweep) redraws every frame. Keep these bindings few.

## Design for glanceable riding

- One number is the hero. Speed or battery, large. Everything else small and quiet.
- High contrast, dark background for sunlight. Avoid thin strokes and low-contrast grey text.
- Do not animate for its own sake. Motion should explain a change.
- No text entry, lists to scroll, or small controls. Touch targets stay large.
- Use `--` for unknown values, never `0`.
- Keep the mode colour readable without relying on colour alone: show the mode name.

## Previewing

- Live window: `sim themes/<id>` (needs a display).
- Headless PNG: `sim themes/<id> --screenshot out.png --at 75`. The same time gives the same frame.
- Check: `sim --check themes/<id>` validates the manifest and compiles without a window.
- Static preview with defaults: `slint-viewer -I contract themes/<id>/main.slint`. Not checked upstream.

Send screenshots at a few times (20 s, 50 s, 75 s) when you show a theme to someone.
