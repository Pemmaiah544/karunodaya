/**
 * Firebase Web Push — Karunodaya
 *
 * Initializes Firebase, registers the service worker, requests notification
 * permission from the user, obtains the FCM device token and registers it
 * with the Django backend so the server can send push notifications.
 *
 * Configuration is passed in via the global KARUNODAYA_FIREBASE_CONFIG object
 * that the Django template renders.
 */
(function () {
    'use strict';

    // ── Guard: must have config injected by the template ──────────────────
    if (!window.KARUNODAYA_FIREBASE_CONFIG) {
        console.warn('[FCM] Firebase config not found. Push notifications disabled.');
        return;
    }

    const config = window.KARUNODAYA_FIREBASE_CONFIG;

    // ── 1. Check browser support ──────────────────────────────────────────
    if (!('serviceWorker' in navigator) || !('Notification' in window)) {
        console.warn('[FCM] Browser does not support push notifications.');
        return;
    }

    // ── 2. Initialize Firebase app (idempotent) ───────────────────────────
    let app;
    try {
        app = firebase.app();  // Already initialised
    } catch (e) {
        app = firebase.initializeApp(config.firebaseConfig);
    }

    const messaging = firebase.messaging(app);

    // ── 3. Register the Service Worker ───────────────────────────────────
    async function registerServiceWorker() {
        try {
            // The SW is served from the root via a Django view with the
            // Service-Worker-Allowed: / header so it can control the full origin.
            const registration = await navigator.serviceWorker.register(
                '/firebase-messaging-sw.js',
                { scope: '/' }
            );

            // POST the firebase config to the SW so it can initialise Firebase there
            await navigator.serviceWorker.ready;
            registration.active && registration.active.postMessage({
                type: 'FIREBASE_CONFIG',
                config: config.firebaseConfig
            });

            return registration;
        } catch (err) {
            console.error('[FCM] Service Worker registration failed:', err);
            throw err;
        }
    }

    // ── 4. Request permission and get token ───────────────────────────────
    async function requestPermissionAndGetToken(swRegistration) {
        const permission = await Notification.requestPermission();

        if (permission !== 'granted') {
            console.info('[FCM] Notification permission denied by user.');
            return null;
        }

        try {
            const token = await messaging.getToken({
                vapidKey: config.vapidKey,
                serviceWorkerRegistration: swRegistration
            });

            if (token) {
                console.info('[FCM] FCM token obtained.');
                return token;
            } else {
                console.warn('[FCM] No token received — check VAPID key / service worker.');
                return null;
            }
        } catch (err) {
            console.error('[FCM] Error getting FCM token:', err);
            return null;
        }
    }

    // ── 5. Register token with Django backend ─────────────────────────────
    async function registerTokenWithBackend(token) {
        try {
            const csrfToken = document.cookie.match(/csrftoken=([^;]+)/);
            const csrf = csrfToken ? csrfToken[1] : '';

            const response = await fetch('/notifications/api/register-device-token/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf
                },
                body: JSON.stringify({
                    device_token: token,
                    platform: 'web'
                })
            });

            if (response.ok) {
                const data = await response.json();
                console.info('[FCM] Token registered with backend:', data.message);
                // Store token locally to detect rotation
                localStorage.setItem('fcm_token', token);
            } else {
                const err = await response.json();
                console.warn('[FCM] Backend registration failed:', err);
            }
        } catch (err) {
            console.error('[FCM] Error registering token with backend:', err);
        }
    }

    // ── 6. Handle foreground messages (app is open) ───────────────────────
    function setupForegroundMessageHandler() {
        messaging.onMessage(function (payload) {
            console.info('[FCM] Foreground message received:', payload);

            const title = (payload.notification && payload.notification.title)
                ? payload.notification.title
                : '📚 Reading Reminder';
            const body = (payload.notification && payload.notification.body)
                ? payload.notification.body
                : 'Time to read with your child!';

            // Use the existing NotificationToast system if available
            if (window.NotificationToast) {
                window.NotificationToast.info(`📚 ${body}`, 8000);
            } else {
                // Fallback: browser notification
                if (Notification.permission === 'granted') {
                    new Notification(title, {
                        body: body,
                        icon: '/static/images/foundation-logo.png'
                    });
                }
            }
        });
    }

    // ── 7. Token refresh handling ─────────────────────────────────────────
    // Firebase automatically refreshes tokens; we re-register on refresh
    // by comparing with localStorage on next load. No onTokenRefresh in JS SDK v9+.

    // ── 8. Main init ──────────────────────────────────────────────────────
    async function initPushNotifications() {
        try {
            const swRegistration = await registerServiceWorker();
            const token = await requestPermissionAndGetToken(swRegistration);

            if (token) {
                // Only register if token changed (avoid redundant API calls)
                const stored = localStorage.getItem('fcm_token');
                if (stored !== token) {
                    await registerTokenWithBackend(token);
                }
            }

            setupForegroundMessageHandler();
        } catch (err) {
            console.error('[FCM] Push notification init failed:', err);
        }
    }

    // Kick off after DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPushNotifications);
    } else {
        initPushNotifications();
    }

})();
