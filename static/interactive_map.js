/*!
 * ViamigoTravelAI Interactive Map Enhancements
 * Enhanced map functionality for 56 Italian cities with 9,930+ places
 * Mobile-responsive map controls and advanced interactions
 */

class ViamigoInteractiveMap {
    constructor() {
        this.map = null;
        this.markers = [];
        this.markerClusters = null;
        this.currentFilters = new Set();
        this.isFullscreen = false;
        this.initializeMapEnhancements();
    }

    // ==================== INITIALIZATION ====================
    initializeMapEnhancements() {
        // Wait for map to be available
        this.waitForMap().then(() => {
            this.enhanceMapControls();
            this.addMapFilters();
            this.addMapSearch();
            this.addLocationServices();
            this.addFullscreenToggle();
            this.optimizeForMobile();
            console.log('🗺️ Interactive map enhancements loaded');
        });
    }

    async waitForMap(maxAttempts = 30) {
        for (let i = 0; i < maxAttempts; i++) {
            if (window.map && typeof L !== 'undefined') {
                this.map = window.map;
                return;
            }
            await new Promise(resolve => setTimeout(resolve, 100));
        }
        throw new Error('Map not available after waiting');
    }

    // ==================== MAP CONTROLS ====================
    enhanceMapControls() {
        // Custom zoom control with better mobile support
        if (this.map) {
            // Remove default zoom control
            this.map.zoomControl.remove();
            
            // Add custom zoom control
            const customZoom = L.control({ position: 'bottomright' });
            
            customZoom.onAdd = function() {
                const div = L.DomUtil.create('div', 'custom-zoom-control');
                div.innerHTML = `
                    <div class="zoom-buttons bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                        <button id="zoom-in" class="zoom-btn block w-10 h-10 bg-gray-800 hover:bg-gray-700 text-white border-b border-gray-600 last:border-b-0 transition-colors flex items-center justify-center">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"/>
                            </svg>
                        </button>
                        <button id="zoom-out" class="zoom-btn block w-10 h-10 bg-gray-800 hover:bg-gray-700 text-white transition-colors flex items-center justify-center">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18 12H6"/>
                            </svg>
                        </button>
                    </div>
                `;
                
                // Prevent map events on control
                L.DomEvent.disableClickPropagation(div);
                
                return div;
            };
            
            customZoom.addTo(this.map);
            
            // Add event listeners
            document.addEventListener('click', (e) => {
                if (e.target.closest('#zoom-in')) {
                    this.map.zoomIn();
                }
                if (e.target.closest('#zoom-out')) {
                    this.map.zoomOut();
                }
            });
        }
    }

    // ==================== MAP FILTERS ====================
    addMapFilters() {
        if (!this.map) return;

        const filterControl = L.control({ position: 'topleft' });
        
        filterControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'map-filter-control');
            div.innerHTML = `
                <div class="filter-container bg-gray-800 rounded-lg shadow-lg p-3 max-w-xs">
                    <div class="filter-header flex items-center justify-between mb-2">
                        <span class="text-white text-sm font-medium">Filtri</span>
                        <button id="toggle-filters" class="text-gray-400 hover:text-white">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                            </svg>
                        </button>
                    </div>
                    <div id="filter-options" class="filter-options space-y-2">
                        <label class="flex items-center text-sm text-gray-300">
                            <input type="checkbox" class="filter-checkbox mr-2" data-type="restaurant" checked>
                            🍕 Ristoranti
                        </label>
                        <label class="flex items-center text-sm text-gray-300">
                            <input type="checkbox" class="filter-checkbox mr-2" data-type="attraction" checked>
                            🏛️ Attrazioni
                        </label>
                        <label class="flex items-center text-sm text-gray-300">
                            <input type="checkbox" class="filter-checkbox mr-2" data-type="hotel" checked>
                            🏨 Hotel
                        </label>
                        <label class="flex items-center text-sm text-gray-300">
                            <input type="checkbox" class="filter-checkbox mr-2" data-type="shop" checked>
                            🛍️ Shopping
                        </label>
                    </div>
                </div>
            `;
            
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        
        filterControl.addTo(this.map);
        
        // Add filter event listeners
        this.setupFilterEvents();
    }

    setupFilterEvents() {
        document.addEventListener('change', (e) => {
            if (e.target.classList.contains('filter-checkbox')) {
                const type = e.target.dataset.type;
                if (e.target.checked) {
                    this.currentFilters.add(type);
                } else {
                    this.currentFilters.delete(type);
                }
                this.updateMarkerVisibility();
            }
        });
        
        document.addEventListener('click', (e) => {
            if (e.target.closest('#toggle-filters')) {
                const options = document.getElementById('filter-options');
                const icon = e.target.closest('#toggle-filters').querySelector('svg');
                
                if (options.style.display === 'none') {
                    options.style.display = 'block';
                    icon.style.transform = 'rotate(0deg)';
                } else {
                    options.style.display = 'none';
                    icon.style.transform = 'rotate(-90deg)';
                }
            }
        });
    }

    updateMarkerVisibility() {
        // Update marker visibility based on current filters
        if (window.markers) {
            window.markers.forEach(marker => {
                const markerType = marker.options.type || 'attraction';
                if (this.currentFilters.size === 0 || this.currentFilters.has(markerType)) {
                    marker.addTo(this.map);
                } else {
                    this.map.removeLayer(marker);
                }
            });
        }
    }

    // ==================== MAP SEARCH ====================
    addMapSearch() {
        if (!this.map) return;

        const searchControl = L.control({ position: 'topright' });
        
        searchControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'map-search-control');
            div.innerHTML = `
                <div class="search-container bg-gray-800 rounded-lg shadow-lg">
                    <div class="search-input-container flex items-center p-2">
                        <svg class="w-4 h-4 text-gray-400 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                        </svg>
                        <input type="text" id="map-search-input" 
                               class="bg-transparent text-white text-sm placeholder-gray-400 outline-none flex-1" 
                               placeholder="Cerca sulla mappa...">
                        <button id="clear-search" class="text-gray-400 hover:text-white ml-2 hidden">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                            </svg>
                        </button>
                    </div>
                    <div id="map-search-results" class="search-results max-h-48 overflow-y-auto hidden border-t border-gray-600"></div>
                </div>
            `;
            
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        
        searchControl.addTo(this.map);
        
        this.setupMapSearchEvents();
    }

    setupMapSearchEvents() {
        const searchInput = document.getElementById('map-search-input');
        const clearButton = document.getElementById('clear-search');
        const resultsContainer = document.getElementById('map-search-results');
        
        if (!searchInput) return;
        
        let searchTimeout;
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            
            if (query.length > 0) {
                clearButton.classList.remove('hidden');
            } else {
                clearButton.classList.add('hidden');
                resultsContainer.classList.add('hidden');
                return;
            }
            
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                this.performMapSearch(query);
            }, 300);
        });
        
        clearButton.addEventListener('click', () => {
            searchInput.value = '';
            clearButton.classList.add('hidden');
            resultsContainer.classList.add('hidden');
        });
    }

    async performMapSearch(query) {
        try {
            const response = await fetch(`/api/cities/search?query=${encodeURIComponent(query)}&limit=5`);
            if (response.ok) {
                const data = await response.json();
                this.displayMapSearchResults(data.places || []);
            }
        } catch (error) {
            console.error('Map search error:', error);
        }
    }

    displayMapSearchResults(results) {
        const resultsContainer = document.getElementById('map-search-results');
        if (!resultsContainer) return;
        
        if (results.length === 0) {
            resultsContainer.classList.add('hidden');
            return;
        }
        
        resultsContainer.innerHTML = results.map(place => `
            <div class="search-result-item p-3 hover:bg-gray-700 cursor-pointer border-b border-gray-600 last:border-b-0" 
                 data-name="${place.name}" data-city="${place.city}">
                <div class="text-white text-sm font-medium">${place.name}</div>
                <div class="text-gray-400 text-xs">${place.city}</div>
            </div>
        `).join('');
        
        resultsContainer.classList.remove('hidden');
        
        // Add click handlers
        resultsContainer.addEventListener('click', (e) => {
            const item = e.target.closest('.search-result-item');
            if (item) {
                const name = item.dataset.name;
                const city = item.dataset.city;
                this.zoomToPlace(name, city);
                resultsContainer.classList.add('hidden');
            }
        });
    }

    // ==================== LOCATION SERVICES ====================
    addLocationServices() {
        if (!this.map || !navigator.geolocation) return;
        
        const locationControl = L.control({ position: 'bottomleft' });
        
        locationControl.onAdd = function() {
            const div = L.DomUtil.create('div', 'location-control');
            div.innerHTML = `
                <button id="locate-me" class="location-btn w-10 h-10 bg-gray-800 hover:bg-gray-700 text-white rounded-lg shadow-lg transition-colors flex items-center justify-center">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                </button>
            `;
            
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        
        locationControl.addTo(this.map);
        
        document.addEventListener('click', (e) => {
            if (e.target.closest('#locate-me')) {
                this.locateUser();
            }
        });
    }

    locateUser() {
        const button = document.getElementById('locate-me');
        if (!button) return;
        
        // Show loading state
        button.innerHTML = `
            <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
        `;
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                this.map.setView([latitude, longitude], 15);
                
                // Add user location marker
                if (this.userLocationMarker) {
                    this.map.removeLayer(this.userLocationMarker);
                }
                
                this.userLocationMarker = L.marker([latitude, longitude], {
                    icon: L.divIcon({
                        className: 'user-location-marker',
                        html: '<div class="w-4 h-4 bg-blue-500 rounded-full border-2 border-white shadow-lg"></div>',
                        iconSize: [16, 16],
                        iconAnchor: [8, 8]
                    })
                }).addTo(this.map);
                
                // Reset button
                button.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                `;
            },
            (error) => {
                console.error('Geolocation error:', error);
                button.innerHTML = `
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                    </svg>
                `;
            }
        );
    }

    // ==================== MOBILE OPTIMIZATIONS ====================
    optimizeForMobile() {
        if (!this.map) return;
        
        // Disable map zooming on double tap to prevent conflicts
        this.map.doubleClickZoom.disable();
        
        // Add custom double tap handling
        let tapTimeout;
        let lastTap = 0;
        
        this.map.on('click', (e) => {
            const now = Date.now();
            if (now - lastTap < 300) {
                clearTimeout(tapTimeout);
                this.map.zoomIn();
            } else {
                tapTimeout = setTimeout(() => {
                    // Single tap logic if needed
                }, 300);
            }
            lastTap = now;
        });
        
        // Improve touch interactions
        if ('ontouchstart' in window) {
            this.map.getContainer().style.touchAction = 'pan-x pan-y';
        }
    }

    // ==================== UTILITY METHODS ====================
    zoomToPlace(name, city) {
        // Find and zoom to a specific place
        if (window.markers) {
            const marker = window.markers.find(m => 
                m.options.title?.includes(name) || 
                m.options.alt?.includes(name)
            );
            
            if (marker) {
                this.map.setView(marker.getLatLng(), 16);
                marker.openPopup();
            }
        }
    }

    addFullscreenToggle() {
        // Add fullscreen toggle for better mobile experience
        const fullscreenControl = L.control({ position: 'bottomright' });
        
        fullscreenControl.onAdd = () => {
            const div = L.DomUtil.create('div', 'fullscreen-control');
            div.innerHTML = `
                <button id="fullscreen-toggle" class="fullscreen-btn w-10 h-10 bg-gray-800 hover:bg-gray-700 text-white rounded-lg shadow-lg transition-colors flex items-center justify-center mb-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"/>
                    </svg>
                </button>
            `;
            
            L.DomEvent.disableClickPropagation(div);
            return div;
        };
        
        fullscreenControl.addTo(this.map);
        
        document.addEventListener('click', (e) => {
            if (e.target.closest('#fullscreen-toggle')) {
                this.toggleFullscreen();
            }
        });
    }

    toggleFullscreen() {
        const mapContainer = this.map.getContainer().closest('.page');
        
        if (!this.isFullscreen) {
            mapContainer.style.position = 'fixed';
            mapContainer.style.top = '0';
            mapContainer.style.left = '0';
            mapContainer.style.width = '100vw';
            mapContainer.style.height = '100vh';
            mapContainer.style.zIndex = '9999';
            this.isFullscreen = true;
        } else {
            mapContainer.style.position = '';
            mapContainer.style.top = '';
            mapContainer.style.left = '';
            mapContainer.style.width = '';
            mapContainer.style.height = '';
            mapContainer.style.zIndex = '';
            this.isFullscreen = false;
        }
        
        // Trigger map resize
        setTimeout(() => {
            this.map.invalidateSize();
        }, 100);
    }
}

// Auto-initialize when map is available
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.viamigoMap = new ViamigoInteractiveMap();
    });
} else {
    window.viamigoMap = new ViamigoInteractiveMap();
}

// Export for global access
window.ViamigoInteractiveMap = ViamigoInteractiveMap;