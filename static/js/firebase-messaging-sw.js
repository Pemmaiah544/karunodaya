// ============================================================
// Firebase Cloud Messaging - Service Worker
// Handles background push notifications when the app is closed/hidden.
// ============================================================

importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/10.12.0/firebase-messaging-compat.js');

// Firebase config is injected at runtime via the /firebase-sw-config/ endpoint.
// We use a simple self.__FIREBASE_CONFIG__ pattern.
// The config object is embedded in the URL query string at registration time.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', event => event.waitUntil(self.clients.claim()));

// ── Receive the Firebase config posted from the main page ──
self.addEventListener('message', function (event) {
    if (event.data && event.data.type === 'FIREBASE_CONFIG') {
        const firebaseConfig = event.data.config;
        firebase.initializeApp(firebaseConfig);
        const messaging = firebase.messaging();

        // Handle background push messages
        messaging.onBackgroundMessage(function (payload) {
            const notificationTitle = (payload.notification && payload.notification.title)
                ? payload.notification.title
                : '📚 Karunodaya';

            const notificationBody = (payload.notification && payload.notification.body)
                ? payload.notification.body
                : 'You have a new reading reminder!';

            const notificationOptions = {
                body: notificationBody,
                icon: '/static/images/foundation-logo.png',
                badge: '/static/images/foundation-logo.png',
                data: payload.data || {},
                tag: 'karunodaya-reading-reminder',
                renotify: true,
                vibrate: [200, 100, 200],
                actions: [
                    { action: 'open', title: '📖 Open App' },
                    { action: 'dismiss', title: 'Dismiss' }
                ]
            };

            self.registration.showNotification(notificationTitle, notificationOptions);
        });
    }
});

// ── Handle notification click ──
self.addEventListener('notificationclick', function (event) {
    event.notification.close();

    if (event.action === 'dismiss') return;

    event.waitUntil(
        self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
            // If app is already open, focus it
            for (let i = 0; i < clientList.length; i++) {
                const client = clientList[i];
                if (client.url.includes(self.location.origin) && 'focus' in client) {
                    return client.focus();
                }
            }
            // Otherwise open a new tab
            if (self.clients.openWindow) {
                return self.clients.openWindow('/dashboard/');
            }
        })
    );
});
