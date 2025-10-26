/**
 * Image Management System for ViamigoTravelAI
 * Handles local database images with online fallbacks
 */

class ViamigoImageManager {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
        this.cache = new Map();
        this.pendingRequests = new Map();
    }

    /**
     * Get image URL for an attraction with fallback logic
     * @param {string} city - City name
     * @param {string} attraction - Attraction name
     * @param {string} fallbackUrl - Optional fallback URL
     * @returns {Promise<string>} Image URL
     */
    async getImageUrl(city, attraction, fallbackUrl = null) {
        const cacheKey = `${city.toLowerCase()}_${attraction.toLowerCase()}`;
        
        // Check cache first
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        // Check if we already have a pending request
        if (this.pendingRequests.has(cacheKey)) {
            return this.pendingRequests.get(cacheKey);
        }

        // Create new request promise
        const promise = this._fetchImageUrl(city, attraction, fallbackUrl);
        this.pendingRequests.set(cacheKey, promise);

        try {
            const result = await promise;
            this.cache.set(cacheKey, result);
            return result;
        } finally {
            this.pendingRequests.delete(cacheKey);
        }
    }

    /**
     * Internal method to fetch image URL - FIXED TO USE CLASSIFICATION ENDPOINT
     */
    async _fetchImageUrl(city, attraction, fallbackUrl) {
        try {
            // Use the WORKING image classification endpoint
            const classifyUrl = `${this.baseUrl}/api/images/classify`;
            
            const response = await fetch(classifyUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: `${attraction} ${city}`,
                    context: `${attraction} in ${city}`
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                if (data.image && data.image.url) {
                    console.log(`✅ Got classified image for ${attraction} in ${city} from ${data.source || 'unknown'} source`);
                    return data.image.url;
                }
            }
        } catch (error) {
            console.warn(`⚠️ Image classification failed for ${attraction}:`, error);
        }

        // Try fallback URL if provided
        if (fallbackUrl) {
            try {
                const response = await fetch(fallbackUrl, { method: 'HEAD' });
                if (response.ok) {
                    console.log(`✅ Using fallback image for ${attraction}`);
                    return fallbackUrl;
                }
            } catch (error) {
                console.warn(`⚠️ Fallback image failed for ${attraction}:`, error);
            }
        }

        // Generate placeholder as last resort
        console.log(`📝 Generating placeholder for ${attraction} in ${city}`);
        return this._generatePlaceholder(city, attraction);
    }

    /**
     * Generate a placeholder image data URL
     */
    _generatePlaceholder(city, attraction) {
        const canvas = document.createElement('canvas');
        canvas.width = 400;
        canvas.height = 300;
        const ctx = canvas.getContext('2d');

        // Background
        ctx.fillStyle = '#f0f0f0';
        ctx.fillRect(0, 0, 400, 300);

        // Border
        ctx.strokeStyle = '#ddd';
        ctx.lineWidth = 2;
        ctx.strokeRect(1, 1, 398, 298);

        // Text
        ctx.fillStyle = '#666';
        ctx.font = 'bold 18px Arial';
        ctx.textAlign = 'center';
        
        // City
        ctx.fillText(`📍 ${city}`, 200, 140);
        
        // Attraction
        ctx.fillStyle = '#333';
        ctx.font = 'bold 20px Arial';
        ctx.fillText(`🏛️ ${attraction}`, 200, 180);

        return canvas.toDataURL('image/jpeg', 0.8);
    }

    /**
     * Preload images for a list of attractions
     */
    async preloadImages(attractions) {
        const promises = attractions.map(item => 
            this.getImageUrl(item.city, item.attraction, item.fallback)
        );
        
        try {
            await Promise.allSettled(promises);
            console.log(`✅ Preloaded ${attractions.length} images`);
        } catch (error) {
            console.warn('⚠️ Some images failed to preload:', error);
        }
    }

    /**
     * Apply image to DOM element with loading states
     */
    async applyImageToElement(element, city, attraction, fallbackUrl = null) {
        // Add loading class
        element.classList.add('loading-image');
        
        try {
            const imageUrl = await this.getImageUrl(city, attraction, fallbackUrl);
            
            // Create img element to test loading
            const img = new Image();
            img.onload = () => {
                element.style.backgroundImage = `url(${imageUrl})`;
                element.classList.remove('loading-image');
                element.classList.add('image-loaded');
            };
            img.onerror = () => {
                console.warn(`Failed to load image for ${attraction}`);
                element.classList.remove('loading-image');
                element.classList.add('image-error');
            };
            img.src = imageUrl;
            
        } catch (error) {
            console.error(`Error applying image for ${attraction}:`, error);
            element.classList.remove('loading-image');
            element.classList.add('image-error');
        }
    }

    /**
     * Get image statistics from the database
     */
    async getImageStats() {
        try {
            const response = await fetch(`${this.baseUrl}/api/images/stats`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.warn('Failed to get image stats:', error);
        }
        return null;
    }
}

// Global instance
window.ViamigoImages = new ViamigoImageManager();

// CSS for loading states
const imageLoadingStyles = `
.loading-image {
    background: linear-gradient(45deg, #f0f0f0 25%, #e0e0e0 25%, #e0e0e0 50%, #f0f0f0 50%, #f0f0f0 75%, #e0e0e0 75%);
    background-size: 20px 20px;
    animation: loading-stripe 1s linear infinite;
}

.image-loaded {
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
}

.image-error {
    background: #ffeaa7;
    display: flex;
    align-items: center;
    justify-content: center;
}

.image-error::after {
    content: "📷 Image unavailable";
    color: #666;
    font-size: 14px;
}

@keyframes loading-stripe {
    0% { background-position: 0 0; }
    100% { background-position: 20px 0; }
}
`;

// Inject styles
const styleSheet = document.createElement('style');
styleSheet.textContent = imageLoadingStyles;
document.head.appendChild(styleSheet);

// Export for ES6 modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ViamigoImageManager;
}