# Build notes (starter widget plugin)

1. Pick a package name and rename `com.example.dashwidget` in the manifest and in the Java source (directory included). Keep the action `dev.olatool.dash.plugin.PLUGIN`.
2. Get the plugin AIDL from a pinned `ola-dash-sdk` checkout (`scripts/fetch-upstream.sh`). Copy it first: `aidl` without `--lang=java` rewrites its inputs in place.
3. Generate the Java stubs:
   `aidl --lang=java -I <copy>/aidl -o <gen> <copy>/aidl/dev/olatool/dash/plugin/*.aidl`
4. Compile with `javac --release 8` against `android.jar` (platform 34), then `d8 --min-api 29`.
5. Package with `aapt2 link` (manifest only), add `classes.dex`, `zipalign -p`, and sign with a debug or release key you control.
6. Install only with the owner's approval. Enable it on the host by the owner's chosen method (see `references/plugins.md`).

Build with the Android SDK on a machine the owner chooses. Do not build on a machine you have not been asked to use.
