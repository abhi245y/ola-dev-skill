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
| `contract` | Required. Integer, at least 1, at most the SDK's `contract-version` (7 at the pin). Declare the lowest you need: `5` if you use no newer feature, `6` for `Actions.open-trunk()`, `Vehicle.trunk-open`, or optional v6 `Dash` properties (`overlay-placement`, `telltale-order`, `overlay-style`, `alert-position`, `lock-style`). Use `7` for `Display.night`, `Vehicle.data-stale`, `Actions.open-apps()` or `Actions.open-themes()`. |
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
- **Globals are re-exported by the wrapper.** The host and `sim` wrap `Dash` in the same host root. A theme need only export `Dash`; keeping its own global exports is harmless (`docs/contract.md` "Re-exporting globals"; `host/src/theme_root.rs` `ROOT` and `sim/src/main.rs` `load` upstream).
- **Import the contract as `"vehicle.slint"`.** The host and `sim` put the contract directory on the include path, so do not copy it into your theme. For a standalone compile, use `slint-compiler -I <contract-dir>`.
- Use the contract's globals only. Do not write to `in` properties.

## Import guard and host state

The guard allows imports only from the theme's own folder and `contract/`. No symlinks. Do not import `host/ui/*.slint`. These words are refused anywhere in theme source, including comments: `PopupWindow`, `Tooltip`, `ContextMenuArea`, `MenuBar`, `DragArea`, `std-widgets.slint`.

Font imports must stay inside the theme folder. Absolute font paths and paths with a `..` segment are refused. Theme fonts (`.ttf`, `.otf`, `.ttc`, in any subfolder) may not contain the host family name `OlaDash Host`. Font files over 16 MiB are refused. `sim --check` prints `import guard: ...` for a refusal; the device falls back to the bundled theme.

The host wraps `Dash`, so a theme's own `z` stays below the overlay. The overlay and lock screen read host-owned `HostState` copies of telltales, clock, battery and stale state. Writing `Vehicle.*` changes only the theme's own drawing. It cannot change those host values. Host text uses the host font, `OlaDash Host`; the theme's `default-font-family` affects only its own text.

`tools/check-themes.sh` also checks `tools/fixtures/refused/` and `tools/fixtures/loads/`. Refused fixtures must fail in the import guard. Loads fixtures must load with the overlay and lock screen intact, including a lit left indicator. The script also checks the NO DATA badge with `--stale` (`tools/check-themes.sh` upstream).

## Display and stale data (v7)

- `Display.night` is false by default. Themes may use it for a night palette or ignore it. The host does not set it yet. Preview with `sim --night`.
- `Vehicle.data-stale` is true when the parser is gone, or no real vehicle data callback arrived for 5 s while in drive. Other values retain the last known state. It clears when callbacks resume or the parser resubscribes. Injected test events do not count.
- The host draws a red NO DATA badge in the TEST DATA slot. It is hidden while TEST DATA shows. Themes may add a hint or ignore `Vehicle.data-stale`. Preview with `sim --stale`.

These additions are compatible with v6 themes, which load unchanged (`docs/contract.md`, `CHANGELOG.md` Unreleased upstream).

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
- `sans` uses the host font, `OlaDash Host`. `segment` uses the host's seven-segment shapes for digits and clock.
- Preview with `sim --state locked`, `locked-error`, or `cooldown`.
- Themes with no `lock-style` show the host default look, a good starting point for a plain screen.

## What a theme may show

- Speed, battery, range, mode, clock, trip, odometer, media, and the buttons. Touch targets at least 64 px.
- Telltales and safety alerts: **none drawn by the theme.** The host draws them and can be told where (placement, order, style). The exception is the optional turn arrow inside the gauge.
- High beam, headlight, and locked state are drawn by the host overlay. A theme may ignore them.
- `DriveMode.unknown` is valid. Show it with a neutral accent.
- `-1` values show `--`.

## Callbacks allowed

`Media.play-pause()`, `Media.next()`, `Media.previous()`, `Actions.open-android-auto()`, `Actions.open-settings()`, `Actions.open-trunk()` (v6, host-gated, see `safety.md` rule 4), `Actions.open-apps()` and `Actions.open-themes()` (v7), and `Plugins.widget-clicked(id)`. Nothing else. Never add a callback that can change vehicle state.

The v7 apps and themes callbacks ask for host screens. The contract says the host ignores them unless parked. At this pin they only log the call; the screens are not wired yet. Host screens and app launches must use the host-owned `HostState.parked` gate. It means unlocked, in Park and stopped, or unlocked and charging; never in test mode. Charging does not require a speed value. The gate is pushed to the host but has no reader yet. It is not a theme API (`TrunkGate.java`, `CHANGELOG.md` Unreleased upstream).

**Trunk key pattern.** Show the key as enabled only when the host could accept it: parked, stopped, and `Vehicle.trunk-open` false. Gate the `TouchArea` on that same condition. The host checks again (unlocked, Park, integer speed 0, latch known closed, 3 s between requests), and the theme gets no result, so show nothing that suggests the trunk is opening. The reference themes gate on `Vehicle.state == VehicleState.park && Vehicle.speed-kmh == 0 && !Vehicle.trunk-open`, matching the host; copy that condition. Do not add retries.

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
| `--night` | Sets `Display.night` (v7). |
| `--stale` | Sets `Vehicle.data-stale` (v7) and shows the host NO DATA badge. |
| `--placement top\|bottom\|left\|right` | Previews another overlay placement. |
| `--contract <dir>` | Uses another contract folder. |

`SIM_PLUGINS=1` is the older spelling of `--plugins --nav`.

Reference themes at the pin, all declaring `contract: 6`: `default` (top placement), `segment` (top), `fields` (left rail), and `minimal` (top, uses the trunk key). Read them for patterns. Their captures are in `docs/img/themes/` upstream.

Send screenshots at a few times (20 s, 50 s, 75 s) when you show a theme to someone.
