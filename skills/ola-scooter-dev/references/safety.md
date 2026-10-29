# Safety: hard rules and why

These rules apply to code, themes, plugins, and to how the software is used. They are commitments from the Dash SDK's safety model (`docs/safety.md` upstream), extended for agents that help build on it. Read this file before any work that touches unlock, ignition, control, the overlay, or CAN writes.

## 1. Owner's own scooter only

Build and test only on a scooter the user owns or is authorised to work on. Refuse to help access, track, unlock, or control someone else's vehicle. Refuse to write exfiltration or location code.

*Why:* a dash app that can see state can also be misused against a third party. The ownership boundary is the main control.

## 2. No motion or mode commands

Never write code that starts the scooter, selects drive or ride mode, toggles PARK and DRIVE, or otherwise commands motion. Do not inject power-button or mode-button events. The published CAN and SDK docs describe these events for reading only.

*Why:* starting a scooter in the wrong place kills people. The SDK's own roadmap lists "unlock or ignition that bypasses the scooter's own interlocks" as not planned.

## 3. Unlock goes through the owner's passcode and the stock service

Unlock code must call the stock profile service with the owner's existing passcode, as the SDK's unlock module does. Never bypass, brute-force, reset, or shorten the attempt limit or the cooldown. Never send a direct unlock command, and never send `PASSCODE_AUTH` through the command path. Never store or log the PIN.

*Why:* the attempt limit and cooldown are the protection against guessing.

## 4. Display-only themes and plugins

Themes and plugins are display-only. Do not add any vehicle-command method to the plugin API or to a theme. The only callbacks themes may use are `Media.play-pause`, `Media.next`, `Media.previous`, `Actions.open-android-auto`, `Actions.open-settings`, and `Plugins.widget-clicked`. A plugin may hear `onAction` only for its own widgets and for media.

*Why:* a theme that can command the vehicle turns a display bug into a control bug.

## 5. The safety overlay stays visible

Telltales, alerts, and the unlock screen belong to the host and are painted above every theme. No theme or plugin may hide, move, cover, shrink, or reorder them. Keep the top 48 px empty; the host's telltale bar lives there.

If a change would hide or obscure the overlay, stop and report it. The SDK treats that as a critical bug.

## 6. Raw CAN is read-only by default

Reading and logging CAN traffic is allowed. Transmitting is not, unless the owner asks for it explicitly. Before any CAN write:

- the owner must request it explicitly, for a stated purpose;
- the vehicle must be parked and stationary;
- explain the specific risk;
- prefer the stock service APIs over raw frames;
- never write while riding.

The CAN catalog marks transmit IDs (`headunit_tx`). Their payload layouts are only partly curated and **not validated on a real vehicle**. Do not build a transmitter from them.

## 7. Firmware and update paths are off limits

Do not install, trigger, stage, or interfere with firmware or OTA updates. Do not touch update-surface components, including update-utility calls and update devices. A contribution that does so must be rejected.

## 8. Keep-alive follows the stock rule

Keep the vehicle awake only as the stock HMI does. Touch-driven, plus the stock media exception. Never hold the vehicle awake indefinitely, and never add a timer that defeats sleep.

## 9. Test data is marked and off by default

Injected or mock data must show a TEST DATA banner on screen, and be off unless the user turns it on. Never ship a test channel, a debuggable APK, or mock data in a release build. Release builds must be built without `debuggable`.

## 10. Clean-room only

Do not copy or redistribute Ola's code, assets, keys, passcodes, account data, or decompiled sources. The SDK's vehicle interface is written from an interoperability spec. Use it. Do not add vendor files.

Do not publish logs or screenshots that contain passcodes, account identifiers, or a VIN. Redact first.

## 11. Glanceable while riding

The dash is for information only while moving. Do not design menus, text entry, pairing, settings, or media browsing that the rider must use while moving. Keep text short and large. Put setup behind a stopped state.

## Reporting a safety problem

Stop. Tell the user what you saw, what file and line, and what you would change. Do not work around the rule. For a vulnerability in the upstream SDK, follow its `SECURITY.md`.
