# CAN reference: format, decoder, evidence rules

Source: `ola-can-reference` (MIT) at the pinned commit. The seed profile is **Gen 1, HVDP 5.0.0** (the vehicle-parser APK). It was recovered from decompiled source with JADX. Nothing in it is a complete scooter CAN specification.

## What is in the repo

- `catalog/gen1/hvdp-5.0.0.json`: the canonical profile. 99 known IDs, 52 curated signal fields, 20 enums.
- `docs/generated/gen1-hvdp-5.0.0-frames.md` and `...-enums.md`: rendered from the JSON. Do not edit them by hand.
- `docs/evidence.md`, `docs/corrections.md`, `docs/open-questions.md`, `docs/operations.md`: how to read the claims.
- `tools/decode.py`, `tools/validate.py`, `tools/render.py`, `schemas/catalog.schema.json`.

## Catalog structure

Top level: `schema_version`, `profile`, `generation`, `vehicle_family`, `bus`, `artifacts`, `bit_numbering`, `evidence`, `enums`, `frames`.

- `bus`: `observed_interface` is `vcan0`. `bitrate` is null. `physical_ecu_attribution` is `unresolved`.
- `bit_numbering`: LSB0. Bit 0 is the least significant bit of payload byte 0. Seed fields are little endian.
- `frames[]`: one entry per ID. Keys: `id` (hex, three digits, uppercase), `decimal_id`, `names`, `directions`, `frame_format`, `payload_bytes`, `evidence`, `parsers`, `transmit_variants`, `payload_status`, `raw_runtime_validation`, `signals`, `notes`.
- `signals[]`: `name`, `start_bit`, `bit_length`, `byte_order`, `signed`, `scale`, `offset`, `unit`, optional `enum`, `confidence`, `unit_confidence`, `notes`. Physical value is `raw * scale + offset`.
- `directions`: relative to the head unit. `headunit_rx` is received by the head unit. `headunit_tx` is transmitted by it. `constant_only` means only a constant exists. These are not claims about which ECU sent a frame.

## Confidence fields

Keep these separate:

- `confidence` describes numeric extraction and the affine conversion. In the seed, every signal is `static_source`. That means it was recovered from parser code, not confirmed on the wire.
- `unit_confidence` describes the physical unit: `inferred`, `static_source`, or `unknown`. A verified bit offset and scale do not prove km/h, V, A, or degC. A `null` unit means **not established**, not dimensionless.
- `raw_runtime_validation` is `unverified` for all 99 frames. No redacted raw-frame trace has been published that proves a layout on a real vehicle.
- `payload_status`: `partial` (some fields curated), `not_curated` (ID and method only), `decompile_gap` (dispatch exists, body not recovered).

Evidence levels (from `docs/evidence.md`): `static_source` (parser or constructor expression), `inferred` (a stated interpretation), `runtime_correlated` (raw frames matched to an observed value or action). Callback-only observations do not make a frame correlated.

## Decoder

Python 3.10+. No third-party packages. Decodes supplied hex only. It does not connect to a bus and does not transmit.

```sh
python3 tools/decode.py --id 0x354 --data 2F00000000000000
```

Output: profile, ID, raw and scaled values per signal, unit, and both confidence fields. The decoder applies the documented affine maths with decimal factors. It does not emulate vendor float rounding.

Run the checks upstream before you trust a change to the catalog:

```sh
python3 tools/validate.py
python3 tools/render.py --check
python3 -m unittest discover -s tests -v
```

## Key IDs

The table below is generated from the pinned catalog by `tools/sync.py`. The "Meaning" column is hand-written and is a reading hypothesis unless the catalog marks it otherwise. Do not transmit any ID whose direction is `headunit_tx`.

<!-- BEGIN GENERATED: key-ids -->
<!-- Generated from the pinned catalog by tools/sync.py. Do not edit by hand. -->

| ID | Dec | Names | Direction | Curated signals (unit) | Meaning |
|---|---|---|---|---|---|
| `0x120` | 288 | OVERALL_BATTERY_STATUS_INFO | headunit_rx | `overall_soc` (%) | Overall battery state of charge (%). |
| `0x140` | 320 | BMS00_PARAM_2 | headunit_rx | `battery_current` (A) | Battery current (A). Sign convention to confirm on a real ride. |
| `0x143` | 323 | VEHICLE_MODE_CAN_ID | headunit_rx | none curated | Vehicle mode. Body not recovered: map only from callbacks and raw captures. |
| `0x144` | 324 | VEHICLE_LOCK_STATE_BCM | headunit_rx | `bcm_lock_state` (unit unknown) | BCM lock state enum. Lock feedback, not a ride-ready signal. |
| `0x150` | 336 | BMS00_PARAM_3 | headunit_rx | `bus_voltage` (V) | Bus (pack) voltage (V). |
| `0x153` | 339 | DCDC_VOLTAGE | headunit_rx | `power_button_status` (unit unknown) | Power-button status. The source name says DCDC_VOLTAGE, but it is not a voltage. |
| `0x15B` | 347 | VEHICLE_DISCHARGE_MODE_REQUEST | headunit_rx | `requested_drive_mode` (unit unknown) | Requested drive mode (DriveModes enum). |
| `0x160` | 352 | BMS00_PARAM_4 | headunit_rx | `effective_battery_temperature` (degC); `minimum_battery_temperature` (degC); `maximum_battery_temperature` (degC) | Effective, minimum and maximum battery temperature (degC). |
| `0x223` | 547 | MCU_DATA_3_CAN_ID | headunit_rx | `motor_current_raw` (unit unknown); `motor_torque_raw` (unit unknown); `current_trip_distance_raw` (unit unknown) | Motor current, torque and trip raw values. Units unresolved: do not label. |
| `0x224` | 548 | MCU_DATA_4 | headunit_rx | `vehicle_direction_raw` (unit unknown) | Vehicle direction raw bit. Meaning of each value not established. |
| `0x313` | 787 | MUC_DATA_1_CAN_ID | headunit_rx | `vehicle_speed` (km/h); `mcu_temperature` (degC); `motor_temperature` (degC); `motor_rpm` (rpm) | Vehicle speed (km/h, scale 0.1), MCU and motor temperature, motor RPM. |
| `0x352` | 850 | DISPLAY_INFO_4 | headunit_rx | `displayed_soc` (%) | Displayed state of charge (%), integer. |
| `0x354` | 852 | DISPLAY_INFO_2 | headunit_rx | `displayed_speed` (km/h) | Displayed speed (km/h), integer. The value the stock dash shows. |
| `0x356` | 854 | DISPLAY_INFO_5 | headunit_rx | `odometer_meters` (m) | Odometer in metres (32-bit). Cumulative, not a trip meter. |
| `0x61D` | 1565 | IMU_DATA_X_CAN_ID | headunit_rx | `accelerometer_x_raw` (unit unknown); `gyrometer_x_raw` (unit unknown) | IMU X axis, raw integer minus 2000. Units unknown. |
| `0x64D` | 1613 | IMU_DATA_Z_CAN_ID | headunit_rx | `accelerometer_z_raw` (unit unknown); `gyrometer_z_raw` (unit unknown) | IMU Z axis, raw integer minus 2000. Units unknown. |
| `0x683` | 1667 | VEHICLE_SAFETY_STATE | headunit_rx | `fall_detection` (unit unknown); `tow_theft_detection` (unit unknown); `regen_availability` (unit unknown); `hill_hold_status` (unit unknown); `tamper_pseudo_wakeup` (unit unknown) | Vehicle safety state: fall, tow/theft, regen availability, hill hold, tamper wakeup. |
| `0x68B` | 1675 | VEHICLE_RANGE_2 | headunit_rx | `custom_mode_range` (km) | Custom-mode range (km). |
| `0x6AE` | 1710 | ACTIVATE_PASSCODE_WINDOW | headunit_rx | `passcode_window_active` (unit unknown) | Passcode window active flag. |
| `0x6C0` | 1728 | COMMAND_ACK | headunit_rx | `hmi_command_ack` (unit unknown) | HMI command acknowledgement (received). |
| `0x6D0` | 1744 | VEHICLE_COMMAND_CAN_ID | headunit_rx | `vehicle_command` (unit unknown) | Vehicle command byte (received). Vocabulary in the enum tables. |
| `0x6F4` | 1780 | VEHICLE_RANGE | headunit_rx | `eco_range` (km); `sport_range` (km); `normal_range` (km); `hyper_range` (km) | Range per mode: eco, sport, normal, hyper (km). |
| `0x643` | 1603 | sendTouchEvent | headunit_tx | `touch_activity` (unit unknown) | TRANSMIT. Touch-activity report from the head unit. Never transmit (safety.md). |
| `0x6BC` | 1724 | sendScooterCommands | headunit_tx | `hmi_command` (unit unknown) | TRANSMIT. HMI command. Never transmit (safety.md). |
<!-- END GENERATED: key-ids -->

## Known gaps (from the catalog's open questions)

- `0x143` vehicle modes and `0x353` telltales: dispatch known, body not recovered.
- `0x660` feature availability, `0x6AD` handlebar D-pad, `0x691` proximity: decompile gaps.
- `0x223` trip byte: position known, units, counter semantics, and rollover unknown.
- IMU values: the parser adds -2000 to a little-endian integer. Units, axes, and range are unknown. It is not IEEE 754 payload decoding.
- Frame timing: repeated callbacks at about 100 ms do not establish a guaranteed CAN period.
- Physical bus topology, bitrate, and originating ECUs: unresolved.
- Gen 2 and other firmware: no profile.

## Corrections worth knowing

From `docs/corrections.md`:

- IMU Z is `0x64D`, not `0x65D`. `0x65D` is magnetometer X/Y transmit.
- `0x153` is named `DCDC_VOLTAGE` but byte 1 is the power-button status.
- Side-stand disable and enable are 90 and 91, not 91 and 92.
- The vehicle-command enum has 217 values (0 to 216). The HMI, App, and voice enums have 107, 22, and 14 values.
- The `0x690` proximity layout puts the command in byte 0, zero in byte 1, and the value in byte 2.
- Unused bytes in a constructed transmit frame are zero. That does not prove they are reserved.

## Contributing a finding

Use the `New signal / frame` or `Correction` issue template, or a pull request that follows `templates/frame.json` and `CONTRIBUTING.md` upstream.

Include:

- generation and firmware or profile (add a new profile rather than editing old ordinals in place)
- CAN ID in hex and decimal, format, direction, and payload length
- byte and bit offsets, byte order, sign, scale, offset, and unit, or the word **unknown**
- evidence: a source symbol, a file SHA-256, or a short redacted raw-frame window
- conditions: parked, riding, charging, button press, repeat count

Rules: separate observation from interpretation. Never substitute zero for an unknown byte. Redact VINs, PINs, locations, BLE addresses, and profile data. Keep the excerpt minimal. Passive captures are enough. Transmit testing is not required, and this skill does not do it.
