# Vehicle-parser interface (summary)

Summary of `sdk/vehicle-interface/SPEC.md` in the pinned `ola-dash-sdk`. The spec is a clean-room interoperability document. For wire detail (codes, argument order, parcel layout), read the spec. Do not duplicate it.

## Shape

- **Service:** package `com.olaelectric.vehicleparser`, class `VehicleParserService`, action `com.olaelectric.vehicleparser.VehicleParserService`. Bind with an explicit component.
- **Binders:** `IVehicleService` (2 methods) returns `IParserService` (15 subscribe calls) and `ICommanderService` (24 methods, of which the SDK uses only `sendTouchEvent`).
- **Subscriptions:** every subscribe call takes a string key. The SDK uses its own package name. Re-subscribe after a reconnect.
- **Callbacks:** 15 callback interfaces, 191 methods. Fourteen are `oneway`. `IVehicleServiceInfoCallbacks` is two-way and must reply with int 0.
- **Enums:** 37, with 635 constants, written on the wire as ordinals. Constant order and method names are load-bearing.
- **Dash behaviour:** the SDK receives every callback and logs it. It keeps only what the contract needs.

Use the SDK's clean-room definitions in `sdk/vehicle-interface/`. Do not use vendor files.

## Callbacks worth knowing

Names are exact. They are load-bearing. Units are as the callback states them. Anything marked *unit unverified* is not established.

| Domain | Callback (interface) | Value | Notes |
|---|---|---|---|
| Speed | `IMotorInfoCallbacks.onSpeedChanged` | int, km/h | Integer display value. Max 2 km/h on the 2026-10-30 walk test |
| Speed | `IMotorInfoCallbacks.onVehicleSpeedChanged` | float | Finer value, same signal |
| Battery | `IBatteryInfoCallbacks.onBatterPackSocChanged` | float, % | Spelling is in the source |
| Battery | `IBatteryInfoCallbacks.onOverallSocChanged` | float, % | Fine SOC |
| Battery | `IDisplayInfoCallbacks.onBatterySocChanged` | int, % | Displayed SOC |
| Battery | `IBatteryInfoCallbacks.onBusVoltage`, `onBatteryCurrent` | float, V and A | Current is negative while discharging per the contract |
| Battery | `IBatteryInfoCallbacks.onPackSoH` | int, % | State of health |
| Battery | `IBatteryInfoCallbacks.onEffectiveBatteryTemperatureChanged`, `onMin...`, `onMax...` | float, degC | Min and max cell temperature |
| Range | `IDisplayInfoCallbacks.onRangeChanged` | int, km | Range for the current mode |
| Odometer | `IDisplayInfoCallbacks.onOdoValueChangedInMeters` | long, m | Cumulative odometer. Not a trip meter |
| State | `IVehicleModeCallbacks.onVehicleStateChanged` | `VehicleStates` | Sleep, idle, park, drive, and others. Ride log shows SLEEP, VEHICLE_IDLE, PARK, DRIVE |
| Lock | `IVehicleModeCallbacks.onVehicleLockStateBCMChanged` | `VehicleLockStateBCM` | Lock feedback, not a ride-ready signal |
| Modes | `IVehicleInfoCallbacks.onDriveModeChanged` | `DriveModes` | Drive mode |
| Modes | `IMotorInfoCallbacks.onVehicleDischargeModeChanged` | `DriveModes` | Discharge mode. Ride log shows it matches the mode in use |
| Modes | `IVehicleModeCallbacks.onVehicleModeLevel4Changed` | `DriveModes` | Level-4 mode. Reverse and park assist appear here |
| Modes | `IVehicleModeCallbacks.onECUModeChanged` | `ECUModes` | ECU state, for example DRIVE_NORMAL |
| Modes | `IHandleBarCallbacks.onDpad_Drive_Mode` | boolean | Mode button press (input, not a command) |
| Reverse | `IVehicleInfoCallbacks.isCruiseReverseMode` | boolean | Pulses in reverse entry |
| Power | `IVehicleInfoCallbacks.isPowerButtonPressed` | `PowerButtonStatus` | Power-button state, for reading |
| Brakes | `IVehicleInfoCallbacks.isFrontBrakeApplied`, `isRearBrakeApplied` | boolean | Brake levers |
| Regen | `IMotorInfoCallbacks.onRegenNotificatioReceived` | `RegenStatus` | Spelling is in the source |
| Motor | `IMotorInfoCallbacks.onMotorRpmChanged`, `onMotorTemperatureChanged`, `onMcuTemperatureChanged` | int rpm, float degC | Rpm and temperatures |
| Indicators | `IDisplayInfoCallbacks.isLeftIndicatorOn`, `isRightIndicatorOn` | boolean, `IndicatorFault` | Stalk state with an optional fault |
| Lights | `IDisplayInfoCallbacks.isHighBeamOn`, `isLowBeamOn`, `isPositionLightOn` | boolean | |
| Stand | `IDisplayInfoCallbacks.isSideStandOn`, `IAlertInfoCallbacks.onSideStandPostionAlert` | boolean | Spelling "Postion" is in the source |
| Charging | `IChargerInfoCallbacks.onChargerConnected` | `ChargerTypes` | Charger type |
| Charging | `IChargerInfoCallbacks.onChargerPluggedIn`, `onVehicleConnectorLatched` | boolean | Plugged in, latched |
| Charging | `IDisplayInfoCallbacks.onChargingStatusChanged` | `ChargingStatus` | Charging state |
| Charging | `IVehicleModeCallbacks.onVehicleChargingModeChanged` | `ChargingModes` | |
| Alerts | `IAlertInfoCallbacks.onFallDetectionAlert`, `onTowTheftDetectionAlert`, `onRegenAvailabilityAlert` | enums | Host alert card and telltale logic lives in `VehicleBridge` |
| Pass code | `IVehicleCommandCallbacks.onPasscodeWindowActivated` | boolean | Passcode window open or closed |

**Not verified:** the charging callbacks above have not been checked on a real charge, and the source repos do not record a charge-session log. Mark charging behaviour as unverified in any report. Do not assume a callback means what its name says until you have a real charge log.

## Modes: wire to contract (host behaviour)

Source: `host/java/dev/olatool/dash/VehicleBridge.java`, `modeIndex`.

| Wire `DriveModes` | Contract `DriveMode` | Status |
|---|---|---|
| ECO | eco | Mapped |
| LIMPHOME | eco | Mapped. Rider-confirmed: Gen 1 reports Eco as LIMPHOME |
| NORMAL | normal | Mapped |
| SPORT | sport | Mapped |
| HYPER | hyper | Mapped |
| CUSTOM | custom | Mapped |
| PARK | park | Mapped |
| REVERSE | reverse | Mapped. Plain reverse not yet seen on the bus |
| PARK_ASSIST | easy-park | Mapped. Observed in a ride log. Plain versus Easy Park is not confirmed |
| any other | unknown | Default |

The contract's `Vehicle.hyper-available` is false when the owner's app revoked Hyper. The mode button then cycles to Custom, as the ride log shows.

## Power-button and mode behaviour (reading only)

The 2026-10-30 ride log (upstream `docs/ride-log-2026-10-30.md`) records:

- Power-button `Normal_Press` toggled PARK and DRIVE. `Long_Press` in PARK locked.
- The mode button cycled Normal, Sport, Custom. Hyper was skipped when revoked.
- Holding the mode button for 3 s reported LIMPHOME, which the rider confirmed is Eco.

These are observations for reading. **Never send them.** See `safety.md` rules 2 and 3.

## Other things the SDK does

- It sends one touch-activity report through `sendTouchEvent` for keep-alive. Keep-alive rules are in `safety.md` rule 8.
- It does not call `unlockedByPasscode` or send `PASSCODE_AUTH` through `sendCommandToScooter`. The unlock flow goes through the profile service. See the SPEC implementer notes, item 6.
- The SPEC does not cover the profile manager service. It has its own spec gap.

## Where to look for detail

- Wire codes, argument order, and enum constants: `sdk/vehicle-interface/SPEC.md`, sections 5 and 6.
- Implementer rules (descriptors, method order, names): section 8 of the same file.
- The CAN side of the same data: `can-bus.md`.
