# Plugins (API v1)

A plugin is an ordinary Android APK. It publishes data into named slots. The host shows that data through its own screens and the theme contract. Plugins are display-only: no method in the API can command the vehicle.

**Status.** The SDK's `docs/plugins.md` and `CHANGELOG.md` (Unreleased) say the host implements API v1. Other SDK docs, including `contract/vehicle.slint` comments, say the host implementation is in progress. Check the pinned commit's `host/java/dev/olatool/dash/plugin/PluginHost.java` before you rely on either claim.

## Declaring a plugin

`AndroidManifest.xml`:

```xml
<service android:name=".WidgetService" android:exported="true">
    <intent-filter>
        <action android:name="dev.olatool.dash.plugin.PLUGIN" />
    </intent-filter>
    <meta-data android:name="dev.olatool.dash.plugin.slots" android:value="widgets" />
</service>
```

- The action is `dev.olatool.dash.plugin.PLUGIN`. `exported="true"` is required so the host can bind.
- The `slots` meta-data is a comma-separated list: `widgets`, `media`, `navigation`. The host ignores calls for any slot not listed.
- The service implements `IDashPlugin`.

## Owner enablement

The host binds a plugin only after the owner enables it. Installing is not enough. Enablement is per plugin and per slot.

The enablement file is `files/plugins/enabled` in the host's private directory, one entry per line:

```
# package                      every slot the plugin declares
com.example.dash.weather
# package:slot,slot            only the listed slots (must be declared)
com.example.dash.nav:navigation
```

On a debug host, `run-as` writes it. Enablement UI is on the roadmap. Do not write the file for an owner without their agreement.

**Media.** Now-playing for the media card comes from the host's built-in `StockMediaService`. Android shows a media session only to an app with notification-listener access. The owner grants that once with `cmd notification allow_listener`. A plugin that publishes media replaces the built-in source, and the most recent publish wins.

## Interfaces

Files: `sdk/plugin-api/aidl/dev/olatool/dash/plugin/` (upstream).

**`IDashPlugin`** (you implement):

| Method | Purpose |
|---|---|
| `oneway void attach(IDashHost host, int hostApiVersion)` | The host is ready. Keep `host` and publish through it. |
| `oneway void detach()` | Stop publishing. The host is going away. |
| `oneway void onAction(String action)` | A user action routed to you. |

`onAction` strings: `media.play-pause`, `media.next`, `media.previous`, and `widget.<id>` when one of your widgets is tapped.

**`IDashHost`** (the host implements it):

| Method | Purpose |
|---|---|
| `int apiVersion()` | Returns 1. |
| `oneway void publishWidget(String id, String title, String value, String unit)` | Add or update a card. `id` is unique within your plugin. |
| `oneway void removeWidget(String id)` | Remove a card. |
| `oneway void publishMedia(String title, String artist, boolean playing)` | Shown only if enabled for `media`. |
| `oneway void publishNavigation(boolean active, String instruction, String distance, String eta)` | Shown only if enabled for `navigation`. |

Calls are `oneway`. A publish has not reached the screen when the call returns.

## Limits

| Item | Limit |
|---|---|
| Widgets per plugin | 4. A fifth new `id` is ignored |
| Widgets shown in total | 6. The default theme shows up to 3 |
| `id` | 32 characters, longer is ignored |
| `title` | 32 characters, cut |
| `value`, `unit`, `distance`, `eta` | 16 characters, cut |
| media title and artist, navigation instruction | 48 characters, cut |

A call for a slot the plugin did not declare, or was not enabled for, is dropped and logged. A call from any uid other than the plugin's own is dropped.

## Lifecycle

1. The owner enables the plugin. The host binds it.
2. The host calls `attach(host, hostApiVersion)`.
3. The plugin publishes. Each `publishWidget` replaces the card with that `id`.
4. The host forwards taps as `onAction("widget.<id>")`.
5. On unbind or shutdown the host calls `detach()`. Stop timers there.

If the plugin dies, the host drops its data and rebinds with backoff: 2 s, doubling to 30 s. A plugin that is not installed is retried the same way, and a package broadcast triggers an immediate rescan.

Themes see a widget's `id` as `<package>|<plugin id>`. Treat it as opaque and pass it back unchanged to `Plugins.widget-clicked`.

## Guarantees and what you may not do

- No method sends a vehicle command.
- No plugin can hide or cover the safety overlay.
- Nothing binds without owner enablement.
- Do not add a method that commands the vehicle. Do not request slot access the owner did not grant.
- Additive changes only. New methods go at the end of an interface and bump the API version.

## Starting point

`templates/plugin/` is a minimal widget plugin (manifest, one service, build notes). Its `README` is `templates/plugin/BUILD.md`. Build it against the upstream AIDL. Do not copy the SDK's GPL example into an MIT project.
