/**
 * MoodFlix Direct Recommendation Fix - v1.0
 * This script bypasses all the complexity of the existing system 
 * and directly renders recommendations from API responses
 */

console.log('*** MoodFlix Direct Recommendation Fix loaded ***');

// Wait for document to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Direct Fix: Document ready, initializing');
    
    // Display status indicator
    createStatusIndicator();
    
    // Add direct rendering
    setupDirectRendering();
    
    // Initial check
    setTimeout(checkForRecommendations, 1000);
    
    // Periodic check
    setInterval(checkForRecommendations, 3000);
});

// Create a small status indicator
function createStatusIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'recommendation-fix-status';
    indicator.style.position = 'fixed';
    indicator.style.bottom = '10px';
    indicator.style.right = '10px';
    indicator.style.backgroundColor = '#333';
    indicator.style.color = '#fff';
    indicator.style.padding = '5px 10px';
    indicator.style.borderRadius = '4px';
    indicator.style.fontSize = '12px';
    indicator.style.opacity = '0.8';
    indicator.style.zIndex = '9999';
    indicator.textContent = 'Recommendations: Initializing...';
    document.body.appendChild(indicator);
}

function updateStatus(text, type = 'info') {
    const indicator = document.getElementById('recommendation-fix-status');
    if (!indicator) return;
    
    indicator.textContent = 'Recommendations: ' + text;
    
    if (type === 'success') {
        indicator.style.backgroundColor = '#4CAF50';
    } else if (type === 'error') {
        indicator.style.backgroundColor = '#F44336';
    } else {
        indicator.style.backgroundColor = '#333';
    }
}

// Main function to fetch recommendations
function checkForRecommendations() {
    updateStatus('Checking...');
    
    // Get current session ID
    const sessionId = window.sessionId || 
                    localStorage.getItem('chat_session_id') || 
                    'fallback_session';
    
    // Direct API call to get latest recommendations
    fetch(`/api/check_response_v2?session_id=${sessionId}&timestamp=0`)
        .then(response => response.json())
        .then(data => {
            console.log('Direct API response:', data);
            
            if (data && data.recommendations && 
                Array.isArray(data.recommendations) && 
                data.recommendations.length > 0) {
                
                console.log(`Found ${data.recommendations.length} recommendations!`);
                directRenderRecommendations(data.recommendations);
                updateStatus(`Rendered ${data.recommendations.length} movies`, 'success');
            } else {
                console.log('No recommendations in API response');
                updateStatus('No new movies');
            }
        })
        .catch(err => {
            console.error('Error fetching recommendations:', err);
            updateStatus('Error fetching data', 'error');
        });
}

// Setup manual trigger
function setupDirectRendering() {
    const manualTriggerBtn = document.createElement('button');
    manualTriggerBtn.textContent = 'Show Recommendations';
    manualTriggerBtn.style.position = 'fixed';
    manualTriggerBtn.style.bottom = '40px';
    manualTriggerBtn.style.right = '10px';
    manualTriggerBtn.style.padding = '8px 16px';
    manualTriggerBtn.style.backgroundColor = '#E50914';
    manualTriggerBtn.style.color = 'white';
    manualTriggerBtn.style.border = 'none';
    manualTriggerBtn.style.borderRadius = '4px';
    manualTriggerBtn.style.cursor = 'pointer';
    manualTriggerBtn.style.zIndex = '9999';
    
    manualTriggerBtn.addEventListener('click', function() {
        checkForRecommendations();
    });
    
    document.body.appendChild(manualTriggerBtn);
}

// Direct rendering function
function directRenderRecommendations(recommendations) {
    // Always get a fresh reference to the container
    const container = document.getElementById('movie-recommendations');
    
    if (!container) {
        console.error('Cannot find recommendations container');
        return;
    }
    
    // Save for debugging
    window._currentRecommendations = recommendations;
    
    try {
        // Clear the container
        container.innerHTML = '';
        
        // Add heading
        const heading = document.createElement('h3');
        heading.textContent = 'Movie Recommendations';
        heading.style.color = '#E50914';
        heading.style.marginBottom = '15px';
        heading.style.borderBottom = '2px solid #333';
        heading.style.paddingBottom = '8px';
        container.appendChild(heading);
        
        // Create cards container
        const cardsContainer = document.createElement('div');
        cardsContainer.style.display = 'flex';
        cardsContainer.style.flexDirection = 'column';
        cardsContainer.style.gap = '10px';
        
        // Create cards for each movie
        recommendations.forEach((movie, index) => {
            try {
                const card = document.createElement('div');
                card.style.backgroundColor = '#2a2a2a';
                card.style.padding = '15px';
                card.style.borderRadius = '8px';
                card.style.marginBottom = '10px';
                card.style.cursor = 'pointer';
                card.style.transition = 'background-color 0.3s';
                
                // Hover effect
                card.onmouseover = function() { this.style.backgroundColor = '#3a3a3a'; };
                card.onmouseout = function() { this.style.backgroundColor = '#2a2a2a'; };
                
                // Title
                const title = document.createElement('div');
                title.textContent = movie.title || `Movie ${index+1}`;
                title.style.fontWeight = 'bold';
                title.style.fontSize = '1.1rem';
                title.style.marginBottom = '5px';
                title.style.color = '#fff';
                card.appendChild(title);
                
                // Year if available
                if (movie.year) {
                    const year = document.createElement('div');
                    year.textContent = `(${movie.year})`;
                    year.style.color = '#aaa';
                    year.style.fontSize = '0.9rem';
                    year.style.marginBottom = '5px';
                    card.appendChild(year);
                }
                
                // Genres if available
                if (movie.genres && movie.genres.length > 0) {
                    const genres = document.createElement('div');
                    genres.textContent = Array.isArray(movie.genres) ? movie.genres.join(', ') : movie.genres;
                    genres.style.color = '#E50914';
                    genres.style.fontSize = '0.85rem';
                    genres.style.marginBottom = '10px';
                    card.appendChild(genres);
                }
                
                // Plot if available
                if (movie.plot) {
                    const plot = document.createElement('div');
                    plot.textContent = movie.plot.length > 150 ? movie.plot.substring(0, 150) + '...' : movie.plot;
                    plot.style.fontSize = '0.9rem';
                    plot.style.color = '#ddd';
                    plot.style.lineHeight = '1.4';
                    card.appendChild(plot);
                }
                
                // Click event
                card.addEventListener('click', function() {
                    const messageInput = document.getElementById('message-input');
                    if (messageInput) {
                        messageInput.value = `Tell me more about "${movie.title}"`;
                        const sendButton = document.getElementById('send-button');
                        if (sendButton) {
                            sendButton.click();
                        }
                    }
                });
                
                cardsContainer.appendChild(card);
            } catch (error) {
                console.error('Error creating movie card:', error);
            }
        });
        
        container.appendChild(cardsContainer);
        console.log('Successfully displayed all recommendation cards');
    } catch (error) {
        console.error('Error rendering recommendations:', error);
    }
}
