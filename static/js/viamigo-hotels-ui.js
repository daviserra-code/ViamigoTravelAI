/**
 * Viamigo Hotels UI Controller
 * Handles hotel search modal, availability checking, and UI updates
 * 
 * Follows Viamigo design principles:
 * - Hotels are a SUPPORTING feature, not primary
 * - Always check availability before showing features
 * - Match existing Tailwind dark theme design
 */

(function() {
    'use strict';
    
    // Wait for DOM and hotels API to be ready
    document.addEventListener('DOMContentLoaded', initHotelsUI);
    
    // State
    let currentCity = null;
    let hotelsAvailable = false;
    let selectedCategory = 'all';
    let searchTimeout = null;
    let hotelModalMode = 'start'; // 'start' or 'end'
    
    function initHotelsUI() {
        console.log('🏨 Initializing Viamigo Hotels UI...');
        
        // Check if hotels API is loaded
        if (typeof window.viamigoHotels === 'undefined') {
            console.error('❌ Hotels API not loaded');
            return;
        }
        
        // Get city from location inputs and check availability
        detectCityAndCheckAvailability();
        
        // Setup event listeners
        setupEventListeners();
        
        console.log('✅ Hotels UI initialized');
    }
    
    /**
     * Detect city from start/end location inputs
     */
    function detectCityAndCheckAvailability() {
        const startInput = document.getElementById('start-location');
        const endInput = document.getElementById('end-location');
        
        if (!startInput || !endInput) return;
        
        // Extract city from location strings
        const startCity = extractCity(startInput.value);
        const endCity = extractCity(endInput.value);
        
        // Use the first available city
        currentCity = startCity || endCity || 'Milan';
        
        console.log(`📍 Detected city: ${currentCity}`);
        
        // Check if hotels are available for this city
        checkHotelAvailability(currentCity);
        
        // Listen for location changes
        startInput.addEventListener('input', debounce(() => {
            const city = extractCity(startInput.value);
            if (city && city !== currentCity) {
                currentCity = city;
                checkHotelAvailability(city);
            }
        }, 500));
        
        endInput.addEventListener('input', debounce(() => {
            const city = extractCity(endInput.value);
            if (city && city !== currentCity) {
                currentCity = city;
                checkHotelAvailability(city);
            }
        }, 500));
    }
    
    /**
     * Extract city name from location string
     * Examples: "Piazza De Ferrari, Genova" → "Genova"
     *           "Milano" → "Milano"
     */
    function extractCity(locationString) {
        if (!locationString) return null;
        
        // Common Italian cities
        const cities = ['Milano', 'Milan', 'Roma', 'Rome', 'Firenze', 'Florence', 
                       'Venezia', 'Venice', 'Torino', 'Turin', 'Bologna', 
                       'Genova', 'Genoa', 'Napoli', 'Naples', 'Palermo'];
        
        for (const city of cities) {
            if (locationString.toLowerCase().includes(city.toLowerCase())) {
                return city;
            }
        }
        
        // Try last comma-separated part
        const parts = locationString.split(',');
        if (parts.length > 1) {
            return parts[parts.length - 1].trim();
        }
        
        return null;
    }
    
    /**
     * Check if hotels are available for a city
     */
    async function checkHotelAvailability(city) {
        try {
            const result = await window.viamigoHotels.checkAvailability(city);
            
            hotelsAvailable = result.available && result.hotelCount > 0;
            currentCity = result.city; // Use normalized city name
            
            console.log(`🏨 Hotels in ${currentCity}: ${result.available ? '✅ Available' : '❌ Not available'} (${result.hotelCount} hotels)`);
            
            // Update UI based on availability
            updateUIForAvailability(result);
            
        } catch (error) {
            console.error('❌ Error checking hotel availability:', error);
            hotelsAvailable = false;
            hideHotelFeatures();
        }
    }
    
    /**
     * Update UI based on hotel availability
     */
    function updateUIForAvailability(result) {
        const startHotelBtn = document.getElementById('start-hotel-btn');
        const hotelsBadge = document.getElementById('hotels-info-badge');
        const hotelsBadgeText = document.getElementById('hotels-info-text');
        
        if (result.available && result.hotelCount > 0) {
            // Show hotel button
            if (startHotelBtn) {
                startHotelBtn.classList.remove('hidden');
            }
            
            // Hide info badge
            if (hotelsBadge) {
                hotelsBadge.classList.add('hidden');
            }
        } else {
            // Hide hotel button
            if (startHotelBtn) {
                startHotelBtn.classList.add('hidden');
            }
            
            // Show info badge with supported cities
            if (hotelsBadge && hotelsBadgeText) {
                window.viamigoHotels.getSupportedCities().then(data => {
                    if (data.cities && data.cities.length > 0) {
                        const cityNames = data.cities.slice(0, 3).map(c => c.city).join(', ');
                        hotelsBadgeText.textContent = `🏨 Hotel disponibili: ${cityNames}`;
                        hotelsBadge.classList.remove('hidden');
                    }
                });
            }
        }
    }
    
    /**
     * Hide all hotel features
     */
    function hideHotelFeatures() {
        const startHotelBtn = document.getElementById('start-hotel-btn');
        if (startHotelBtn) {
            startHotelBtn.classList.add('hidden');
        }
    }
    
    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Hotel search button
        const startHotelBtn = document.getElementById('start-hotel-btn');
        if (startHotelBtn) {
            startHotelBtn.addEventListener('click', () => {
                hotelModalMode = 'start';
                openHotelModal();
            });
        }
        
        // Modal close button
        const closeBtn = document.getElementById('close-hotel-modal');
        if (closeBtn) {
            closeBtn.addEventListener('click', closeHotelModal);
        }
        
        // Close on backdrop click
        const modal = document.getElementById('hotel-modal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    closeHotelModal();
                }
            });
        }
        
        // Search input
        const searchInput = document.getElementById('hotel-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    searchHotels(e.target.value);
                }, 300);
            });
        }
        
        // Category buttons
        const categoryBtns = document.querySelectorAll('.hotel-category-btn');
        categoryBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                // Update active state
                categoryBtns.forEach(b => {
                    b.classList.remove('bg-violet-500', 'text-white');
                    b.classList.add('bg-gray-700', 'text-gray-300');
                });
                btn.classList.remove('bg-gray-700', 'text-gray-300');
                btn.classList.add('bg-violet-500', 'text-white');
                
                // Update category and search
                selectedCategory = btn.dataset.category;
                const searchInput = document.getElementById('hotel-search-input');
                searchHotels(searchInput ? searchInput.value : '');
            });
        });
        
        // City selector
        const citySelector = document.getElementById('hotel-city-selector');
        if (citySelector) {
            citySelector.addEventListener('change', (e) => {
                currentCity = e.target.value;
                console.log(`🌍 City changed to: ${currentCity}`);
                // Reload stats and hotels for new city
                loadHotelStats();
                searchHotels('');
            });
        }
    }
    
    /**
     * Open hotel search modal
     */
    function openHotelModal() {
        const modal = document.getElementById('hotel-modal');
        const searchInput = document.getElementById('hotel-search-input');
        
        if (!modal) return;
        
        modal.classList.remove('hidden');
        
        // Focus search input
        if (searchInput) {
            setTimeout(() => searchInput.focus(), 100);
        }
        
        // Load city selector first
        loadCitySelector();
        
        // Load stats and top hotels
        loadHotelStats();
        searchHotels('');
    }
    
    /**
     * Close hotel search modal
     */
    function closeHotelModal() {
        const modal = document.getElementById('hotel-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        
        // Clear search
        const searchInput = document.getElementById('hotel-search-input');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Reset category
        selectedCategory = 'all';
        const categoryBtns = document.querySelectorAll('.hotel-category-btn');
        categoryBtns.forEach(btn => {
            if (btn.dataset.category === 'all') {
                btn.classList.remove('bg-gray-700', 'text-gray-300');
                btn.classList.add('bg-violet-500', 'text-white');
            } else {
                btn.classList.remove('bg-violet-500', 'text-white');
                btn.classList.add('bg-gray-700', 'text-gray-300');
            }
        });
    }
    
    /**
     * Load supported cities into selector
     */
    async function loadCitySelector() {
        const citySelector = document.getElementById('hotel-city-selector');
        if (!citySelector) return;
        
        try {
            const result = await window.viamigoHotels.getSupportedCities();
            
            if (result.success && result.cities && result.cities.length > 0) {
                // Sort cities by hotel count (descending)
                const cities = result.cities.sort((a, b) => b.hotel_count - a.hotel_count);
                
                // Build options HTML
                citySelector.innerHTML = cities.map(city => {
                    const selected = city.city === currentCity ? 'selected' : '';
                    return `<option value="${city.city}" ${selected}>
                        📍 ${city.city} (${city.hotel_count.toLocaleString()} hotel${city.hotel_count !== 1 ? 's' : ''})
                    </option>`;
                }).join('');
                
                // Set current city if not already set
                if (!currentCity && cities.length > 0) {
                    currentCity = cities[0].city;
                }
                
                console.log(`🌍 Loaded ${cities.length} cities, current: ${currentCity}`);
            } else {
                citySelector.innerHTML = '<option value="">Nessuna città disponibile</option>';
            }
        } catch (error) {
            console.error('❌ Failed to load cities:', error);
            citySelector.innerHTML = '<option value="">Errore caricamento città</option>';
        }
    }
    
    /**
     * Load and display hotel statistics
     */
    async function loadHotelStats() {
        const statsWidget = document.getElementById('hotel-stats-widget');
        const totalEl = document.getElementById('stats-total');
        const avgRatingEl = document.getElementById('stats-avg-rating');
        const totalReviewsEl = document.getElementById('stats-total-reviews');
        const categoriesEl = document.getElementById('stats-categories');
        
        if (!statsWidget || !currentCity) return;
        
        try {
            const result = await window.viamigoHotels.getStats(currentCity);
            
            if (result.success && result.stats) {
                const stats = result.stats;
                
                // Update numbers
                if (totalEl) {
                    totalEl.textContent = stats.total_hotels || 0;
                }
                if (avgRatingEl) {
                    const avgRating = stats.average_rating ? stats.average_rating.toFixed(1) : '—';
                    avgRatingEl.innerHTML = `
                        <span>${avgRating}</span>
                        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                        </svg>
                    `;
                }
                if (totalReviewsEl) {
                    totalReviewsEl.textContent = stats.total_reviews ? stats.total_reviews.toLocaleString() : '0';
                }
                
                // Update category breakdown
                if (categoriesEl && stats.by_category) {
                    const categories = [
                        { key: 'luxury', label: '💎 Luxury', color: 'text-yellow-400' },
                        { key: 'premium', label: '⭐ Premium', color: 'text-blue-400' },
                        { key: 'mid-range', label: '🏨 Mid-Range', color: 'text-green-400' },
                        { key: 'budget', label: '💰 Budget', color: 'text-gray-400' }
                    ];
                    
                    categoriesEl.innerHTML = categories.map(cat => {
                        const count = stats.by_category[cat.key] || 0;
                        const percentage = stats.total_hotels > 0 
                            ? Math.round((count / stats.total_hotels) * 100) 
                            : 0;
                        return `
                            <span class="${cat.color} bg-gray-700/50 px-2 py-1 rounded">
                                ${cat.label}: ${count} (${percentage}%)
                            </span>
                        `;
                    }).join('');
                }
                
                // Show widget
                statsWidget.classList.remove('hidden');
                
            } else {
                // Hide widget if no data
                statsWidget.classList.add('hidden');
            }
            
        } catch (error) {
            console.error('❌ Failed to load hotel stats:', error);
            statsWidget.classList.add('hidden');
        }
    }
    
    /**
     * Search hotels
     */
    async function searchHotels(query) {
        const loading = document.getElementById('hotel-loading');
        const list = document.getElementById('hotel-list');
        const empty = document.getElementById('hotel-empty');
        
        if (!loading || !list || !empty) return;
        
        // Show loading
        loading.classList.remove('hidden');
        list.innerHTML = '';
        empty.classList.add('hidden');
        
        try {
            let result;
            
            // Handle favorites category
            if (selectedCategory === 'favorites') {
                const favorites = getFavorites();
                
                // Filter by current city and search query
                const filteredFavorites = favorites.filter(fav => {
                    const matchesCity = !currentCity || fav.city === currentCity;
                    const matchesQuery = !query.trim() || fav.name.toLowerCase().includes(query.toLowerCase());
                    return matchesCity && matchesQuery;
                });
                
                result = {
                    success: true,
                    hotels: filteredFavorites
                };
            } else if (query.trim()) {
                // Search by name
                result = await window.viamigoHotels.search(currentCity, query, 0, 20);
            } else {
                // Get top hotels by category
                result = await window.viamigoHotels.getTopHotels(currentCity, selectedCategory, 20);
            }
            
            // Hide loading
            loading.classList.add('hidden');
            
            if (result.success && result.hotels && result.hotels.length > 0) {
                renderHotels(result.hotels);
            } else {
                empty.classList.remove('hidden');
                // Show helpful message for empty favorites
                if (selectedCategory === 'favorites') {
                    const emptyDiv = document.getElementById('hotel-empty');
                    if (emptyDiv) {
                        emptyDiv.innerHTML = `
                            <div class="text-center py-12 text-gray-400">
                                <svg class="w-16 h-16 mx-auto mb-3 opacity-50" fill="currentColor" viewBox="0 0 20 20">
                                    <path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"/>
                                </svg>
                                <p class="font-medium">Nessun hotel preferito</p>
                                <p class="text-sm mt-1">Aggiungi hotel ai preferiti cliccando ❤️</p>
                            </div>
                        `;
                    }
                }
            }
            
        } catch (error) {
            console.error('❌ Hotel search failed:', error);
            loading.classList.add('hidden');
            empty.classList.remove('hidden');
        }
    }
    
    /**
     * Render hotel list
     */
    function renderHotels(hotels) {
        const list = document.getElementById('hotel-list');
        if (!list) return;
        
        list.innerHTML = hotels.map(hotel => {
            const isFavorite = isHotelFavorite(hotel.name, currentCity);
            const heartIcon = isFavorite 
                ? `<svg class="w-5 h-5 fill-current text-red-500" viewBox="0 0 20 20"><path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z"/></svg>`
                : `<svg class="w-5 h-5 fill-current text-gray-400" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"/></svg>`;
            
            return `
            <div class="bg-gray-700 rounded-lg p-3 hover:bg-gray-600 transition-colors border border-gray-600 hotel-card" data-hotel-name="${escapeHtml(hotel.name)}" data-hotel-city="${currentCity}" data-hotel-rating="${hotel.rating || 0}" data-hotel-reviews="${hotel.review_count || 0}" data-hotel-address="${escapeHtml(hotel.address || '')}" data-hotel-lat="${hotel.latitude || ''}" data-hotel-lng="${hotel.longitude || ''}">
                <div class="flex items-start justify-between">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2">
                            <h4 class="font-semibold text-white text-sm truncate flex-1">${escapeHtml(hotel.name)}</h4>
                            <button class="favorite-btn flex-shrink-0 p-1 hover:scale-110 transition-transform" data-hotel-name="${escapeHtml(hotel.name)}" data-hotel-city="${currentCity}" title="${isFavorite ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti'}">
                                ${heartIcon}
                            </button>
                        </div>
                        ${hotel.address ? `<p class="text-xs text-gray-400 mt-1 line-clamp-1">${escapeHtml(hotel.address)}</p>` : ''}
                    </div>
                    <div class="ml-2 flex-shrink-0">
                        <div class="flex items-center space-x-1 text-yellow-400">
                            <span class="text-sm font-bold">${hotel.rating || '—'}</span>
                            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                            </svg>
                        </div>
                        ${hotel.review_count ? `<p class="text-xs text-gray-400 text-right mt-0.5">${hotel.review_count.toLocaleString()} recensioni</p>` : ''}
                    </div>
                </div>
                ${hotel.distance_km ? `<p class="text-xs text-violet-400 mt-2">📍 ${hotel.distance_km.toFixed(2)} km di distanza</p>` : ''}
                <button class="select-hotel-btn mt-2 w-full bg-violet-500 hover:bg-violet-600 text-white text-sm font-medium py-2 rounded-lg transition-colors">
                    Parti da qui
                </button>
            </div>
        `;
        }).join('');
        
        // Add click handlers to select hotel buttons
        document.querySelectorAll('.hotel-card .select-hotel-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const card = btn.closest('.hotel-card');
                selectHotel(card.dataset.hotelName, card.dataset.hotelLat, card.dataset.hotelLng);
            });
        });
        
        // Add click handlers to favorite buttons
        document.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const hotelName = btn.dataset.hotelName;
                const city = btn.dataset.hotelCity;
                const card = btn.closest('.hotel-card');
                
                toggleFavorite({
                    name: hotelName,
                    city: city,
                    rating: parseFloat(card.dataset.hotelRating) || 0,
                    reviews: parseInt(card.dataset.hotelReviews) || 0,
                    address: card.dataset.hotelAddress || '',
                    latitude: card.dataset.hotelLat || '',
                    longitude: card.dataset.hotelLng || ''
                });
                
                // Update icon
                const isFavorite = isHotelFavorite(hotelName, city);
                btn.innerHTML = isFavorite 
                    ? `<svg class="w-5 h-5 fill-current text-red-500" viewBox="0 0 20 20"><path d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z"/></svg>`
                    : `<svg class="w-5 h-5 fill-current text-gray-400" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clip-rule="evenodd"/></svg>`;
                btn.title = isFavorite ? 'Rimuovi dai preferiti' : 'Aggiungi ai preferiti';
            });
        });
    }
    
    /**
     * Select a hotel
     */
    function selectHotel(hotelName, lat, lng) {
        console.log(`✅ Selected hotel: ${hotelName}`);
        
        // Update start location input
        const startInput = document.getElementById('start-location');
        if (startInput && hotelName) {
            startInput.value = `🏨 ${hotelName}`;
            
            // Store coordinates if available
            if (lat && lng) {
                startInput.dataset.lat = lat;
                startInput.dataset.lng = lng;
            }
        }
        
        // Close modal
        closeHotelModal();
        
        // Show success feedback
        showSuccessToast(`Hotel selezionato: ${hotelName}`);
    }
    
    /**
     * Show success toast
     */
    function showSuccessToast(message) {
        // Create toast element
        const toast = document.createElement('div');
        toast.className = 'fixed top-4 left-1/2 transform -translate-x-1/2 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 flex items-center space-x-2';
        toast.innerHTML = `
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
            </svg>
            <span>${escapeHtml(message)}</span>
        `;
        
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Debounce function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // ===== FAVORITES MANAGEMENT =====
    
    const FAVORITES_KEY = 'viamigo_favorite_hotels';
    
    /**
     * Get all favorite hotels from localStorage
     */
    function getFavorites() {
        try {
            const stored = localStorage.getItem(FAVORITES_KEY);
            return stored ? JSON.parse(stored) : [];
        } catch (error) {
            console.error('❌ Error reading favorites:', error);
            return [];
        }
    }
    
    /**
     * Save favorites to localStorage
     */
    function saveFavorites(favorites) {
        try {
            localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
        } catch (error) {
            console.error('❌ Error saving favorites:', error);
        }
    }
    
    /**
     * Check if hotel is in favorites
     */
    function isHotelFavorite(hotelName, city) {
        const favorites = getFavorites();
        return favorites.some(fav => fav.name === hotelName && fav.city === city);
    }
    
    /**
     * Toggle hotel favorite status
     */
    function toggleFavorite(hotel) {
        let favorites = getFavorites();
        const index = favorites.findIndex(fav => fav.name === hotel.name && fav.city === hotel.city);
        
        if (index >= 0) {
            // Remove from favorites
            favorites.splice(index, 1);
            showSuccessToast(`❌ ${hotel.name} rimosso dai preferiti`);
            console.log(`💔 Removed from favorites: ${hotel.name}`);
        } else {
            // Add to favorites
            favorites.push({
                name: hotel.name,
                city: hotel.city,
                rating: hotel.rating,
                reviews: hotel.reviews,
                address: hotel.address,
                latitude: hotel.latitude,
                longitude: hotel.longitude,
                savedAt: new Date().toISOString()
            });
            showSuccessToast(`❤️ ${hotel.name} aggiunto ai preferiti`);
            console.log(`💚 Added to favorites: ${hotel.name}`);
        }
        
        saveFavorites(favorites);
    }
    
    /**
     * Get favorite hotels count
     */
    function getFavoritesCount() {
        return getFavorites().length;
    }
    
    // Make favorites accessible globally for debugging
    window.viamigoFavorites = {
        get: getFavorites,
        toggle: toggleFavorite,
        count: getFavoritesCount,
        isHotelFavorite: isHotelFavorite
    };
    
})();
