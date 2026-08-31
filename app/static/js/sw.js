self.addEventListener(push, function(event) {
    if (!event.data) return;

    let payload = {};
    try {
        payload = event.data.json();
    } catch (e) {
        payload = { title: Market Alert, body: event.data.text() };
    }

    const title = payload.title || ⚡ Market Alert;
    const options = {
        body: payload.body || Price alert condition triggered!,
        icon: payload.icon || /static/icon.png,
        badge: /static/icon.png,
        vibrate: [200, 100, 200],
        data: payload.data || {},
        tag: market-alert- + Date.now(),
        renotify: true,
        requireInteraction: true
    };

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

self.addEventListener(notificationclick, function(event) {
    event.notification.close();
    const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : /;

    event.waitUntil(
        clients.matchAll({ type: window, includeUncontrolled: true }).then(function(clientList) {
            for (let i = 0; i < clientList.length; i++) {
                let client = clientList[i];
                if (client.url && focus in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(targetUrl);
            }
        })
    );
});
