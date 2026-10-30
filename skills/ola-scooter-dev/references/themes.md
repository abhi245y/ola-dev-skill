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
| `contract` | Required. Integer, at least 1, at most the SDK's `contract-version` (6 at the pin). Declare the lowest you need: `5` if you use no v6 feature, `6` if you use `Actions.open-trunk()`, `Vehicle.trunk-open`, any optional v6 `Dash` property (`overlay-placement`, `telltale-order`, `overlay-style`, `alert-position`, `lock-style`). |
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
- **Keep `inherits Window`.** The bundled themes and `host/README.md` both use it, and the host embeds the theme in its own root window. Follow the bundled themes.
- **Re-export the globals you use.** `sim` sets values on the root instance, so the exports must be present. The host re-exports on its own, but keep the line.
- **Import the contract as `"vehicle.slint"`.** The host and `sim` put the contract directory on the include path, so do not copy it into your theme. For a standalone compile, use `slint-compiler -I <contract-dir>`.
- Use the contract's globals only. Do not write to `in` properties.

## Overlay placement and the reserved strip (v6)

The host draws the telltale strip over every theme. A theme may move it with the optional `overlay-placement` property on `Dash`. The default is `top`, which is also what a theme with no declaration gets.

| Placement | Reserved strip |
|---|---|
| `top` (default) | Top 48 px, full width |
| `bottom` | Bottom 48 px, full width |
| `left` | Left 72 px, full height |
| `right` | Right 72 px, full height |

- Keep the reserved strip as plain background. Nothing important goes under it, and the theme's own controls must stay clear of it for the placement you declare.
- Telltales and alert cards use the area outside the strip. Alert cards are centred there, or placed by `alert-position`.
- The host clamps placement so no overlay element goes off screen.

```slint
import { OverlayPlacement, Telltale, AlertPosition, OverlayStyle } from "vehicle.slint";

export component Dash inherits Window {
    out property <OverlayPlacement> overlay-placement: OverlayPlacement.left;
    out property <[Telltale]> telltale-order: [Telltale.left-indicator, Telltale.right-indicator, Telltale.ready];
    out property <OverlayStyle> overlay-style: {
        background: #05070b,
        foreground: #f4f6fa,
        corner-radius: 16px,
        show-labels: true,
    };
    out property <AlertPosition> alert-position: AlertPosition.upper;
}
```

- **Order.** A partial list is allowed. Unknown and duplicate entries are dropped, and missing telltales are appended in host order. A theme can reorder telltales but cannot drop them.
- **Style.** `background` and `foreground` must reach 4.5:1 (WCAG 2.x). Otherwise the host uses its own colours and logs the reason under `OlaDash`. Telltale colours and icon sizes are host-fixed. Labels take the theme's `foreground`.
- **Types.** A wrong type makes the theme fail to compile, so the host falls back to the bundled default.
- Declare only what you need. A theme that omits all four properties behaves as in contract 5.

## Lock screen (v6)

While the scooter is locked or unlocking, the host covers the dash with the passcode screen. A theme only chooses its look, with the optional `out` property `lock-style` on `Dash`:

```slint
import { LockStyle, LockKeyShape, LockDigits } from "vehicle.slint";

export component Dash inherits Window {
    out property <LockStyle> lock-style: {
        background: #05070b,
        foreground: #f4f6fa,
        muted: #8f9bb0,
        accent: #33c3f5,
        key-background: #0c1118,
        key-border: #223045,
        key-shape: LockKeyShape.rounded,
        digits: LockDigits.sans,
    };
}
```

- **The host keeps** the keypad, its key order and labels, all copy, the passcode cells and their count, attempts, cooldown, and error text, and the phase logic. A theme gets no callback, no text, and no layout here, and cannot read the digits entered.
- **Contrast is checked on load.** A failing pair falls back to host colours and is logged. The keys have a fixed minimum size, so a theme cannot shrink them.
- `key-shape` is `rounded`, `square`, or `grid`. `digits` is `sans` or `segment`. Unknown values fall back to the host default.
- Preview with `sim --state locked`, `locked-error`, or `cooldown`.
- Themes with no `lock-style` show the host default look, a good starting point for a plain screen.

## What a theme may show

- Speed, battery, range, mode, clock, trip, odometer, media, and the buttons. Touch targets at least 64 px.
- Telltales and safety alerts: **none drawn by the theme.** The host draws them and can be told where (placement, order, style). The exception is the optional turn arrow inside the gauge.
- High beam, headlight, and locked state are drawn by the host overlay. A theme may ignore them.
- `DriveMode.unknown` is valid. Show it with a neutral accent.
- `-1` values show `--`.

## Callbacks allowed

`Media.play-pause()`, `Media.next()`, `Media.previous()`, `Actions.open-android-auto()`, `Actions.open-settings()`, `Actions.open-trunk()` (v6, host-gated, see `safety.md` rule 4), and `Plugins.widget-clicked(id)`. Nothing else. Never add a callback that can change vehicle state.

**Trunk key pattern.** Show the key as enabled only when the host could accept it: parked, stopped, and `Vehicle.trunk-open` false. Gate the `TouchArea` on that same condition. The host checks again (unlocked, Park, integer speed 0, latch known closed, 3 s between requests), and the theme gets no result, so show nothing that suggests the trunk is opening. The reference themes gate at `Vehicle.speed-kmh < 1`, which is looser than the host's integer-zero rule (see upstream findings). For a new theme, use the stricter check and mark it unverified against the host's int conversion. Do not add retries.

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
- Sim options (upstream `docs/themes.md`):

| Option | Effect |
|---|---|
| `--state ride\|park\|charge\|reverse\|trunk\|easy-park` | Holds one vehicle state. `ride` is the default mock loop. |
| `--state locked\|locked-error\|cooldown` | Shows the host lock screen. |
| `--alert 1..6` | Holds one host alert. Code 3 is the side-stand card. |
| `--plugins` | Feeds three mock plugin widgets. |
| `--nav` | Feeds an active navigation card. |
| `--placement top\|bottom\|left\|right` | Previews another overlay placement. |
| `--contract <dir>` | Uses another contract folder. |

`SIM_PLUGINS=1` is the older spelling of `--plugins --nav`.

Reference themes at the pin, all declaring `contract: 6`: `default` (top placement), `segment` (top), `fields` (left rail), and `minimal` (top, uses the trunk key). Read them for patterns. Their captures are in `docs/img/themes/` upstream.

Send screenshots at a few times (20 s, 50 s, 75 s) when you show a theme to someone.
