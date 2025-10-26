/*!
 * ViamigoTravelAI Service Worker
 * Offline capabilities for 9,930+ places across 56 Italian cities
 * Enables PWA features, caching, and offline functionality
 */

const CACHE_NAME = 'viamigo-travel-v1.0';
const STATIC_CACHE_NAME = 'viamigo-static-v1.0';
const DATA_CACHE_NAME = 'viamigo-data-v1.0';

// Resources to cache for offline access
const STATIC_RESOURCES = [
    '/',
    '/static/index.html',
    '/static/ux_enhancements.js',
    '/static/performance_dashboard.html',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
    'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Poppins:wght@700&display=swap'
];

// API endpoints to cache
const API_ENDPOINTS = [
    '/api/cities/search',
    '/api/get_city_attractions',
    '/plan_ai_powered',
    '/api/performance/health'
];

// Install event - cache static resources
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        Promise.all([
            // Cache static resources
            caches.open(STATIC_CACHE_NAME).then((cache) => {
                console.log('📦 Caching static resources');
                return cache.addAll(STATIC_RESOURCES.filter(url => 
                    !url.startsWith('https://cdn.') && !url.startsWith('https://unpkg.')
                ));
            }),
            
            // Cache external CDN resources separately (they might fail)
            caches.open(STATIC_CACHE_NAME).then((cache) => {
                const cdnResources = STATIC_RESOURCES.filter(url => 
                    url.startsWith('https://cdn.') || url.startsWith('https://unpkg.') || url.startsWith('https://fonts.')
                );
                
                return Promise.allSettled(
                    cdnResources.map(url => 
                        cache.add(url).catch(err => 
                            console.warn(`⚠️ Failed to cache ${url}:`, err)
                        )
                    )
                );
            })
        ])
    );
    
    // Skip waiting to activate immediately
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activated');
    
    event.waitUntil(
        Promise.all([
            // Clean up old caches
            caches.keys().then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && 
                            cacheName !== STATIC_CACHE_NAME && 
                            cacheName !== DATA_CACHE_NAME) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            
            // Claim all clients
            self.clients.claim()
        ])
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Handle different types of requests
    if (request.method !== 'GET') {
        return;
    }
    
    // API requests - cache with network first strategy
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(handleApiRequest(request));
        return;
    }
    
    // Static resources - cache first strategy
    if (isStaticResource(url)) {
        event.respondWith(handleStaticRequest(request));
        return;
    }
    
    // HTML pages - network first with cache fallback
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(handleHtmlRequest(request));
        return;
    }
    
    // Default - network with cache fallback
    event.respondWith(handleDefaultRequest(request));
});

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
    const url = new URL(request.url);
    
    try {
        // Try network first for fresh data
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            // Cache successful API responses
            const cache = await caches.open(DATA_CACHE_NAME);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
    } catch (error) {
        console.log('🌐 Network failed for API, trying cache:', url.pathname);
        
        // Fallback to cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            // Add offline indicator header
            const headers = new Headers(cachedResponse.headers);
            headers.set('X-Served-From', 'cache');
            
            return new Response(cachedResponse.body, {
                status: cachedResponse.status,
                statusText: cachedResponse.statusText,
                headers: headers
            });
        }
        
        // Return offline fallback for specific APIs
        return createOfflineFallback(url.pathname);
    }
}

// Handle static resources with cache-first strategy
async function handleStaticRequest(request) {
    const cachedResponse = await caches.match(request);
    
    if (cachedResponse) {
        return cachedResponse;
    }
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('❌ Failed to fetch static resource:', request.url);
        return new Response('Resource not available offline', { status: 404 });
    }
}

// Handle HTML requests with network-first strategy
async function handleHtmlRequest(request) {
    try {
        const networkResponse = await fetch(request);
        
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
            return networkResponse;
        }
        
        throw new Error('Network response not ok');
    } catch (error) {
        console.log('🌐 Network failed for HTML, trying cache');
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline page fallback
        return caches.match('/static/index.html') || 
               new Response('App not available offline', { 
                   status: 404,
                   headers: { 'Content-Type': 'text/html' }
               });
    }
}

// Handle default requests
async function handleDefaultRequest(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        const cachedResponse = await caches.match(request);
        return cachedResponse || new Response('Not available offline', { status: 404 });
    }
}

// Check if resource is static
function isStaticResource(url) {
    return url.pathname.startsWith('/static/') || 
           url.hostname.includes('cdn.') ||
           url.hostname.includes('unpkg.') ||
           url.hostname.includes('fonts.') ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.jpeg') ||
           url.pathname.endsWith('.gif') ||
           url.pathname.endsWith('.svg');
}

// Create offline fallback responses
function createOfflineFallback(pathname) {
    if (pathname.includes('/api/cities/search')) {
        return new Response(JSON.stringify({
            cities: [
                'Roma', 'Milano', 'Napoli', 'Torino', 'Palermo', 'Genova', 
                'Bologna', 'Firenze', 'Bari', 'Catania', 'Venezia', 'Verona'
            ],
            places: [],
            offline: true
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    if (pathname.includes('/api/get_city_attractions')) {
        return new Response(JSON.stringify({
            attractions: [],
            message: 'Dati non disponibili offline',
            offline: true
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    if (pathname.includes('/plan_ai_powered')) {
        return new Response(JSON.stringify({
            itinerary: [],
            message: 'Pianificazione non disponibile offline. Connettiti a internet per pianificare nuovi itinerari.',
            offline: true
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    if (pathname.includes('/api/performance/health')) {
        return new Response(JSON.stringify({
            status: 'offline',
            message: 'Modalità offline attiva',
            timestamp: Date.now()
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
    }
    
    // Default offline response
    return new Response(JSON.stringify({
        error: 'Service not available offline',
        message: 'Questa funzionalità richiede una connessione internet',
        offline: true
    }), {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
    });
}

// Handle background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('🔄 Background sync triggered:', event.tag);
    
    if (event.tag === 'sync-itinerary') {
        event.waitUntil(syncOfflineItineraries());
    }
    
    if (event.tag === 'sync-preferences') {
        event.waitUntil(syncOfflinePreferences());
    }
});

// Sync offline itineraries when back online
async function syncOfflineItineraries() {
    try {
        // Get offline itineraries from IndexedDB
        const db = await openIndexedDB();
        const transaction = db.transaction(['itineraries'], 'readonly');
        const store = transaction.objectStore('itineraries');
        const itineraries = await getAllFromStore(store);
        
        // Sync each offline itinerary
        for (const itinerary of itineraries) {
            if (itinerary.offline) {
                try {
                    await fetch('/api/sync-itinerary', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(itinerary)
                    });
                    
                    // Mark as synced
                    itinerary.offline = false;
                    await saveToIndexedDB('itineraries', itinerary);
                    
                    console.log('✅ Itinerary synced:', itinerary.id);
                } catch (error) {
                    console.error('❌ Failed to sync itinerary:', error);
                }
            }
        }
    } catch (error) {
        console.error('❌ Sync failed:', error);
    }
}

// Sync offline preferences when back online
async function syncOfflinePreferences() {
    try {
        // Implementation for syncing user preferences
        console.log('🔄 Syncing offline preferences...');
    } catch (error) {
        console.error('❌ Preference sync failed:', error);
    }
}

// IndexedDB helpers
function openIndexedDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('ViamigoOfflineDB', 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

function getAllFromStore(store) {
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

function saveToIndexedDB(storeName, data) {
    return new Promise(async (resolve, reject) => {
        try {
            const db = await openIndexedDB();
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.put(data);
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
        } catch (error) {
            reject(error);
        }
    });
}

// Message handling for communication with main thread
self.addEventListener('message', (event) => {
    const { type, data } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'CACHE_ITINERARY':
            cacheItinerary(data);
            break;
            
        case 'CLEAR_CACHE':
            clearAllCaches();
            break;
            
        case 'GET_CACHE_SIZE':
            getCacheSize().then(size => {
                event.ports[0].postMessage({ type: 'CACHE_SIZE', size });
            });
            break;
    }
});

// Cache itinerary data
async function cacheItinerary(itinerary) {
    try {
        const cache = await caches.open(DATA_CACHE_NAME);
        const response = new Response(JSON.stringify(itinerary), {
            headers: { 'Content-Type': 'application/json' }
        });
        await cache.put(`/offline/itinerary/${itinerary.id}`, response);
        console.log('✅ Itinerary cached for offline use');
    } catch (error) {
        console.error('❌ Failed to cache itinerary:', error);
    }
}

// Clear all caches
async function clearAllCaches() {
    try {
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
        );
        console.log('🗑️ All caches cleared');
    } catch (error) {
        console.error('❌ Failed to clear caches:', error);
    }
}

// Get total cache size
async function getCacheSize() {
    try {
        let totalSize = 0;
        const cacheNames = await caches.keys();
        
        for (const cacheName of cacheNames) {
            const cache = await caches.open(cacheName);
            const requests = await cache.keys();
            
            for (const request of requests) {
                const response = await cache.match(request);
                if (response) {
                    const blob = await response.blob();
                    totalSize += blob.size;
                }
            }
        }
        
        return Math.round(totalSize / 1024 / 1024 * 100) / 100; // MB
    } catch (error) {
        console.error('❌ Failed to calculate cache size:', error);
        return 0;
    }
}

console.log('🚀 ViamigoTravelAI Service Worker loaded successfully');