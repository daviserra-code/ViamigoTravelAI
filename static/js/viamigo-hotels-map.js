/**
 * Viamigo Hotels Map Integration
 * Adds hotel markers with category-based styling to the map
 * 
 * Features:
 * - Hotel markers with custom icons by category
 * - Marker clustering for better performance
 * - Click to show hotel details
 * - Toggle layer on/off
 * - Graceful degradation for cities without hotels
 * 
 * @requires Leaflet.js
 * @requires Leaflet.markercluster.js
 * @requires viamigo-hotels-api.js
 */

class ViamigoHotelsMap {
    constructor(mapInstance) {
        this.map = mapInstance;
        this.hotelsLayer = null;
        this.markerClusterGroup = null;
        this.currentCity = null;
        this.hotelsData = [];
        this.isVisible = false;
        
        this.init();
    }
    
    init() {
        // Create marker cluster group for better performance
        if (typeof L.markerClusterGroup !== 'undefined') {
            this.markerClusterGroup = L.markerClusterGroup({
                maxClusterRadius: 50,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true,
                iconCreateFunction: (cluster) => {
                    const count = cluster.getChildCount();
                    let size = 'small';
                    if (count > 10) size = 'medium';
                    if (count > 25) size = 'large';
                    
                    return L.divIcon({
                        html: `<div class="hotel-cluster-${size}"><span>${count}</span></div>`,
                        className: 'hotel-marker-cluster',
                        iconSize: L.point(40, 40)
                    });
                }
            });
        } else {
            // Fallback to regular layer group
            this.markerClusterGroup = L.layerGroup();
        }
        
        console.log('🏨 Hotels map integration initialized');
    }
    
    /**
     * Get category-based icon for hotel marker
     */
    getHotelIcon(hotel) {
        const rating = hotel.rating || hotel.average_score || 0;
        
        // Determine category based on rating
        let category = 'budget';
        let color = '#6b7280'; // gray-500
        let iconHtml = '🏨';
        
        if (rating >= 9.0) {
            category = 'luxury';
            color = '#f59e0b'; // amber-500 (gold)
            iconHtml = '⭐';
        } else if (rating >= 8.5) {
            category = 'premium';
            color = '#3b82f6'; // blue-500
            iconHtml = '🏨';
        } else if (rating >= 8.0) {
            category = 'mid-range';
            color = '#10b981'; // green-500
            iconHtml = '🏨';
        }
        
        return L.divIcon({
            className: 'custom-marker hotel-marker',
            html: `
                <div class="hotel-marker-content" style="background-color: ${color};" data-category="${category}">
                    <span class="hotel-icon">${iconHtml}</span>
                    ${rating > 0 ? `<span class="hotel-rating">${rating.toFixed(1)}</span>` : ''}
                </div>
            `,
            iconSize: [36, 36],
            iconAnchor: [18, 18],
            popupAnchor: [0, -18]
        });
    }
    
    /**
     * Create popup content for hotel marker
     */
    createHotelPopup(hotel) {
        const rating = hotel.rating || hotel.average_score || 0;
        const reviews = hotel.review_count || hotel.total_reviews || 0;
        const hotelName = hotel.name || hotel.hotel_name;
        const hotelAddress = hotel.address || hotel.hotel_address;
        
        // Determine category label
        let categoryLabel = 'Budget';
        let categoryClass = 'bg-gray-100 text-gray-700';
        
        if (rating >= 9.0) {
            categoryLabel = 'Luxury';
            categoryClass = 'bg-amber-100 text-amber-700';
        } else if (rating >= 8.5) {
            categoryLabel = 'Premium';
            categoryClass = 'bg-blue-100 text-blue-700';
        } else if (rating >= 8.0) {
            categoryLabel = 'Mid-Range';
            categoryClass = 'bg-green-100 text-green-700';
        }
        
        return `
            <div class="hotel-popup max-w-xs">
                <div class="flex items-start justify-between mb-2">
                    <h3 class="font-bold text-sm text-gray-900 flex-1 pr-2">${hotelName}</h3>
                    <span class="text-xs px-2 py-1 rounded ${categoryClass} whitespace-nowrap">${categoryLabel}</span>
                </div>
                
                ${rating > 0 ? `
                    <div class="flex items-center gap-2 mb-2">
                        <span class="text-lg font-bold text-violet-600">${rating.toFixed(1)}</span>
                        <div class="flex-1">
                            <div class="flex items-center">
                                ${this.renderStars(rating)}
                            </div>
                            <span class="text-xs text-gray-600">${reviews.toLocaleString()} reviews</span>
                        </div>
                    </div>
                ` : ''}
                
                ${hotelAddress ? `
                    <p class="text-xs text-gray-600 mb-2">
                        <span class="inline-block mr-1">📍</span>
                        ${hotelAddress}
                    </p>
                ` : ''}
                
                <div class="flex gap-2 mt-3 mb-2">
                    <button 
                        onclick="viamigoHotelsMapInstance.startRouteFromHotel('${hotelName.replace(/'/g, "\\'")}', '${hotel.city}')"
                        class="flex-1 text-xs bg-violet-500 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition"
                        title="Start your route from this hotel"
                    >
                        🚀 Start Here
                    </button>
                    <button 
                        onclick="viamigoHotelsMapInstance.endRouteAtHotel('${hotelName.replace(/'/g, "\\'")}', '${hotel.city}')"
                        class="flex-1 text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded transition"
                        title="End your route at this hotel"
                    >
                        🏁 End Here
                    </button>
                </div>
                <div class="flex gap-2">
                    <button 
                        onclick="viamigoHotelsMapInstance.showHotelDetails('${hotelName.replace(/'/g, "\\'")}', '${hotel.city}')"
                        class="flex-1 text-xs bg-gray-600 hover:bg-gray-700 text-white px-3 py-1.5 rounded transition"
                        title="View full hotel details"
                    >
                        ℹ️ Details
                    </button>
                </div>
            </div>
        `;
    }
    
    /**
     * Render star rating
     */
    renderStars(rating) {
        const fullStars = Math.floor(rating / 2);
        const halfStar = (rating / 2) % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
        
        let stars = '';
        for (let i = 0; i < fullStars; i++) stars += '⭐';
        if (halfStar) stars += '✨';
        for (let i = 0; i < emptyStars; i++) stars += '☆';
        
        return `<span class="text-xs">${stars}</span>`;
    }
    
    /**
     * Extract city name from a location string
     * E.g., "Corso Buenos Aires, Milano" -> "Milano"
     */
    extractCityName(location) {
        if (!location) return 'Milan'; // Default fallback
        
        // Convert to string if needed
        location = String(location);
        
        // If location contains a comma, take the last part (usually the city)
        if (location.includes(',')) {
            const parts = location.split(',');
            const city = parts[parts.length - 1].trim();
            return city || 'Milan'; // Fallback if empty
        }
        
        return location.trim() || 'Milan'; // Fallback if empty
    }
    
    /**
     * Load and display hotels for a city
     */
    async loadHotels(city) {
        if (!city) {
            console.warn('🏨 No city specified for hotel loading, using Milan as default');
            city = 'Milan';
        }
        
        // Extract just the city name if location string includes address
        city = this.extractCityName(city);
        
        // Extra safety check
        if (!city || typeof city !== 'string') {
            console.warn('🏨 Invalid city name, using Milan as default');
            city = 'Milan';
        }
        
        this.currentCity = city;
        
        try {
            // Check availability first
            const availability = await window.viamigoHotels.checkAvailability(city);
            
            if (!availability.available) {
                console.log(`🏨 No hotels available for ${city}`);
                this.clearHotels();
                return;
            }
            
            console.log(`🏨 Loading hotels for ${city}...`);
            
            // Fetch nearby hotels (within city bounds)
            // search(city, query, minRating, limit)
            const response = await window.viamigoHotels.search(
                city,      // city parameter
                '',        // no query filter
                8.5,       // min rating 8.5+ for premium quality only
                30         // fetch 30 to have selection
            );
            
            if (response.success && response.hotels.length > 0) {
                // Filter and sort hotels by rating, show only top 15 to avoid clutter
                this.hotelsData = response.hotels
                    .filter(h => h.latitude && h.longitude && h.rating >= 8.5)
                    .sort((a, b) => (b.rating || 0) - (a.rating || 0))
                    .slice(0, 15); // Show max 15 premium hotels
                
                console.log(`✅ Loaded ${this.hotelsData.length} premium hotels (8.5+)`);
                this.renderHotels();
            } else {
                console.log(`🏨 No hotels found for ${city}`);
                this.clearHotels();
            }
            
        } catch (error) {
            console.error('❌ Error loading hotels:', error);
            this.clearHotels();
        }
    }
    
    /**
     * Render hotel markers on map
     */
    renderHotels() {
        // Clear existing markers
        this.markerClusterGroup.clearLayers();
        
        if (this.hotelsData.length === 0) {
            console.log('🏨 No hotels to render');
            return;
        }
        
        console.log(`🏨 Rendering ${this.hotelsData.length} hotel markers...`);
        
        let renderedCount = 0;
        this.hotelsData.forEach(hotel => {
            if (!hotel.latitude || !hotel.longitude) {
                console.warn(`🏨 Skipping hotel without coordinates: ${hotel.name || hotel.hotel_name}`);
                return;
            }
            
            const icon = this.getHotelIcon(hotel);
            const marker = L.marker([hotel.latitude, hotel.longitude], { icon });
            
            // Add popup
            const popupContent = this.createHotelPopup(hotel);
            marker.bindPopup(popupContent, {
                maxWidth: 300,
                className: 'hotel-marker-popup'
            });
            
            // Add to cluster group
            this.markerClusterGroup.addLayer(marker);
            renderedCount++;
        });
        
        console.log(`✅ Rendered ${renderedCount} hotel markers (${this.hotelsData.length - renderedCount} skipped without coords)`);
        
        // Add to map if visible
        if (this.isVisible && !this.map.hasLayer(this.markerClusterGroup)) {
            this.map.addLayer(this.markerClusterGroup);
            console.log('🏨 Hotels layer added to map');
        }
    }
    
    /**
     * Clear all hotel markers
     */
    clearHotels() {
        if (this.markerClusterGroup) {
            this.markerClusterGroup.clearLayers();
        }
        this.hotelsData = [];
        console.log('🏨 Cleared hotel markers');
    }
    
    /**
     * Show hotel layer
     */
    async show() {
        // If no hotels loaded yet and we have a city, load them
        if (this.hotelsData.length === 0 && this.currentCity) {
            console.log('🏨 No hotels loaded, loading now...');
            await this.loadHotels(this.currentCity);
        } else if (this.hotelsData.length === 0) {
            // Try to get city from window, extract just city name
            let city = window.currentCityName || 'Milan';
            city = this.extractCityName(city);
            console.log(`🏨 No city set, trying ${city}...`);
            await this.loadHotels(city);
        }
        
        if (!this.map.hasLayer(this.markerClusterGroup)) {
            this.map.addLayer(this.markerClusterGroup);
        }
        this.isVisible = true;
        console.log('🏨 Hotels layer shown');
    }
    
    /**
     * Hide hotel layer
     */
    hide() {
        if (this.map.hasLayer(this.markerClusterGroup)) {
            this.map.removeLayer(this.markerClusterGroup);
        }
        this.isVisible = false;
        console.log('🏨 Hotels layer hidden');
    }
    
    /**
     * Toggle hotel layer visibility
     */
    async toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            await this.show();
        }
        return this.isVisible;
    }
    
    /**
     * Start route from hotel (integration with main app)
     */
    async startRouteFromHotel(hotelName, city) {
        console.log(`🚀 Starting route from hotel: ${hotelName}`);
        
        try {
            const response = await window.viamigoHotels.getDetails(hotelName, city);
            
            if (response.success && response.hotel) {
                const hotel = response.hotel;
                
                // Update start location input
                const startInput = document.getElementById('start-location');
                if (startInput) {
                    startInput.value = hotel.hotel_name;
                }
                
                // Close popup
                this.map.closePopup();
                
                // Show success toast
                this.showToast(`🏨 Starting route from ${hotel.hotel_name}`, 'success');
                
                // Trigger route generation if user wants
                if (confirm(`Start your route from ${hotel.hotel_name}?\n\nThis will use the hotel as your starting point.`)) {
                    // Trigger the main route generation
                    if (typeof generateRoute === 'function') {
                        generateRoute();
                    }
                }
            }
        } catch (error) {
            console.error('❌ Error starting route from hotel:', error);
            this.showToast('Failed to start route from hotel', 'error');
        }
    }
    
    /**
     * End route at hotel (3.2)
     */
    async endRouteAtHotel(hotelName, city) {
        console.log(`🏁 Ending route at hotel: ${hotelName}`);
        
        try {
            const response = await window.viamigoHotels.getDetails(hotelName, city);
            
            if (response.success && response.hotel) {
                const hotel = response.hotel;
                
                // Update end location input
                const endInput = document.getElementById('end-location');
                if (endInput) {
                    endInput.value = hotel.hotel_name;
                }
                
                // Close popup
                this.map.closePopup();
                
                // Show success toast
                this.showToast(`🏁 Ending route at ${hotel.hotel_name}`, 'success');
                
                // Trigger route generation if user wants
                if (confirm(`End your route at ${hotel.hotel_name}?\n\nThis will use the hotel as your destination.`)) {
                    // Trigger the main route generation
                    if (typeof generateRoute === 'function') {
                        generateRoute();
                    }
                }
            }
        } catch (error) {
            console.error('❌ Error ending route at hotel:', error);
            this.showToast('Failed to end route at hotel', 'error');
        }
    }
    
    /**
     * Show hotel details (integration with UI)
     */
    async showHotelDetails(hotelName, city) {
        console.log(`ℹ️ Showing details for: ${hotelName}`);
        
        // Close map popup
        this.map.closePopup();
        
        // Trigger the existing hotel details modal from viamigo-hotels-ui.js
        if (window.viamigoHotelsUI && typeof window.viamigoHotelsUI.showHotelDetails === 'function') {
            window.viamigoHotelsUI.showHotelDetails(hotelName, city);
        } else {
            // Fallback: open search modal with pre-filled hotel name
            const searchInput = document.getElementById('hotel-search-input');
            if (searchInput) {
                searchInput.value = hotelName;
                const searchModal = document.getElementById('hotel-search-modal');
                if (searchModal) {
                    searchModal.classList.remove('hidden');
                }
            }
        }
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Check if toast function exists
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
            return;
        }
        
        // Fallback: simple alert
        console.log(`Toast: ${message}`);
    }
    
    /**
     * Update hotels when city changes
     */
    updateCity(city) {
        if (city !== this.currentCity) {
            console.log(`🏨 City changed: ${this.currentCity} → ${city}`);
            this.loadHotels(city);
        }
    }
    
    /**
     * Show accommodation suggestions for route (Phase 3.3)
     * @param {Array} routePoints - Array of {lat, lng, name} objects
     */
    async showAccommodationSuggestions(routePoints) {
        if (!routePoints || routePoints.length === 0) {
            console.warn('🏨 No route points provided for accommodation suggestions');
            return;
        }
        
        console.log(`🏨 Finding accommodation suggestions for route with ${routePoints.length} stops`);
        console.log('🏨 Route points:', routePoints);
        
        try {
            // Call the accommodation suggestions API
            console.log('🏨 Calling /api/hotels/accommodation-suggestions...');
            const response = await fetch('/api/hotels/accommodation-suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ route_points: routePoints })
            });
            
            console.log('🏨 API response status:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('🏨 API error:', errorText);
                throw new Error(`HTTP ${response.status}: ${errorText}`);
            }
            
            const data = await response.json();
            console.log('🏨 API response data:', data);
            
            if (data.success && data.suggestions && data.suggestions.length > 0) {
                console.log(`🏨 Got ${data.suggestions.length} suggestions, rendering panel...`);
                this.renderAccommodationPanel(data.suggestions, data.city);
            } else {
                console.log('🏨 No accommodation suggestions available:', data);
            }
        } catch (error) {
            console.error('❌ Error fetching accommodation suggestions:', error);
        }
    }
    
    /**
     * Render accommodation suggestions panel
     */
    renderAccommodationPanel(hotels, city) {
        console.log(`🏨 Rendering accommodation panel for ${hotels.length} hotels in ${city}`);
        console.log('🏨 Hotels data:', hotels);
        
        // Find or create the suggestions container
        let container = document.getElementById('accommodation-suggestions');
        
        if (!container) {
            // Create container after timeline
            const timeline = document.querySelector('.timeline');
            console.log('🏨 Looking for .timeline element:', !!timeline);
            
            if (!timeline) {
                console.error('🏨 Timeline container (.timeline) not found! Cannot render accommodation panel.');
                console.log('🏨 Available elements:', document.querySelectorAll('*[class*="timeline"]'));
                return;
            }
            
            console.log('🏨 Creating accommodation suggestions container');
            container = document.createElement('div');
            container.id = 'accommodation-suggestions';
            container.className = 'mt-4 p-4 bg-gray-800 rounded-lg border border-gray-700';
            timeline.parentElement.appendChild(container);
            console.log('🏨 Container created and appended');
        } else {
            console.log('🏨 Reusing existing container');
        }
        
        // Render panel HTML
        const limitedHotels = hotels.slice(0, 5); // Show max 5
        
        container.innerHTML = `
            <div class="flex items-center justify-between mb-3">
                <h3 class="text-lg font-semibold text-white flex items-center gap-2">
                    💡 Where to Stay Near Your Route
                </h3>
                <button 
                    onclick="document.getElementById('accommodation-suggestions').remove()"
                    class="text-gray-400 hover:text-white transition"
                    title="Close"
                >
                    ✕
                </button>
            </div>
            
            <p class="text-sm text-gray-400 mb-4">
                Hotels optimally positioned for your ${city} itinerary
            </p>
            
            <div class="space-y-3">
                ${limitedHotels.map((hotel, index) => `
                    <div class="bg-gray-700 rounded-lg p-3 hover:bg-gray-600 transition">
                        <div class="flex items-start justify-between">
                            <div class="flex-1">
                                <div class="flex items-center gap-2 mb-1">
                                    ${hotel.category === 'luxury' ? '⭐' : '🏨'}
                                    <span class="font-semibold text-white">${hotel.name}</span>
                                    ${index === 0 ? '<span class="text-xs bg-yellow-500 text-black px-2 py-0.5 rounded ml-2">🏆 Best Position</span>' : ''}
                                </div>
                                <div class="text-sm text-gray-300 mb-2">
                                    ${hotel.rating}/10 • ${hotel.review_count} reviews
                                </div>
                                <div class="text-xs text-gray-400 mb-2">
                                    📍 ${hotel.avg_distance_km.toFixed(2)}km average from route stops
                                </div>
                            </div>
                        </div>
                        <div class="flex gap-2 mt-2">
                            <button 
                                onclick="viamigoHotelsMapInstance.startRouteFromHotel('${hotel.name.replace(/'/g, "\\'")}', '${city}')"
                                class="flex-1 text-xs bg-violet-500 hover:bg-violet-600 text-white px-3 py-1.5 rounded transition"
                            >
                                🚀 Start Here
                            </button>
                            <button 
                                onclick="viamigoHotelsMapInstance.endRouteAtHotel('${hotel.name.replace(/'/g, "\\'")}', '${city}')"
                                class="flex-1 text-xs bg-green-500 hover:bg-green-600 text-white px-3 py-1.5 rounded transition"
                            >
                                🏁 End Here
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        console.log(`🏨 Rendered accommodation panel with ${limitedHotels.length} suggestions`);
    }
}

// Initialize hotels map when map is ready
let viamigoHotelsMapInstance = null;

function initializeHotelsMap(mapInstance) {
    console.log('🏨 initializeHotelsMap called');
    
    if (!mapInstance) {
        console.error('❌ Cannot initialize hotels map: map instance is null');
        return null;
    }
    
    if (!window.viamigoHotels) {
        console.error('❌ Cannot initialize hotels map: viamigoHotels API not loaded');
        console.log('Available window properties:', Object.keys(window).filter(k => k.includes('hotel')));
        return null;
    }
    
    try {
        viamigoHotelsMapInstance = new ViamigoHotelsMap(mapInstance);
        window.viamigoHotelsMapInstance = viamigoHotelsMapInstance;
        console.log('✅ Hotels map integration ready');
        return viamigoHotelsMapInstance;
    } catch (error) {
        console.error('❌ Error initializing hotels map:', error);
        return null;
    }
}

// Export to window for global access
window.ViamigoHotelsMap = ViamigoHotelsMap;
window.initializeHotelsMap = initializeHotelsMap;

console.log('🏨 viamigo-hotels-map.js loaded successfully');
