/// <reference lib="WebWorker" />
import { cleanupOutdatedCaches, precacheAndRoute } from 'workbox-precaching'
import { registerRoute, NavigationRoute } from 'workbox-routing'
import { NetworkFirst, CacheFirst, StaleWhileRevalidate } from 'workbox-strategies'
import { ExpirationPlugin } from 'workbox-expiration'
import { CacheableResponsePlugin } from 'workbox-cacheable-response'

declare const self: ServiceWorkerGlobalScope

// Injected by vite-plugin-pwa at build time
precacheAndRoute(self.__WB_MANIFEST)
cleanupOutdatedCaches()

// App Shell — SPA navigation fallback (NetworkFirst with offline fallback)
registerRoute(
  new NavigationRoute(
    new NetworkFirst({
      cacheName: 'igs-navigation',
      plugins: [
        new ExpirationPlugin({ maxEntries: 1, maxAgeSeconds: 60 * 60 * 24 }),
      ],
      networkTimeoutSeconds: 5,
    })
  )
)

// API responses — NetworkFirst so fresh data is always preferred
registerRoute(
  ({ url }) => url.pathname.startsWith('/api/'),
  new NetworkFirst({
    cacheName: 'igs-api',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 100, maxAgeSeconds: 60 * 5 }),
    ],
    networkTimeoutSeconds: 10,
  })
)

// Static assets (JS, CSS, fonts) — CacheFirst after initial fetch
registerRoute(
  ({ request }) =>
    request.destination === 'script' ||
    request.destination === 'style' ||
    request.destination === 'font',
  new CacheFirst({
    cacheName: 'igs-static',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 60, maxAgeSeconds: 60 * 60 * 24 * 30 }),
    ],
  })
)

// Images — StaleWhileRevalidate
registerRoute(
  ({ request }) => request.destination === 'image',
  new StaleWhileRevalidate({
    cacheName: 'igs-images',
    plugins: [
      new CacheableResponsePlugin({ statuses: [0, 200] }),
      new ExpirationPlugin({ maxEntries: 50, maxAgeSeconds: 60 * 60 * 24 * 7 }),
    ],
  })
)

// Skip waiting so updates activate immediately after install
self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') {
    self.skipWaiting()
  }
})
