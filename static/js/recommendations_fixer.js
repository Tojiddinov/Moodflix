// Enhanced Recommendations Handler
console.log('Enhanced Recommendations Handler v5.0 DEBUGGING loaded!');

// Global reference to the recommendations container
let movieRecommendationsElement = null;

// Store the global reference from the template
let originalMovieRecommendations = null;

// Enable detailed debugging
const DEBUG = true;

// More robust logging
function debugLog(...args) {
    if (DEBUG) {
        console.log('[RecommendationDebug]', ...args);
    }


// Initialize DOM references when the document loads
function initializeReferences() {
    movieRecommendationsElement = document.getElementById('movie-recommendations');
    if (!movieRecommendationsElement) {
        console.error('Movie recommendations container not found! Make sure the HTML includes a div with id="movie-recommendations"');
    } else {
        console.log('Movie recommendations container found and initialized');
    }
}

// Create a debug button to force recommendations display
function createDebugButton() {
    // Check if the button already exists
    if (document.getElementById('debug-recommendations-button')) {
        return;
    }

    // Create button container
    const debugContainer = document.createElement('div');
    debugContainer.style.position = 'fixed';
    debugContainer.style.bottom = '10px';
    debugContainer.style.right = '10px';
    debugContainer.style.zIndex = '9999';

    // Create button
    const debugButton = document.createElement('button');
    debugButton.id = 'debug-recommendations-button';
    debugButton.textContent = 'Debug Recommendations';
    debugButton.style.backgroundColor = '#E50914';
    debugButton.style.color = 'white';
    debugButton.style.border = 'none';
    debugButton.style.borderRadius = '4px';
    debugButton.style.padding = '8px 16px';
    debugButton.style.cursor = 'pointer';
    debugButton.style.fontWeight = 'bold';
    debugButton.style.boxShadow = '0 2px 5px rgba(0,0,0,0.3)';

    // Add click handler
    debugButton.addEventListener('click', function() {
        console.log('Manually triggering recommendations display');
        const testMovies = [
            {
                title: 'The Shawshank Redemption',
                year: 1994,
                plot: 'Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.',
                genres: ['Drama']
            },
            {
                title: 'The Godfather',
                year: 1972, 
                plot: 'The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.',
                genres: ['Crime', 'Drama']
            },
            {
                title: 'The Dark Knight',
                year: 2008,
                plot: 'When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.',
                genres: ['Action', 'Crime', 'Drama']
            }
        ];
        renderMovieRecommendations(testMovies);
    });

    // Add to container and page
    debugContainer.appendChild(debugButton);
    document.body.appendChild(debugContainer);
}

// Main recommendation rendering function - SIMPLIFIED VERSION
function renderMovieRecommendations(recommendations) {
    console.log('SIMPLIFIED RENDERING SYSTEM ACTIVATED');
    console.log('Recommendations provided:', recommendations ? recommendations.length : 0);
    
    // CRITICAL FIX: Always get a fresh reference to avoid stale DOM references
    const container = document.getElementById('movie-recommendations');
    console.log('Container exists:', !!container);
    
    if (!container) {
        console.error('CRITICAL: Recommendations container not found!');
        return;
    }
    
    // Store recommendations for debug
    window._lastRecommendations = recommendations;
    
    try {
        // Clear existing content
        container.innerHTML = '';
        console.log('Container cleared');
        
        // Simple heading
        const heading = document.createElement('h3');
        heading.textContent = 'Movie Recommendations';
        heading.style.color = '#E50914';
        heading.style.padding = '10px 0';
        heading.style.borderBottom = '2px solid #333';
        heading.style.marginBottom = '15px';
        container.appendChild(heading);
        console.log('Heading added');
    
        // Check if we have valid recommendations
        if (!recommendations || !Array.isArray(recommendations) || recommendations.length === 0) {
            const message = document.createElement('div');
            message.textContent = 'No recommendations available. Try asking about a specific movie genre or mood.';
            message.style.padding = '15px';
            message.style.color = '#aaa';
            container.appendChild(message);
            console.log('No recommendations message added');
            return;
        }
        
        // Create container for the movie cards
        const cardsList = document.createElement('div');
        cardsList.style.display = 'flex';
        cardsList.style.flexDirection = 'column';
        cardsList.style.gap = '10px';
        console.log('Creating cards for', recommendations.length, 'recommendations');
        
        // Process each recommendation
        recommendations.forEach((movie, index) => {
            try {
                // Extract movie properties
                const title = movie.title || (typeof movie === 'string' ? movie : `Movie ${index+1}`);
                const year = movie.year || '';
                const plot = movie.plot || movie.description || '';
                const genres = movie.genres || [];
                
                // Create movie card with direct inline styles
                const card = document.createElement('div');
                card.className = 'movie-recommendation-card';
                card.style.backgroundColor = '#2a2a2a';
                card.style.padding = '15px';
                card.style.borderRadius = '8px';
                card.style.cursor = 'pointer';
                card.style.transition = 'background-color 0.3s';
                
                // Add hover effect
                card.onmouseover = function() { this.style.backgroundColor = '#3a3a3a'; };
                card.onmouseout = function() { this.style.backgroundColor = '#2a2a2a'; };
                
                // Create title element
                const titleEl = document.createElement('div');
                titleEl.textContent = title;
                titleEl.style.fontWeight = 'bold';
                titleEl.style.fontSize = '1.1rem';
                titleEl.style.marginBottom = '5px';
                titleEl.style.color = '#fff';
                card.appendChild(titleEl);
                
                // Add year if available
                if (year) {
                    const yearEl = document.createElement('div');
                    yearEl.textContent = `(${year})`;
                    yearEl.style.color = '#aaa';
                    yearEl.style.fontSize = '0.9rem';
                    yearEl.style.marginBottom = '5px';
                    card.appendChild(yearEl);
                }
                
                // Add genres if available
                if (genres && genres.length > 0) {
                    const genresEl = document.createElement('div');
                    genresEl.textContent = Array.isArray(genres) ? genres.join(', ') : genres;
                    genresEl.style.color = '#E50914';
                    genresEl.style.fontSize = '0.85rem';
                    genresEl.style.marginBottom = '10px';
                    card.appendChild(genresEl);
                }
                
                // Add plot if available
                if (plot) {
                    const plotEl = document.createElement('div');
                    plotEl.textContent = plot.length > 150 ? plot.substring(0, 150) + '...' : plot;
                    plotEl.style.fontSize = '0.9rem';
                    plotEl.style.color = '#ddd';
                    plotEl.style.lineHeight = '1.4';
                    card.appendChild(plotEl);
                }
                
                // Add click event to get more details about this movie
                card.addEventListener('click', function() {
                    const messageInput = document.getElementById('message-input');
                    if (messageInput) {
                        messageInput.value = `Tell me more about ${title}`;
                        const sendButton = document.getElementById('send-button');
                        if (sendButton) {
                            sendButton.click();
                        }
                    }
                });
            
                // Add to container
                cardsList.appendChild(card);
                console.log(`Added movie card for: ${title}`);
            } catch (error) {
                console.error('Error creating movie card:', error);
            }
        });
    
        // Add all cards to the container
        container.appendChild(cardsList);
        console.log(`Successfully displayed ${recommendations.length} movie recommendations`);
            
    } catch (error) {
        console.error('Error rendering recommendations:', error);
    }
}

// Response interceptor for directly handling the recommendations
function setupResponseInterceptor() {
    // Override fetch to intercept API responses
    const originalFetch = window.fetch;
    window.fetch = function() {
        const fetchPromise = originalFetch.apply(this, arguments);
        
        // Store original URL for logging
        const url = arguments[0];
        
        // Process all API responses
        fetchPromise.then(response => {
            // Only process certain API endpoints
            if (typeof url === 'string' && (
                url.includes('/api/real_time_text_v2') || 
                url.includes('/api/check_response_v2'))) {
                
                console.log(`Intercepted response from ${url}`);
                
                // Clone the response to avoid consuming it
                const clonedResponse = response.clone();
                
                // Try to parse the JSON
                clonedResponse.json()
                    .then(data => {
                        console.log('Response data:', data);
                        
                        // Check for recommendations and render them
                        if (data && data.recommendations && 
                            Array.isArray(data.recommendations) && 
                            data.recommendations.length > 0) {
                            
                            console.log('🎬 Found recommendations in response:', data.recommendations.length);
                            renderMovieRecommendations(data.recommendations);
                        }
                    })
                    .catch(error => {
                        console.error('Error parsing JSON response:', error);
                    });
            }
        }).catch(error => {
            console.error('Fetch error:', error);
        });
        
        // Return the original promise to not break normal functionality
        return fetchPromise;
    };
    
    // Also intercept XHR requests
    const originalXHROpen = XMLHttpRequest.prototype.open;
    const originalXHRSend = XMLHttpRequest.prototype.send;
    
    XMLHttpRequest.prototype.open = function() {
        this._url = arguments[1];
        return originalXHROpen.apply(this, arguments);
    };
    
    XMLHttpRequest.prototype.send = function() {
        // Store original onload
        const originalOnload = this.onload;
        
        // Add our interceptor
        this.onload = function() {
            // Call original onload first
            if (originalOnload) originalOnload.apply(this, arguments);
            
            // Check if this is an API response we care about
            if (this._url && typeof this._url === 'string' && (
                this._url.includes('/api/real_time_text_v2') || 
                this._url.includes('/api/check_response_v2'))) {
                
                console.log(`Intercepted XHR response from ${this._url}`);
                
                try {
                    // Parse response text
                    const data = JSON.parse(this.responseText);
                    console.log('XHR Response data structure:', Object.keys(data));
                    
                    // Check for recommendations - with extra debugging
                    if (data) {
                        console.log('Response data exists');
                        
                        if (data.recommendations) {
                            console.log('Recommendations field exists');
                            console.log('Recommendations type:', typeof data.recommendations);
                            
                            // Analyze the recommendations data
                            if (Array.isArray(data.recommendations)) {
                                console.log('Recommendations is an array of length:', data.recommendations.length);
                                console.log('First recommendation:', data.recommendations.length > 0 ? JSON.stringify(data.recommendations[0]).substring(0, 100) : 'empty array');
                                
                                if (data.recommendations.length > 0) {
                                    console.log('🎬 Found valid recommendations in XHR response');
                                    // Try both with window function and direct rendering
                                    if (typeof window.displayRecommendations === 'function') {
                                        console.log('Using window.displayRecommendations');
                                        window.displayRecommendations(data.recommendations);
                                    }
                                    console.log('Also using renderMovieRecommendations directly');
                                    renderMovieRecommendations(data.recommendations);
                                }
                            } else {
                                console.log('Recommendations is not an array, trying to convert...');
                                try {
                                    // Sometimes the recommendations might be stringified
                                    if (typeof data.recommendations === 'string') {
                                        const parsed = JSON.parse(data.recommendations);
                                        if (Array.isArray(parsed) && parsed.length > 0) {
                                            console.log('Successfully parsed recommendations string to array');
                                            renderMovieRecommendations(parsed);
                                        }
                                    }
                                } catch (parseError) {
                                    console.error('Error parsing recommendations string:', parseError);
                                }
                            }
                        } else {
                            console.log('No recommendations field in response');
                        }
                    }
                } catch (error) {
                    console.error('Error processing XHR response:', error);
                }
            }
        };
        
        return originalXHRSend.apply(this, arguments);
    };
}

// Handle polling function enhancement
function enhancePollFunction() {
    // Try to find the polling function in the page
    if (typeof window.pollForResponses === 'function') {
        console.log('Enhancing existing pollForResponses function');
        
        // Save original function
        const originalPoll = window.pollForResponses;
        
        // Replace with our enhanced version
        window.pollForResponses = function() {
            console.log('Enhanced pollForResponses called');
            
            // Call original to maintain functionality
            const result = originalPoll.apply(this, arguments);
            
            // Get the URL being used
            const sessionId = window.sessionId || '';
            const timestamp = window.lastTimestamp || Date.now() / 1000;
            
            // Make an additional direct fetch to ensure we get recommendations
            setTimeout(() => {
                fetch(`/api/check_response_v2?session_id=${sessionId}&timestamp=${timestamp}`)
                    .then(response => response.json())
                    .then(data => {
                        console.log('Direct poll response:', data);
                        
                        if (data && data.recommendations && 
                            Array.isArray(data.recommendations) && 
                            data.recommendations.length > 0) {
                            
                            console.log('Found recommendations in direct poll');
                            renderMovieRecommendations(data.recommendations);
                        }
                    })
                    .catch(error => {
                        console.error('Error in direct poll:', error);
                    });
            }, 500);
            
            return result;
        };
        
        console.log('Polling function enhanced');
    }
}

// Override the display recommendations function
function overrideDisplayRecommendations() {
    if (typeof window.displayRecommendations === 'function') {
        console.log('Overriding existing displayRecommendations function');
        
        // Save original function as backup
        window._originalDisplayRecommendations = window.displayRecommendations;
        
        // Replace with our version
        window.displayRecommendations = function(recommendations) {
            console.log('Enhanced displayRecommendations called with:', recommendations);
            renderMovieRecommendations(recommendations);
        };
    } else {
        console.log('Creating new displayRecommendations function');
        window.displayRecommendations = renderMovieRecommendations;
    }
    
    // Sync the global variable used in the HTML template with our element
    if (window.movieRecommendations === undefined) {
        console.log('Setting global movieRecommendations variable');
        window.movieRecommendations = document.getElementById('movie-recommendations');
    }
}

// Main initialization function to run when document is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('Document ready - initializing enhanced recommendations handler');
    
    // Initialize DOM references first
    initializeReferences();
    
    // Set up all our enhancements
    setupResponseInterceptor();
    overrideDisplayRecommendations();
    enhancePollFunction();
    createDebugButton();
    
    // Add a special debug button to bypass all the normal flow
    const debugFixButton = document.createElement('button');
    debugFixButton.textContent = 'Force Direct Recommendations';
    debugFixButton.style.position = 'fixed';
    debugFixButton.style.top = '10px';
    debugFixButton.style.right = '10px';
    debugFixButton.style.zIndex = '10000';
    debugFixButton.style.padding = '10px';
    debugFixButton.style.backgroundColor = '#ff4500';
    debugFixButton.style.color = 'white';
    debugFixButton.style.border = 'none';
    debugFixButton.style.borderRadius = '5px';
    
    debugFixButton.addEventListener('click', function() {
        console.log('DIRECT FIX button clicked');
        
        // This is the sample recommendations format from the terminal output
        const directRecs = [
            {
                'title': 'running forever',
                'year': 2000,
                'genres': ['Family'],
                'actors': ['David Raizor', 'Cody Howard', 'Martin Kove'],
                'directors': ['Mike Mayhall'],
                'mood': ['neutral'],
                'themes': ['Family'],
                'plot': 'A family movie directed by Mike Mayhall, starring David Raizor, Cody Howard and Martin Kove.',
                'index': 0
            },
            {
                'title': 'rodeo girl',
                'year': 2000,
                'genres': ['Family'],
                'actors': ['Carrie Bradstreet', 'Joel Paul Reisig', 'Yassie Hawkes'],
                'directors': ['Joel Paul Reisig'],
                'mood': ['neutral'],
                'themes': ['Family'],
                'plot': 'A family movie directed by Joel Paul Reisig, starring Carrie Bradstreet, Joel Paul Reisig and Yassie Hawkes.',
                'index': 1
            },
            {
                'title': 'the little ponderosa zoo',
                'year': 2000,
                'genres': ['Family'],
                'actors': ['Mike Stanley', 'Jeff Delaney', 'Jamison Stalsworth'],
                'directors': ['Luke Dye'],
                'mood': ['neutral'],
                'themes': ['Family'],
                'plot': 'A family movie directed by Luke Dye, starring Mike Stanley, Jeff Delaney and Jamison Stalsworth.',
                'index': 2
            }
        ];
        
        // Get a direct reference to the container
        const container = document.getElementById('movie-recommendations');
        console.log('Direct container access:', !!container);
        
        if (container) {
            // Manual direct rendering
            container.innerHTML = '';
            
            // Add a heading
            const heading = document.createElement('h3');
            heading.textContent = 'DIRECT Movies';
            heading.style.color = '#E50914';
            heading.style.marginBottom = '15px';
            container.appendChild(heading);
            
            // Create movie cards container
            const cardsContainer = document.createElement('div');
            cardsContainer.style.display = 'flex';
            cardsContainer.style.flexDirection = 'column';
            cardsContainer.style.gap = '10px';
            
            // Create cards for each movie
            directRecs.forEach(movie => {
                const card = document.createElement('div');
                card.style.backgroundColor = '#333';
                card.style.padding = '15px';
                card.style.borderRadius = '8px';
                card.style.marginBottom = '10px';
                
                const title = document.createElement('div');
                title.textContent = movie.title;
                title.style.fontWeight = 'bold';
                title.style.fontSize = '18px';
                title.style.marginBottom = '5px';
                
                const details = document.createElement('div');
                details.textContent = movie.plot;
                details.style.fontSize = '14px';
                details.style.color = '#ccc';
                
                card.appendChild(title);
                card.appendChild(details);
                cardsContainer.appendChild(card);
            });
            
            container.appendChild(cardsContainer);
            console.log('Direct rendering complete');
        } else {
            console.error('Could not find recommendations container for direct rendering');
        }
    });
    
    document.body.appendChild(debugFixButton);
    
    // Force initial test display
    setTimeout(() => {
        console.log('Triggering initial test display');
        const testMovies = [
            {
                title: 'Test Movie 1',
                year: 2023,
                plot: 'This is a test recommendation to verify the display is working properly.',
                genres: ['Test']
            },
            {
                title: 'Test Movie 2',
                year: 2023,
                plot: 'Second test recommendation to ensure multiple cards display correctly.',
                genres: ['Test']
            }
        ];
        renderMovieRecommendations(testMovies);
    }, 2000);
    
    console.log('Enhanced recommendations handler initialized successfully');
});
// End of the file
}
