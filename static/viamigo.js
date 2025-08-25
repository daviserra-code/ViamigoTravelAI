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

        let response = `Ho trovato ${data.recommendations.length} ottimi consigli per te:\\n\\n`;
        
        data.recommendations.forEach((rec, index) => {
            response += `**${index + 1}. ${rec.destination}**\\n`;
            response += `${rec.description}\\n`;
            
            if (rec.estimated_cost) {
                response += `💰 Costo stimato: €${rec.estimated_cost}\\n`;
            }
            
            if (rec.best_time_to_visit) {
                response += `📅 Miglior periodo: ${rec.best_time_to_visit}\\n`;
            }
            
            if (rec.activities && rec.activities.length > 0) {
                response += `🎯 Attività: ${rec.activities.slice(0, 3).join(', ')}\\n`;
            }
            
            response += `\\n`;
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
        typingDiv.innerHTML = '<p class="text-sm text-gray-400">L\\'AI sta scrivendo...</p>';

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
            api.addMessageToChat('Mi dispiace, c\\'è stato un errore. Riprova tra un momento.');
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
                context: "walk"
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
            desc: rec.description,
            context: "museum"
        });

        // Add AI tip occasionally
        if (index === 0 && rec.local_tips && rec.local_tips.length > 0) {
            itineraryItems.push({
                type: "tip",
                title: "Consiglio dell'AI",
                desc: rec.local_tips[0]
            });
        }
    });

    renderCustomItinerary(itineraryItems, timelineContainer);
}

function renderCustomItinerary(items, container) {
    container.innerHTML = '';
    
    items.forEach(item => {
        if (item.type === 'tip') {
            container.innerHTML += `<div class="pro-tip relative my-4 ml-2 p-3 rounded-lg border-l-4 border-violet-500 bg-violet-900/50"><h4 class="font-bold text-white text-sm">${item.title}</h4><p class="text-sm text-gray-300">${item.desc}</p></div>`;
        } else {
            container.innerHTML += `
                <div class="timeline-item relative pb-8">
                    <div class="dot bg-gray-500"></div>
                    <div class="flex justify-between items-start">
                        <div>
                            <p class="text-xs text-gray-400 mb-1">${item.time}</p>
                            <h3 class="font-semibold text-white">${item.title}</h3>
                            <p class="text-sm text-gray-300">${item.desc}</p>
                        </div>
                        <button class="ai-button p-2 text-violet-400" data-context="${item.context}">
                            <svg class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor"><path d="M10 3.5a1.5 1.5 0 013 0V5a1.5 1.5 0 01-3 0V3.5zM10 8.5a1.5 1.5 0 013 0V10a1.5 1.5 0 01-3 0V8.5zM7 15l-1.5 1.5a1.5 1.5 0 01-3 0V15a1.5 1.5 0 013 0zm1.5-1.5a1.5 1.5 0 010-3H10a1.5 1.5 0 010 3h-1.5zm-1.5-2a1.5 1.5 0 013 0v1.5a1.5 1.5 0 01-3 0v-1.5zM10 13.5a1.5 1.5 0 013 0V15a1.5 1.5 0 01-3 0v-1.5z"/></svg>
                        </button>
                    </div>
                </div>`;
        }
    });
}