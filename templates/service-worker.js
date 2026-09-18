self.addEventListener("install", function (event) {
    self.skipWaiting();
});

self.addEventListener("activate", function (event) {
    event.waitUntil(self.clients.claim());
});

self.addEventListener("push", function (event) {
    let payload = {};
    try {
        payload = event.data ? event.data.json() : {};
    } catch (error) {
        payload = {
            title: "Giorgos Health",
            body: event.data ? event.data.text() : "Νέα υπενθύμιση",
        };
    }

    const title = payload.title || "Giorgos Health";
    const options = {
        body: payload.body || "Νέα υπενθύμιση",
        icon: payload.icon || "/static/icons/icon-192.png",
        badge: payload.badge || "/static/icons/icon-192.png",
        tag: payload.tag || "giorgos-health-reminder",
        renotify: payload.renotify !== false,
        silent: payload.silent === true,
        vibrate: payload.vibrate || [220, 100, 220],
        data: payload.data || {url: payload.url || "/reminders/"},
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener("notificationclick", function (event) {
    event.notification.close();

    const targetUrl =
        (event.notification.data && event.notification.data.url) ||
        "/reminders/";

    event.waitUntil(
        self.clients.matchAll({
            type: "window",
            includeUncontrolled: true,
        }).then(function (clientList) {
            for (const client of clientList) {
                if ("focus" in client) {
                    client.navigate(targetUrl);
                    return client.focus();
                }
            }

            if (self.clients.openWindow) {
                return self.clients.openWindow(targetUrl);
            }
        })
    );
});
