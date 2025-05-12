/**
 * MoodFlix Recommendation Bridge
 * Intercepts API responses and bridges them to the existing displayMovieRecommendations function
 */

console.log('MoodFlix Recommendation Bridge - v1.0 loaded');

// Wait for document to be ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Recommendation Bridge: Initializing');
    
    // Start intercepting API responses after a short delay
    setTimeout(setupInterceptors, 500);
});

// Set up API interceptors
function setupInterceptors() {
    // Look for the existing displayMovieRecommendations function
    if (typeof window.displayMovieRecommendations !== 'function') {
        console.error('Recommendation Bridge: displayMovieRecommendations function not found!');
        return;
    }
    
    console.log('Recommendation Bridge: Found displayMovieRecommendations function');
    
    // Intercept XHR responses
    interceptXHR();
    
    // Intercept Fetch responses
    interceptFetch();
    
    // Start periodic polling
    startPolling();
}

// Intercept XMLHttpRequest
function interceptXHR() {
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function() {
        this._url = arguments[1];
        return originalOpen.apply(this, arguments);
    };
    
    XMLHttpRequest.prototype.send = function() {
        const originalOnload = this.onload;
        
        this.onload = function() {
            if (originalOnload) {
                originalOnload.apply(this, arguments);
            }
            
            try {
                // Only process specific endpoints
                if (this._url && typeof this._url === 'string' && 
                    (this._url.includes('/api/real_time_text_v2') || 
                     this._url.includes('/api/check_response_v2'))) {
                    
                    const data = JSON.parse(this.responseText);
                    processResponse(data);
                }
            } catch (error) {
                console.error('Error processing XHR response:', error);
            }
        };
        
        return originalSend.apply(this, arguments);
    };
    
    console.log('Recommendation Bridge: XHR interceptor set up');
}

// Intercept Fetch
function interceptFetch() {
    const originalFetch = window.fetch;
    
    window.fetch = function() {
        const fetchPromise = originalFetch.apply(this, arguments);
        const url = arguments[0];
        
        if (typeof url === 'string' && 
            (url.includes('/api/real_time_text_v2') || 
             url.includes('/api/check_response_v2'))) {
            
            fetchPromise.then(response => {
                const clonedResponse = response.clone();
                
                clonedResponse.json()
                    .then(data => {
                        processResponse(data);
                    })
                    .catch(error => {
                        console.error('Error parsing fetch response:', error);
                    });
            });
        }
        
        return fetchPromise;
    };
    
    console.log('Recommendation Bridge: Fetch interceptor set up');
}

// Process API response
function processResponse(data) {
    if (data && data.recommendations && 
        Array.isArray(data.recommendations) && 
        data.recommendations.length > 0) {
        
        console.log('Recommendation Bridge: Found recommendations in response', data.recommendations.length);
        console.log('Recommendation data:', JSON.stringify(data.recommendations, null, 2));
        
        // Try multiple approaches to display recommendations
        // 1. Try the window function first
        if (typeof window.displayMovieRecommendations === 'function') {
            console.log('Using window.displayMovieRecommendations');
            window.displayMovieRecommendations(data.recommendations);
        }
        
        // 2. Try direct access to the real_time_chat.js function
        if (typeof displayMovieRecommendations === 'function') {
            console.log('Using displayMovieRecommendations directly');
            displayMovieRecommendations(data.recommendations);
        }
        
        // 3. As a fallback, try direct DOM manipulation
        const container = document.getElementById('movie-recommendations');
        if (container) {
            console.log('Using direct DOM manipulation as fallback');
            renderFallbackRecommendations(container, data.recommendations);
        }
    }
}

// Fallback renderer for when other methods fail
function renderFallbackRecommendations(container, movies) {
    // Clear existing content
    container.innerHTML = '';
    
    // Create a heading
    const heading = document.createElement('h3');
    heading.textContent = 'Movie Recommendations';
    heading.style.color = '#E50914';
    heading.style.marginBottom = '15px';
    container.appendChild(heading);
    
    // Create movie cards
    movies.forEach(movie => {
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.style.backgroundColor = '#333';
        card.style.borderRadius = '8px';
        card.style.padding = '15px';
        card.style.marginBottom = '15px';
        
        // Build card content
        const title = document.createElement('h4');
        title.textContent = movie.title;
        title.style.color = 'white';
        title.style.marginBottom = '5px';
        
        const details = document.createElement('div');
        details.innerHTML = `
            <p style="margin: 5px 0; color: #aaa;">Year: ${movie.year || 'Unknown'}</p>
            <p style="margin: 5px 0; color: #E50914;">${Array.isArray(movie.genres) ? movie.genres.join(', ') : movie.genres || 'Unknown genre'}</p>
            <p style="margin: 10px 0; color: #ddd;">${movie.plot || 'No plot available'}</p>
        `;
        
        // Add to card
        card.appendChild(title);
        card.appendChild(details);
        container.appendChild(card);
    });
    
    // Make sure it's visible
    container.style.display = 'block';
}

// Direct polling for recommendations
function startPolling() {
    setInterval(pollForRecommendations, 3000);
    
    // Initial poll
    setTimeout(pollForRecommendations, 1000);
}

// Poll for recommendations
function pollForRecommendations() {
    // Get the current session ID
    const sessionId = window.sessionId || 
                     localStorage.getItem('chat_session_id') || 
                     'fallback_session';
    
    fetch(`/api/check_response_v2?session_id=${sessionId}&timestamp=0`)
        .then(response => response.json())
        .then(data => {
            if (data && data.recommendations) {
                processResponse(data);
            }
        })
        .catch(error => {
            console.error('Error in direct polling:', error);
        });
}

// Add a debug button to force recommendations check
function addDebugButton() {
    const button = document.createElement('button');
    button.textContent = 'Check Recs';
    button.style.position = 'fixed';
    button.style.bottom = '10px';
    button.style.left = '10px';
    button.style.zIndex = '9999';
    button.style.padding = '5px 10px';
    button.style.backgroundColor = '#E50914';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '4px';
    
    button.addEventListener('click', pollForRecommendations);
    
    document.body.appendChild(button);
}

// Add debug button after a delay
setTimeout(addDebugButton, 2000);
