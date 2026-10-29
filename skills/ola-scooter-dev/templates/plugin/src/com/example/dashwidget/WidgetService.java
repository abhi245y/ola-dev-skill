package com.example.dashwidget;

import android.app.Service;
import android.content.Intent;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.RemoteException;

import dev.olatool.dash.plugin.IDashHost;
import dev.olatool.dash.plugin.IDashPlugin;

/** Starter plugin: one display-only card with a counter. No vehicle access. */
public final class WidgetService extends Service {
    private final Handler main = new Handler(Looper.getMainLooper());
    private IDashHost host;
    private int count;

    // ponytail: fixed 5 s tick; no settings. Add a setting only when a user asks for one.
    private final Runnable tick = new Runnable() {
        @Override
        public void run() {
            count++;
            publish();
            main.postDelayed(this, 5000L);
        }
    };

    private final IDashPlugin.Stub binder = new IDashPlugin.Stub() {
        @Override
        public void attach(IDashHost h, int hostApiVersion) {
            main.post(() -> {
                host = h;
                main.removeCallbacks(tick);
                tick.run();
            });
        }

        @Override
        public void detach() {
            main.post(() -> {
                main.removeCallbacks(tick);
                host = null;
            });
        }

        @Override
        public void onAction(String action) {
            // Display-only: taps on "widget.counter" need no action here.
        }
    };

    @Override
    public IBinder onBind(Intent intent) {
        return binder;
    }

    private void publish() {
        if (host == null) {
            return;
        }
        try {
            host.publishWidget("counter", "Counter", String.valueOf(count), "");
        } catch (RemoteException e) {
            // The host went away; detach() stops the timer.
        }
    }
}
