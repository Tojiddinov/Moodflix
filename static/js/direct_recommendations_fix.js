// Direct Recommendations Fix - Version 1.0
console.log('Direct Recommendations Fix loaded!');

// Wait for document to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Setting up direct recommendations fix');
    
    // Create debug UI
    const debugButton = document.createElement('button');
    debugButton.textContent = 'Fix Recommendations';
    debugButton.style.position = 'fixed';
    debugButton.style.bottom = '10px';
    debugButton.style.left = '10px';
    debugButton.style.zIndex = '10000';
    debugButton.style.backgroundColor = '#4CAF50';
    debugButton.style.color = 'white';
    debugButton.style.border = 'none';
    debugButton.style.borderRadius = '4px';
    debugButton.style.padding = '10px 15px';
    debugButton.style.cursor = 'pointer';
    
    // Add to page
    document.body.appendChild(debugButton);
    
    // Set up direct API poll
    debugButton.addEventListener('click', function() {
        console.log('Manual recommendations fix triggered');
        checkForRecommendations();
    });
    
    // Set up periodic checking
    setInterval(checkForRecommendations, 5000);
    
    // Initial check
    setTimeout(checkForRecommendations, 1000);
    
    // Main function to check for and display recommendations
    function checkForRecommendations() {
        // Get current session ID
        const sessionId = localStorage.getItem('chat_session_id') || 
                         window.sessionId || 
                         document.querySelector('meta[name="session-id"]')?.content || 
                         'fallback_session';
        
        // Make direct API call
        fetch(`/api/check_response_v2?session_id=${sessionId}&timestamp=0`)
            .then(response => response.json())
            .then(data => {
                console.log('Direct API fetch for recommendations:', data);
                
                if (data && data.recommendations && Array.isArray(data.recommendations) && data.recommendations.length > 0) {
                    console.log(`Found ${data.recommendations.length} recommendations from API`);
                    displayRecommendations(data.recommendations);
                } else {
                    console.log('No recommendations in API response');
                }
            })
            .catch(error => {
                console.error('Error fetching recommendations:', error);
            });
    }
    
    // Direct display function that doesn't rely on existing code
    function displayRecommendations(recommendations) {
        // Find the container
        const container = document.getElementById('movie-recommendations');
        if (!container) {
            console.error('Cannot find movie-recommendations container');
            return;
        }
        
        console.log(`Displaying ${recommendations.length} recommendations directly`);
        
        // Clear container
        container.innerHTML = '';
        
        // Add header
        const header = document.createElement('h3');
        header.textContent = 'Movie Recommendations';
        header.style.color = '#E50914';
        header.style.marginBottom = '15px';
        header.style.paddingBottom = '8px';
        header.style.borderBottom = '2px solid #333';
        container.appendChild(header);
        
        // Create container for cards
        const cardsContainer = document.createElement('div');
        cardsContainer.style.display = 'flex';
        cardsContainer.style.flexDirection = 'column';
        cardsContainer.style.gap = '10px';
        
        // Create a card for each recommendation
        recommendations.forEach(movie => {
            const card = document.createElement('div');
            card.style.backgroundColor = '#2a2a2a';
            card.style.padding = '15px';
            card.style.borderRadius = '8px';
            card.style.marginBottom = '10px';
            card.style.cursor = 'pointer';
            
            // Add hover effect
            card.onmouseover = function() { this.style.backgroundColor = '#3a3a3a'; };
            card.onmouseout = function() { this.style.backgroundColor = '#2a2a2a'; };
            
            // Add title
            const title = document.createElement('div');
            title.textContent = movie.title || 'Unknown Title';
            title.style.fontWeight = 'bold';
            title.style.fontSize = '18px';
            title.style.marginBottom = '5px';
            title.style.color = '#fff';
            card.appendChild(title);
            
            // Add year if available
            if (movie.year) {
                const year = document.createElement('div');
                year.textContent = `(${movie.year})`;
                year.style.color = '#aaa';
                year.style.fontSize = '14px';
                year.style.marginBottom = '5px';
                card.appendChild(year);
            }
            
            // Add genres if available
            if (movie.genres && movie.genres.length > 0) {
                const genres = document.createElement('div');
                genres.textContent = Array.isArray(movie.genres) ? movie.genres.join(', ') : movie.genres;
                genres.style.color = '#E50914';
                genres.style.fontSize = '14px';
                genres.style.marginBottom = '10px';
                card.appendChild(genres);
            }
            
            // Add plot if available
            if (movie.plot) {
                const plot = document.createElement('div');
                plot.textContent = movie.plot;
                plot.style.fontSize = '14px';
                plot.style.color = '#ddd';
                plot.style.lineHeight = '1.4';
                card.appendChild(plot);
            }
            
            // Add click handler
            card.addEventListener('click', function() {
                const messageInput = document.getElementById('message-input');
                if (messageInput) {
                    messageInput.value = `Tell me more about "${movie.title}"`;
                    
                    // Find and click send button
                    const sendButton = document.getElementById('send-button');
                    if (sendButton) {
                        sendButton.click();
                    }
                }
            });
            
            // Add card to container
            cardsContainer.appendChild(card);
        });
        
        // Add cards to main container
        container.appendChild(cardsContainer);
        console.log('Recommendations displayed successfully');
    }
});
