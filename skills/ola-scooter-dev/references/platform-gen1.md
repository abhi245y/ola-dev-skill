# Head unit platform (Gen 1)

Scope: S1 Pro Gen 1 only. Gen 2 and other models are unknown. Everything here is traced to the pinned Dash SDK (`ola-dash-sdk`) unless marked otherwise.

## Known from the SDK

| Item | Value | Source |
|---|---|---|
| Android | API 29 or later (host `minSdk 29`) | `host/README.md` |
| ABI | arm64-v8a only | `host/README.md` |
| Panel | 1280 x 768 landscape, theme coordinates in panel pixels | `docs/themes.md`, `host/src/lib.rs` |
| Density | 236 dpi. The Android backend scales about 1.47x, so the host forces scale 1.0 after the window exists | `host/src/lib.rs` (comment near line 456) |
| Stock vehicle service | package `com.olaelectric.vehicleparser`, service `VehicleParserService`, binder interface `IVehicleService` | `sdk/vehicle-interface/SPEC.md` section 3.1 |
| Stock HMI (home screen) | package `com.olaelectric.hmiclient`. The dev swap script disables it | `docs/architecture.md`, `host/test/hmi-swap.sh` |
| Stock profile service | `com.olaelectric.profilemanagerservice`, used for passcode unlock only | `host/README.md` |
| Stock Android Auto and Settings | Launched through the contract's `Actions` callbacks | `contract/vehicle.slint` |

## Stock components, at a high level

- **Vehicle-parser service.** Vendor service. Sits between the head unit and the vehicle buses, and exposes decoded state as binder callbacks. Details: `vehicle-interface.md`.
- **Profile manager service.** Owns the passcode check and the unlock request. It enforces its own attempt limit and cooldown. The dash uses it, and nothing else, for unlock.
- **Stock HMI.** The stock home screen. The SDK can replace it during development only, which needs a root adb shell.
- **Buses.** The CAN reference observes traffic on `vcan0`, the Android-side interface. Directions are relative to the head unit. The physical bus topology, bitrate, and originating ECUs are **unresolved** (`ola-can-reference` README).

## adb

- `adb` reaches the head unit over the link. The SDK docs use plain `adb` commands and do not describe the network path. A related public RE project notes that adb may use the head unit's IPv6 link-local address with a scope ID. That note is not verified in the two source repos. Look up your own setup. Do not hard-code an address, and do not share one.
- If `adb` shows `offline`, reconnect the device (see `troubleshooting.md`).

## Reported, not verified here

- The SoC is reported as Qualcomm SDM450 and RAM as about 2.9 GB. Neither figure appears in the two source repos. Check on the device (`getprop ro.board.platform`, `/proc/meminfo`) before you rely on either.

## Unknown or unverified

- Gen 2 hardware, vehicle interface, and display. Not covered.
- Whether the GL renderer on the device matches the software renderer used by `sim`. The SDK says this has not been tested.
- Behaviour of the dash under every power state. The SDK records only the sleep, idle, park, drive, and charging transitions seen in one short test ride.
- Whether non-owner accounts or other users are present on the head unit. Not in scope.
