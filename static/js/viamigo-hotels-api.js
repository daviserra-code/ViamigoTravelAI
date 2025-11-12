/**
 * Viamigo Hotels API Service
 * Handles all hotel-related API calls with availability checking
 * 
 * IMPORTANT: Always check city availability before showing hotel features
 */

const HOTELS_API_BASE = '/api/hotels';

// City name normalization (Italian → English for database compatibility)
const CITY_ALIASES = {
    'Milano': 'Milan',
    'Roma': 'Rome',
    'Firenze': 'Florence',
    'Venezia': 'Venice',
    'Torino': 'Turin',
    'Genova': 'Genoa',
    'Napoli': 'Naples',
    'Bologna': 'Bologna',
    'Palermo': 'Palermo',
    // Lowercase variants
    'milano': 'Milan',
    'roma': 'Rome',
    'firenze': 'Florence',
    'venezia': 'Venice',
    'torino': 'Turin',
    'genova': 'Genoa',
    'napoli': 'Naples',
    'bologna': 'Bologna',
    'palermo': 'Palermo'
};

/**
 * Normalize city name to database format
 * @param {string} city - City name in any language
 * @returns {string} - Normalized city name
 */
function normalizeCity(city) {
    if (!city) return 'Milan'; // Default fallback
    
    // Ensure city is a string
    if (typeof city !== 'string') {
        console.warn(`⚠️ normalizeCity: expected string, got ${typeof city}:`, city);
        return 'Milan';
    }
    
    const cityLower = city.toLowerCase().trim();
    return CITY_ALIASES[cityLower] || city;
}

/**
 * Viamigo Hotels API Client
 */
const viamigoHotels = {
    /**
     * CHECK THIS FIRST! Verify if city has hotel data
     * @param {string} city - City name
     * @returns {Promise<Object>} - {available: boolean, hotel_count: number, message: string}
     */
    async checkAvailability(city) {
        try {
            const normalizedCity = normalizeCity(city);
            const response = await fetch(`${HOTELS_API_BASE}/availability/${encodeURIComponent(normalizedCity)}`);
            const data = await response.json();
            return {
                success: data.success,
                available: data.available,
                hotelCount: data.hotel_count || 0,
                avgRating: data.avg_rating || 0,
                message: data.message || '',
                city: normalizedCity
            };
        } catch (error) {
            console.error('❌ Hotel availability check failed:', error);
            return {
                success: false,
                available: false,
                hotelCount: 0,
                message: 'Error checking hotel availability'
            };
        }
    },

    /**
     * Get list of all cities with hotel data
     * @returns {Promise<Array>} - Array of city objects with stats
     */
    async getSupportedCities() {
        try {
            const response = await fetch(`${HOTELS_API_BASE}/supported-cities`);
            const data = await response.json();
            return {
                success: data.success,
                cities: data.cities || [],
                count: data.count || 0
            };
        } catch (error) {
            console.error('❌ Failed to get supported cities:', error);
            return { success: false, cities: [], count: 0 };
        }
    },

    /**
     * Search hotels in a city
     * @param {string} city - City name
     * @param {string} query - Search query (hotel name)
     * @param {number} minRating - Minimum rating (default 8.0)
     * @param {number} limit - Max results (default 10)
     * @returns {Promise<Object>} - {success: boolean, hotels: Array}
     */
    async search(city, query = '', minRating = 8.0, limit = 10) {
        try {
            const normalizedCity = normalizeCity(city);
            
            // Check availability first
            const availability = await this.checkAvailability(normalizedCity);
            if (!availability.available) {
                return {
                    success: false,
                    hotels: [],
                    message: availability.message
                };
            }

            const params = new URLSearchParams({
                city: normalizedCity,
                q: query,
                min_rating: minRating,
                limit: limit
            });

            const response = await fetch(`${HOTELS_API_BASE}/search?${params}`);
            const data = await response.json();
            return {
                success: data.success,
                hotels: data.hotels || [],
                count: data.count || 0
            };
        } catch (error) {
            console.error('❌ Hotel search failed:', error);
            return { success: false, hotels: [], count: 0 };
        }
    },

    /**
     * Get hotels near a location
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     * @param {number} radius - Radius in km (default 1.0)
     * @param {number} minRating - Minimum rating (default 8.0)
     * @param {number} limit - Max results (default 5)
     * @returns {Promise<Object>} - {success: boolean, hotels: Array}
     */
    async getNearby(lat, lng, radius = 1.0, minRating = 8.0, limit = 5) {
        try {
            const params = new URLSearchParams({
                lat: lat,
                lng: lng,
                radius: radius,
                min_rating: minRating,
                limit: limit
            });

            const response = await fetch(`${HOTELS_API_BASE}/nearby?${params}`);
            const data = await response.json();
            return {
                success: data.success,
                hotels: data.hotels || [],
                count: data.count || 0,
                center: data.center,
                radiusKm: data.radius_km
            };
        } catch (error) {
            console.error('❌ Nearby hotels query failed:', error);
            return { success: false, hotels: [], count: 0 };
        }
    },

    /**
     * Get top hotels in a city by category
     * @param {string} city - City name
     * @param {string} category - luxury|premium|mid-range|budget|all
     * @param {number} limit - Max results (default 20)
     * @returns {Promise<Object>} - {success: boolean, hotels: Array}
     */
    async getTopHotels(city, category = 'all', limit = 20) {
        try {
            const normalizedCity = normalizeCity(city);
            
            // Check availability first
            const availability = await this.checkAvailability(normalizedCity);
            if (!availability.available) {
                return {
                    success: false,
                    hotels: [],
                    message: availability.message
                };
            }

            const params = new URLSearchParams({
                category: category,
                limit: limit
            });

            const response = await fetch(`${HOTELS_API_BASE}/top/${encodeURIComponent(normalizedCity)}?${params}`);
            const data = await response.json();
            return {
                success: data.success,
                hotels: data.hotels || [],
                count: data.count || 0,
                category: data.category
            };
        } catch (error) {
            console.error('❌ Top hotels query failed:', error);
            return { success: false, hotels: [], count: 0 };
        }
    },

    /**
     * Get hotel details by name
     * @param {string} hotelName - Hotel name
     * @param {string} city - City name (optional but recommended)
     * @returns {Promise<Object>} - {success: boolean, hotel: Object}
     */
    async getDetails(hotelName, city = null) {
        try {
            const params = new URLSearchParams();
            if (city) {
                params.append('city', normalizeCity(city));
            }

            const url = `${HOTELS_API_BASE}/details/${encodeURIComponent(hotelName)}${params.toString() ? '?' + params : ''}`;
            const response = await fetch(url);
            const data = await response.json();
            return {
                success: data.success,
                hotel: data.hotel || null
            };
        } catch (error) {
            console.error('❌ Hotel details query failed:', error);
            return { success: false, hotel: null };
        }
    },

    /**
     * Get city statistics
     * @param {string} city - City name
     * @returns {Promise<Object>} - {success: boolean, stats: Object}
     */
    async getStats(city) {
        try {
            const normalizedCity = normalizeCity(city);
            const response = await fetch(`${HOTELS_API_BASE}/stats/${encodeURIComponent(normalizedCity)}`);
            const data = await response.json();
            return {
                success: data.success,
                stats: data.stats || null,
                city: data.city
            };
        } catch (error) {
            console.error('❌ Hotel stats query failed:', error);
            return { success: false, stats: null };
        }
    },

    /**
     * Get category information
     * @returns {Promise<Object>} - {success: boolean, categories: Object}
     */
    async getCategories() {
        try {
            const response = await fetch(`${HOTELS_API_BASE}/categories`);
            const data = await response.json();
            return {
                success: data.success,
                categories: data.categories || {}
            };
        } catch (error) {
            console.error('❌ Categories query failed:', error);
            return { success: false, categories: {} };
        }
    }
};

// Export for use in other scripts
if (typeof window !== 'undefined') {
    window.viamigoHotels = viamigoHotels;
    window.normalizeCity = normalizeCity;
    console.log('✅ Viamigo Hotels API loaded');
}
