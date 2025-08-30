// Viamigo Travel App - API Integration
class ViamigoAPI {
    constructor() {
        this.baseURL = '/api/v1';
        this.chatContainer = null;
        this.chatInput = null;
        this.isTyping = false;
    }

    async sendChatMessage(message) {
        try {
            // Create travel query from message
            const query = {
                query_text: message,
                interests: this.getUserInterests(),
                budget: this.getUserBudget(),
                group_size: 1
            };

            const response = await fetch(`${this.baseURL}/travel/recommendations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(query)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return this.formatRecommendationsForChat(data);
        } catch (error) {
            console.error('Error sending message:', error);
            return 'Mi dispiace, c\'è stato un problema nel generare i consigli di viaggio. Riprova tra un momento.';
        }
    }

    async planTrip(departure, destination) {
        try {
            const query = {
                query_text: `Pianifica un viaggio da ${departure} a ${destination}`,
                destination: destination,
                interests: this.getUserInterests(),
                budget: this.getUserBudget(),
                group_size: 1
            };

            const response = await fetch(`${this.baseURL}/travel/recommendations`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(query)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Error planning trip:', error);
            return null;
        }
    }

    getUserInterests() {
        const selected = document.querySelectorAll('.interest-tag.selected');
        return Array.from(selected).map(tag => tag.textContent.toLowerCase());
    }

    getUserBudget() {
        const selected = document.querySelector('.segmented-control button.selected');
        if (!selected) return 1000;

        const budgetText = selected.textContent;
        if (budgetText === '€') return 500;
        if (budgetText === '€€') return 1500;
        if (budgetText === '€€€') return 3000;
        return 1000;
    }

    formatRecommendationsForChat(data) {
        if (!data.recommendations || data.recommendations.length === 0) {
            return 'Non ho trovato consigli per questa ricerca. Prova con una destinazione diversa!';
        }

        let response = `Ho trovato ${data.recommendations.length} ottimi consigli per te:\n\n`;

        data.recommendations.forEach((rec, index) => {
            response += `**${index + 1}. ${rec.destination}**\n`;
            response += `${rec.description}\n`;

            if (rec.estimated_cost) {
                response += `💰 Costo stimato: €${rec.estimated_cost}\n`;
            }

            if (rec.best_time_to_visit) {
                response += `📅 Miglior periodo: ${rec.best_time_to_visit}\n`;
            }

            if (rec.activities && rec.activities.length > 0) {
                response += `🎯 Attività: ${rec.activities.slice(0, 3).join(', ')}\n`;
            }

            response += `\n`;
        });

        return response;
    }

    addMessageToChat(message, isUser = false) {
        if (!this.chatContainer) {
            this.chatContainer = document.querySelector('#home-chat-view .flex-grow');
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = isUser
            ? 'bg-violet-500 text-white p-3 rounded-lg max-w-xs ml-auto'
            : 'bg-gray-800 p-3 rounded-lg max-w-xs';

        const messageText = document.createElement('p');
        messageText.className = 'text-sm';
        messageText.style.whiteSpace = 'pre-line';
        messageText.textContent = message.replace(/\\n/g, '\\n').replace(/\\*\\*/g, '');

        messageDiv.appendChild(messageText);
        this.chatContainer.appendChild(messageDiv);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    showTypingIndicator() {
        if (this.isTyping) return;
        this.isTyping = true;

        const typingDiv = document.createElement('div');
        typingDiv.id = 'typing-indicator';
        typingDiv.className = 'bg-gray-800 p-3 rounded-lg max-w-xs';
        typingDiv.innerHTML = '<p class="text-sm text-gray-400">L\'AI sta scrivendo...</p>';

        if (!this.chatContainer) {
            this.chatContainer = document.querySelector('#home-chat-view .flex-grow');
        }
        this.chatContainer.appendChild(typingDiv);
        this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
    }

    hideTypingIndicator() {
        this.isTyping = false;
        const typingDiv = document.getElementById('typing-indicator');
        if (typingDiv) {
            typingDiv.remove();
        }
    }
}

// Initialize API and event handlers
document.addEventListener('DOMContentLoaded', function() {
    const api = new ViamigoAPI();

    // Handle chat input
    const chatInput = document.querySelector('#home-chat-view input[type="text"]');
    const sendButton = document.querySelector('#home-chat-view .send-button');

    async function handleSendMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        // Add user message to chat
        api.addMessageToChat(message, true);
        chatInput.value = '';

        // Show typing indicator
        api.showTypingIndicator();

        try {
            // Get AI response
            const response = await api.sendChatMessage(message);

            // Hide typing indicator and show response
            api.hideTypingIndicator();
            api.addMessageToChat(response);
        } catch (error) {
            api.hideTypingIndicator();
            api.addMessageToChat('Mi dispiace, c\'è stato un errore. Riprova tra un momento.');
        }
    }

    if (sendButton) {
        sendButton.addEventListener('click', handleSendMessage);
    }

    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                handleSendMessage();
            }
        });
    }

    // Handle trip planning
    const planButton = document.querySelector('.plan-button');
    if (planButton) {
        planButton.addEventListener('click', async function() {
            const departureInput = document.querySelector('input[placeholder="Partenza"]');
            const destinationInput = document.querySelector('input[placeholder="Destinazione"]');

            const departure = departureInput.value.trim();
            const destination = destinationInput.value.trim();

            if (!departure || !destination) {
                alert('Per favore inserisci sia la partenza che la destinazione');
                return;
            }

            // Change button state
            planButton.textContent = 'Pianificando...';
            planButton.disabled = true;

            try {
                const tripData = await api.planTrip(departure, destination);

                if (tripData && tripData.recommendations) {
                    // Switch to itinerary page and populate data
                    const itineraryPage = document.getElementById('page-itinerary');
                    const homePage = document.getElementById('page-home');

                    homePage.classList.remove('active');
                    itineraryPage.classList.add('active');

                    // Update navigation
                    document.querySelectorAll('.nav-button').forEach(btn => {
                        btn.classList.remove('active', 'text-white');
                        btn.classList.add('text-gray-500');
                    });
                    document.querySelector('[data-page="itinerary"]').classList.add('active', 'text-white');

                    // Update header with trip info
                    const headerText = itineraryPage.querySelector('.header h2');
                    if (headerText) {
                        headerText.textContent = `Da ${departure} a ${destination}`;
                    }

                    // Generate itinerary based on recommendations
                    generateItineraryFromRecommendations(tripData.recommendations);
                } else {
                    alert('Non sono riuscito a creare un itinerario. Riprova con destinazioni diverse.');
                }
            } catch (error) {
                alert('Errore nella pianificazione del viaggio. Riprova tra un momento.');
            } finally {
                planButton.textContent = 'Pianifica il mio giorno';
                planButton.disabled = false;
            }
        });
    }

    // Handle interest tags selection
    document.querySelectorAll('.interest-tag').forEach(tag => {
        tag.addEventListener('click', function() {
            this.classList.toggle('selected');
        });
    });

    // Handle segmented controls
    document.querySelectorAll('.segmented-control button').forEach(button => {
        button.addEventListener('click', function() {
            // Remove selected from siblings
            this.parentElement.querySelectorAll('button').forEach(btn => {
                btn.classList.remove('selected');
            });
            // Add selected to clicked button
            this.classList.add('selected');
        });
    });

    // Save preferences
    const saveButton = document.querySelector('.save-button');
    if (saveButton) {
        saveButton.addEventListener('click', function() {
            // Here you could save to localStorage or send to backend
            const interests = api.getUserInterests();
            const budget = api.getUserBudget();

            localStorage.setItem('viamigo-interests', JSON.stringify(interests));
            localStorage.setItem('viamigo-budget', budget.toString());

            // Show feedback
            const originalText = this.textContent;
            this.textContent = 'Salvato!';
            this.style.backgroundColor = '#10b981';

            setTimeout(() => {
                this.textContent = originalText;
                this.style.backgroundColor = '';
            }, 2000);
        });
    }

    // Load saved preferences
    const savedInterests = localStorage.getItem('viamigo-interests');
    const savedBudget = localStorage.getItem('viamigo-budget');

    if (savedInterests) {
        const interests = JSON.parse(savedInterests);
        document.querySelectorAll('.interest-tag').forEach(tag => {
            if (interests.includes(tag.textContent.toLowerCase())) {
                tag.classList.add('selected');
            }
        });
    }
});

function generateItineraryFromRecommendations(recommendations) {
    const timelineContainer = document.querySelector('#itinerary-list-view .timeline');
    if (!timelineContainer) return;

    const itineraryItems = [];
    let currentTime = 9; // Start at 9 AM

    recommendations.forEach((rec, index) => {
        // Add travel time before each activity (except first)
        if (index > 0) {
            const travelTime = Math.random() * 30 + 15; // 15-45 minutes
            const startTime = String(Math.floor(currentTime)).padStart(2, '0') + ':' + String(Math.floor((currentTime % 1) * 60)).padStart(2, '0');
            currentTime += travelTime / 60;
            const endTime = String(Math.floor(currentTime)).padStart(2, '0') + ':' + String(Math.floor((currentTime % 1) * 60)).padStart(2, '0');

            itineraryItems.push({
                time: `${startTime} - ${endTime} (${Math.floor(travelTime)} min)`,
                title: `Spostamento verso ${rec.destination}`,
                desc: "Usa i mezzi pubblici o cammina seguendo le indicazioni.",
                context: "walk",
                transport: "walking" // Explicitly set transport type
            });
        }

        // Add the main activity
        const activityDuration = Math.random() * 120 + 60; // 1-3 hours
        const startTime = String(Math.floor(currentTime)).padStart(2, '0') + ':' + String(Math.floor((currentTime % 1) * 60)).padStart(2, '0');
        currentTime += activityDuration / 60;
        const endTime = String(Math.floor(currentTime)).padStart(2, '0') + ':' + String(Math.floor((currentTime % 1) * 60)).padStart(2, '0');

        itineraryItems.push({
            time: `${startTime} - ${endTime} (${Math.floor(activityDuration)} min)`,
            title: rec.destination,
            description: rec.description, // Use description from recommendation
            context: "museum", // Default context, can be refined
            opening_hours: rec.opening_hours, // Add rich details
            price_range: rec.price_range,
            highlights: rec.highlights,
            insider_tip: rec.insider_tip,
            lat: rec.lat, // Include coordinates if available
            lon: rec.lon
        });

        // Add AI tip occasionally
        if (index === 0 && rec.local_tips && rec.local_tips.length > 0) {
            itineraryItems.push({
                type: "tip",
                title: "Consiglio dell'AI",
                description: rec.local_tips[0]
            });
        }
    });

    renderCustomItinerary(itineraryItems, timelineContainer);
    // Call the function to draw the route after itinerary is rendered
    drawRouteOnMap(itineraryItems);
}

// Placeholder for getRealCoordinates - replace with actual implementation if available
function getRealCoordinates(title, city) {
    // This is a mock function. In a real app, you'd have a data source.
    console.log(`Mock lookup for coordinates of "${title}" in ${city}`);
    // Example fallback data for Genova
    if (city === 'genova') {
        if (title.toLowerCase().includes('acquario')) return { lat: 44.4071, lng: 8.9237 };
        if (title.toLowerCase().includes('centro storico')) return { lat: 44.4094, lng: 8.9285 };
        if (title.toLowerCase().includes('via balbi')) return { lat: 44.4088, lng: 8.9168 };
    }
    return null; // Return null if not found
}


// Placeholder functions for createTipCard, createEmergencyPlanCard, createSmartDiscoveryCard
function createTipCard(title, description) {
    return `<div class="pro-tip relative my-4 ml-2 p-3 rounded-lg border-l-4 border-violet-500 bg-violet-900/50"><h4 class="font-bold text-white text-sm">${title}</h4><p class="text-sm text-gray-300">${description}</p></div>`;
}

function createEmergencyPlanCard(title, description, plan_b_data) {
    return `<div class="pro-tip relative my-4 ml-2 p-3 rounded-lg border-l-4 border-red-500 bg-red-900/50"><h4 class="font-bold text-white text-sm">${title}</h4><p class="text-sm text-gray-300">${description}</p><p class="text-sm text-red-300 mt-1">Piano B: ${plan_b_data}</p></div>`;
}

function createSmartDiscoveryCard(title, description, discoveries) {
    let discoveryList = discoveries.map(d => `<li class="text-gray-300 text-xs">${d}</li>`).join('');
    return `<div class="pro-tip relative my-4 ml-2 p-3 rounded-lg border-l-4 border-blue-500 bg-blue-900/50"><h4 class="font-bold text-white text-sm">${title}</h4><p class="text-sm text-gray-300">${description}</p><ul class="list-disc pl-5 mt-2">${discoveryList}</ul></div>`;
}

function renderCustomItinerary(items, container) {
    container.innerHTML = '';

    items.forEach((item, index) => {
        let htmlContent;
        if (item.type === 'tip') {
            htmlContent = createTipCard(item.title, item.description);
        } else if (item.type === 'emergency_plan') {
            htmlContent = createEmergencyPlanCard(item.title, item.description, item.plan_b_data);
        } else if (item.type === 'smart_discovery') {
            htmlContent = createSmartDiscoveryCard(item.title, item.description, item.discoveries);
        } else {
            htmlContent = createTimelineItem(item, index);
        }

        const itemDiv = document.createElement('div');
        itemDiv.innerHTML = htmlContent.trim(); // Use trim to avoid issues with whitespace

        // Add click listener for detail expansion (if it's a regular item)
        if (!item.type) {
            const detailButton = itemDiv.querySelector('.cursor-pointer'); // Assuming createTimelineItem returns an item with a click handler attribute
            if (detailButton) {
                 // Safely get context, title, description
                const context = item.context || '';
                const title = item.title || '';
                const description = item.description || '';
                detailButton.setAttribute('onclick', `openModal('${context}', '${title}', '${description}')`);
            } else {
                // Fallback if the button isn't found, add listener to the main item div
                itemDiv.querySelector('.timeline-item').addEventListener('click', () => {
                    openModal(item.context || '', item.title || '', item.description || '');
                });
            }
        }

        container.appendChild(itemDiv.firstChild); // Append the actual content element
    });
}


function createTimelineItem(item, index) {
        const iconMap = {
            'walking': '🚶',
            'metro': '🚇',
            'bus': '🚌',
            'tram': '🚋',
            'train': '🚂',
            'funicular': '🚡',
            'start': '📍', // Changed to a more general starting point icon
            'visit': '🏛️'
        };

        // Use 'transport' property for icon, fallback to 'context' or default
        const iconKey = item.transport || item.context || 'walking';
        const icon = iconMap[iconKey] || '📍';
        const timeDisplay = item.time || `Step ${index + 1}`;

        // Extract rich details from _rich_details or direct properties
            const richDetails = item._rich_details || item;
            let richDetailsHTML = '';

            if (richDetails.opening_hours || richDetails.price_range || richDetails.highlights || richDetails.insider_tip) {
                richDetailsHTML = `
                    <div class="mt-3 space-y-2">
                        ${richDetails.opening_hours ? `<div class="flex items-center space-x-2 text-xs">
                            <span class="text-green-400">🕒</span>
                            <span class="text-gray-300">${richDetails.opening_hours}</span>
                        </div>` : ''}
                        ${richDetails.price_range ? `<div class="flex items-center space-x-2 text-xs">
                            <span class="text-yellow-400">💰</span>
                            <span class="text-gray-300">${richDetails.price_range}</span>
                        </div>` : ''}
                        ${richDetails.highlights && richDetails.highlights.length > 0 ? `<div class="flex items-start space-x-2 text-xs">
                            <span class="text-purple-400">✨</span>
                            <span class="text-gray-300">${richDetails.highlights.slice(0, 2).join(', ')}</span>
                        </div>` : ''}
                        ${richDetails.insider_tip ? `<div class="flex items-start space-x-2 text-xs">
                            <span class="text-blue-400">💡</span>
                            <span class="text-gray-300">${richDetails.insider_tip}</span>
                        </div>` : ''}
                    </div>
                `;
            }

        return `
            <div class="timeline-item bg-gray-800 rounded-xl p-4 border border-gray-700 hover:border-violet-500 transition-all duration-200 cursor-pointer" onclick="openModal('${item.context || ''}', '${item.title || ''}', '${item.description || ''}')">
                <div class="flex items-start space-x-3">
                    <div class="timeline-icon w-10 h-10 bg-violet-500 rounded-full flex items-center justify-center text-white font-bold text-sm shrink-0">
                        ${index + 1}
                    </div>
                    <div class="flex-grow min-w-0">
                        <div class="flex items-center space-x-2 mb-1">
                            <span class="text-lg">${icon}</span>
                            <h3 class="font-semibold text-white text-sm leading-tight">${item.title}</h3>
                            <span class="text-xs text-gray-400 ml-auto shrink-0">${timeDisplay}</span>
                        </div>
                        <p class="text-gray-300 text-xs leading-relaxed">${item.description}</p>
                        ${richDetailsHTML}
                    </div>
                </div>
            </div>
        `;
    }

// Placeholder for the modal opening function
function openModal(context, title, description) {
    console.log(`Opening modal for: ${title}`);
    console.log(`Context: ${context}, Description: ${description}`);
    // Implement modal display logic here. For now, just log.
    alert(`Details for ${title}:\n${description}\n(Context: ${context})`);
}

// Placeholder for the fallback modal
function showFallbackModal(context) {
    console.log(`Showing fallback modal for context: ${context}`);
    document.getElementById('modal-title').textContent = 'Informazioni non disponibili';
    document.getElementById('modal-summary').textContent = 'Mi dispiace, non è stato possibile caricare i dettagli per questa attrazione. Riprova più tardi.';
    document.getElementById('modal-details').innerHTML = '';
    document.getElementById('modal-tip').style.display = 'none';
    document.getElementById('details-modal').style.display = 'flex';
}


// --- MAP RELATED FUNCTIONS ---

let mapInstance = null;
let routeLayer = null;
let routeCoordinates = [];
let bounds = null;
let markerIndex = 1; // Initialize marker index

// Function to initialize the map
function initializeMap() {
    if (!mapInstance) {
        const mapContainer = document.getElementById('map'); // Assuming a map div with id 'map'
        if (!mapContainer) {
            console.error('Map container not found!');
            return;
        }
        mapInstance = L.map('map').setView([44.4071, 8.9237], 13); // Centered on Genova

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(mapInstance);

        // Initialize route layer and bounds
        routeLayer = L.layerGroup().addTo(mapInstance);
        bounds = L.latLngBounds();
    }
}

// Function to draw the route on the map
function drawRouteOnMap(itinerary) {
    initializeMap(); // Ensure map is initialized

    // Clear previous route and markers
    if (routeLayer) {
        routeLayer.clearLayers();
    }
    routeCoordinates = [];
    markerIndex = 1; // Reset marker index for new route

    itinerary.forEach((item, index) => {
        console.log(`Analizzando item ${index}:`, item);
        if (item.type !== 'tip') {
            console.log(`📍 Processando waypoint: ${item.title}, markerIndex attuale: ${markerIndex}`);
            // Rileva la città dall'itinerario
            const currentCity = window.currentCityName || 'genova';

            // Use coordinates from backend (lat/lon format) if available
            let lat, lng;
            if (item.lat && item.lon) {
                lat = item.lat;
                lng = item.lon;
                console.log(`✓ Coordinate dal backend per ${item.title}: ${lat}, ${lng}`);
            } else if (item.coordinates && Array.isArray(item.coordinates) && item.coordinates.length === 2) {
                // Array format [lat, lng] from backend
                lat = item.coordinates[0];
                lng = item.coordinates[1];
                console.log(`✓ Coordinate backend array per ${item.title}: ${lat}, ${lng}`);
            } else if (item.coordinates && item.coordinates.lat && item.coordinates.lng) {
                lat = item.coordinates.lat;
                lng = item.coordinates.lng;
                console.log(`✓ Coordinate dal backend (formato coordinates) per ${item.title}: ${lat}, ${lng}`);
            } else {
                console.log(`❌ ERRORE: Nessuna coordinata valida per ${item.title}`);
                console.log(`Dati ricevuti:`, item);

                // Fallback: try local database
                const realCoords = getRealCoordinates(item.title, currentCity);
                if (realCoords) {
                    lat = realCoords.lat;
                    lng = realCoords.lng;
                    console.log(`⚠ Coordinate locali per ${item.title}: ${lat}, ${lng}`);
                } else {
                    // Fallback to Genova instead of NYC to maintain consistency
                    console.log(`🚨 EMERGENCY: Nessuna coordinata per ${item.title} - usando Genova!`);
                    lat = 44.4063 + (index * 0.002);  // Genova + offset
                    lng = 8.9314 + (index * 0.002);
                    console.log(`🏛️ Genova fallback per ${item.title}: ${lat}, ${lng}`);
                }
            }

            // Add coordinates to the route
            routeCoordinates.push([lat, lng]);

            // Determine marker color based on type
            let markerColor = 'blue';
            if (item.transport === 'start') markerColor = 'green';
            else if (item.type === 'transport') markerColor = 'orange';

            // Different icon for starting point
            let markerIcon = markerIndex.toString();
            if (item.transport === 'start') {
                markerIcon = '🏁';
                console.log(`🏁 Punto di partenza: ${item.title}`);
            } else {
                console.log(`🔢 Assegnando numero ${markerIndex} a ${item.title}`);
            }
            markerIndex++; // Increment for EACH visible waypoint

            // Custom marker with sequential numbering
            const customIcon = L.divIcon({
                className: 'custom-marker activity-marker',
                html: `<div class="marker-content bg-${markerColor}-500 text-white rounded-full w-8 h-8 flex items-center justify-center font-bold text-xs border-2 border-white shadow-lg">${markerIcon}</div>`,
                iconSize: [32, 32],
                iconAnchor: [16, 16],
                popupAnchor: [0, -16]
            });

            const marker = L.marker([lat, lng], { icon: customIcon }).addTo(routeLayer);

            // Popup with stop information and transport icon
            const transportIcons = {
                'walking': '🚶',
                'metro': '🚇',
                'bus': '🚌',
                'tram': '🚋',
                'funicular': '🚡',
                'taxi': '🚕',
                'start': '🏁'
            };

            const transportIcon = transportIcons[item.transport] || '🚶';

            marker.bindPopup(`
                <div class="text-gray-900 max-w-xs">
                    <h3 class="font-bold text-sm mb-1">${item.title}</h3>
                    <p class="text-xs text-gray-600 mb-1">${item.time || ''} ${transportIcon}</p>
                    <p class="text-xs mb-2">${item.description}</p>
                    ${item.context && !item.type ? `<button onclick="openModal('${item.context}')" class="mt-1 text-xs bg-violet-500 text-white px-2 py-1 rounded">Più info</button>` : ''}
                </div>
            `);

            bounds.extend([lat, lng]);
        }
    });

    // Draw the route after all markers are placed
    if (routeCoordinates.length > 1) {
        drawRealisticRoute(routeCoordinates, routeLayer);
    }

    // Fit map to bounds if they exist
    if (bounds && !bounds.isInvalid()) {
        mapInstance.fitBounds(bounds);
    }
}

// --- REALISTIC ROUTING ---
        async function drawRealisticRoute(coordinates, layer) {
            console.log('🛣️ Disegno percorso semplificato per', coordinates.length, 'punti');

            // Instead of calling unreliable APIs, draw logical walking paths
            for (let i = 0; i < coordinates.length - 1; i++) {
                const start = coordinates[i];
                const end = coordinates[i + 1];

                // Calculate distance to determine route style
                const distance = Math.sqrt(
                    Math.pow(end[0] - start[0], 2) + Math.pow(end[1] - start[1], 2)
                ) * 111; // Rough km conversion

                let routeStyle = {
                    color: '#8b5cf6',
                    weight: 4,
                    opacity: 0.8,
                    lineCap: 'round',
                    lineJoin: 'round'
                };

                // Different styles for different distances
                if (distance > 1) { // Long distance - dashed line
                    routeStyle.dashArray = '15, 10';
                    routeStyle.color = '#f97316'; // Orange for transport
                } else if (distance < 0.3) { // Very short - thin line
                    routeStyle.weight = 2;
                    routeStyle.opacity = 0.6;
                }

                // Draw simple straight line (more reliable than API calls)
                const routeLine = L.polyline([start, end], routeStyle).addTo(layer);

                console.log(`✅ Percorso logico disegnato da punto ${i} a punto ${i+1} (${distance.toFixed(1)}km)`);
            }
        }