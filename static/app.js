/**
 * MoodFlix Application JavaScript
 * Handles interactions with the MoodFlix API
 */

// Global state
const state = {
    currentUser: null,
    recommendations: [],
    history: [],
    trendingMovies: []
};

// API endpoints
const API = {
    CHAT: '/api/chat',
    VOICE: '/api/voice',
    HISTORY: '/api/history',
    MOVIE_DETAILS: '/api/movie_details',
    SIMILAR_MOVIES: '/api/similar_movies',
    SET_VOLUME: '/api/set_volume',
    MOVIEBUDDY: '/api/moviebuddy'
};

// DOM elements
document.addEventListener('DOMContentLoaded', () => {
    // Initialize UI components
    initializeMoodButtons();
    initializeVoiceInput();
    initializeSearchBox();
    loadTrendingMovies();
    
    // Check if on movie details page
    const movieTitle = document.getElementById('movie-title');
    if (movieTitle) {
        loadMovieDetails(movieTitle.dataset.title);
    }
    
    // Check if on profile page
    if (document.getElementById('user-profile')) {
        loadUserHistory();
    }
});

/**
 * Initialize mood buttons
 */
function initializeMoodButtons() {
    const moodButtons = document.querySelectorAll('.mood-button');
    if (!moodButtons.length) return;
    
    moodButtons.forEach(button => {
        button.addEventListener('click', () => {
            const mood = button.dataset.mood;
            getRecommendationsByMood(mood);
        });
    });
}

/**
 * Initialize voice input
 */
function initializeVoiceInput() {
    const voiceButton = document.getElementById('voice-input-button');
    if (!voiceButton) return;
    
    let isRecording = false;
    let mediaRecorder;
    let audioChunks = [];
    
    voiceButton.addEventListener('click', () => {
        if (isRecording) {
            // Stop recording
            mediaRecorder.stop();
            voiceButton.textContent = 'Start Voice Input';
            voiceButton.classList.remove('recording');
            isRecording = false;
        } else {
            // Start recording
            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(stream => {
                    mediaRecorder = new MediaRecorder(stream);
                    mediaRecorder.start();
                    
                    mediaRecorder.addEventListener('dataavailable', event => {
                        audioChunks.push(event.data);
                    });
                    
                    mediaRecorder.addEventListener('stop', () => {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        audioChunks = [];
                        
                        // Send audio to server
                        sendVoiceInput(audioBlob);
                        
                        // Stop all tracks
                        stream.getTracks().forEach(track => track.stop());
                    });
                    
                    voiceButton.textContent = 'Stop Recording';
                    voiceButton.classList.add('recording');
                    isRecording = true;
                })
                .catch(error => {
                    console.error('Error accessing microphone:', error);
                    showError('Could not access microphone. Please check permissions.');
                });
        }
    });
}

/**
 * Initialize search box
 */
function initializeSearchBox() {
    const searchBox = document.getElementById('search-box');
    if (!searchBox) return;
    
    searchBox.addEventListener('keypress', event => {
        if (event.key === 'Enter') {
            event.preventDefault();
            const query = searchBox.value.trim();
            if (query) {
                getChatRecommendations(query);
            }
        }
    });
}

/**
 * Load trending movies
 */
function loadTrendingMovies() {
    const trendingSlider = document.querySelector('.trending-slider');
    if (!trendingSlider) return;
    
    // For now, we'll use dummy data
    // In a real implementation, this would call an API endpoint
    const dummyMovies = [
        { title: 'Dune', image: 'dune.jpg' },
        { title: 'Joker', image: 'jok.jpg' },
        { title: 'Gladiator', image: 'glad.jpg' },
        { title: 'Venom', image: 'venom.jpg' },
        { title: 'Saturday Night', image: 'saturdaynight.jpg' }
    ];
    
    dummyMovies.forEach(movie => {
        const movieCard = document.createElement('div');
        movieCard.className = 'movie-card';
        movieCard.innerHTML = `
            <a href="#" data-title="${movie.title}">
                <img src="/static/${movie.image}" alt="${movie.title}">
                <div class="overlay">${movie.title}</div>
            </a>
        `;
        trendingSlider.appendChild(movieCard);
        
        // Add click event
        movieCard.querySelector('a').addEventListener('click', (event) => {
            event.preventDefault();
            loadMovieDetails(movie.title);
        });
    });
}

/**
 * Get recommendations by mood
 */
function getRecommendationsByMood(mood) {
    showLoader();
    
    // Create message based on mood
    const message = `I'm feeling ${mood} today. Can you recommend some movies?`;
    
    // Send to chat API
    fetch(API.CHAT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();
        if (data.type === 'recommendations') {
            displayRecommendations(data.movies);
        } else {
            showError(data.message || 'Could not get recommendations');
        }
    })
    .catch(error => {
        hideLoader();
        showError('Error connecting to server');
        console.error('Error:', error);
    });
}

/**
 * Get chat recommendations
 */
function getChatRecommendations(message) {
    showLoader();
    
    fetch(API.CHAT, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message })
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();
        if (data.type === 'recommendations') {
            displayRecommendations(data.movies);
        } else {
            showError(data.message || 'Could not get recommendations');
        }
    })
    .catch(error => {
        hideLoader();
        showError('Error connecting to server');
        console.error('Error:', error);
    });
}

/**
 * Send voice input to server
 */
function sendVoiceInput(audioBlob) {
    showLoader();
    
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');
    
    fetch(API.VOICE, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();
        if (data.type === 'recommendations') {
            // Show transcription
            const transcriptionEl = document.getElementById('transcription');
            if (transcriptionEl) {
                transcriptionEl.textContent = `"${data.transcription}"`;
                transcriptionEl.style.display = 'block';
            }
            
            displayRecommendations(data.movies);
        } else {
            showError(data.message || 'Could not get recommendations');
        }
    })
    .catch(error => {
        hideLoader();
        showError('Error connecting to server');
        console.error('Error:', error);
    });
}

/**
 * Send voice input to MovieBuddy AI
 */
function sendVoiceToMovieBuddy(audioBlob, userId = 'default_user') {
    showLoader();
    
    const formData = new FormData();
    formData.append('audio_data', audioBlob, 'recording.wav');
    formData.append('user_id', userId);
    
    fetch(API.MOVIEBUDDY, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();
        
        if (data.success) {
            // Show transcription
            const transcriptionEl = document.getElementById('transcription');
            if (transcriptionEl) {
                transcriptionEl.textContent = `"${data.transcript}"`;
                transcriptionEl.style.display = 'block';
            }
            
            // Show MovieBuddy response
            const movieBuddyResponseEl = document.getElementById('moviebuddy-response');
            if (movieBuddyResponseEl) {
                movieBuddyResponseEl.textContent = data.response;
                movieBuddyResponseEl.style.display = 'block';
            }
            
            // Display recommendations if available
            if (data.recommendations && data.recommendations.length > 0) {
                displayRecommendations(data.recommendations);
            }
            
            // Handle conversation state
            if (data.waiting_for_follow_up) {
                // Show UI indicator that MovieBuddy is waiting for more input
                const followUpEl = document.getElementById('follow-up-indicator');
                if (followUpEl) {
                    followUpEl.style.display = 'block';
                }
            } else {
                // Hide follow-up indicator
                const followUpEl = document.getElementById('follow-up-indicator');
                if (followUpEl) {
                    followUpEl.style.display = 'none';
                }
            }
            
            // If there's a specific movie, display it
            if (data.movie) {
                displayMovieDetails(data.movie);
            }
        } else {
            showError(data.error || 'Could not process voice input');
        }
    })
    .catch(error => {
        hideLoader();
        showError('Error connecting to server');
        console.error('Error:', error);
    });
}

/**
 * Load movie details
 */
function loadMovieDetails(title) {
    showLoader();
    
    fetch(API.MOVIE_DETAILS, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title })
    })
    .then(response => response.json())
    .then(data => {
        if (data.type === 'movie_details') {
            displayMovieDetails(data.movie);
            loadSimilarMovies(title);
        } else {
            showError(data.message || 'Could not get movie details');
        }
    })
    .catch(error => {
        hideLoader();
        showError('Error connecting to server');
        console.error('Error:', error);
    });
}

/**
 * Load similar movies
 */
function loadSimilarMovies(title) {
    fetch(API.SIMILAR_MOVIES, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title })
    })
    .then(response => response.json())
    .then(data => {
        hideLoader();
        if (data.type === 'similar_movies') {
            displaySimilarMovies(data.movies);
        } else {
            console.error(data.message || 'Could not get similar movies');
        }
    })
    .catch(error => {
        hideLoader();
        console.error('Error:', error);
    });
}

/**
 * Load user history
 */
function loadUserHistory() {
    fetch(API.HISTORY)
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            displayHistory(data.history);
        } else {
            console.error('Could not load history');
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

/**
 * Display recommendations
 */
function displayRecommendations(movies) {
    const resultsContainer = document.getElementById('results');
    if (!resultsContainer) return;
    
    resultsContainer.innerHTML = '';
    
    if (!movies || movies.length === 0) {
        resultsContainer.innerHTML = '<p>No movies found matching your criteria.</p>';
        return;
    }
    
    const row = document.createElement('div');
    row.className = 'row';
    
    movies.forEach(movie => {
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-4';
        
        // Get image URL or use placeholder
        const imageUrl = movie.poster_path 
            ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
            : '/static/movies.webp';
        
        col.innerHTML = `
            <div class="card h-100">
                <img src="${imageUrl}" class="card-img-top" alt="${movie.title}">
                <div class="card-body">
                    <h5 class="card-title">${movie.title}</h5>
                    <p class="card-text">${movie.overview ? movie.overview.substring(0, 100) + '...' : 'No description available.'}</p>
                </div>
                <div class="card-footer">
                    <small class="text-muted">${movie.year || 'Unknown year'}</small>
                    <a href="#" class="btn btn-sm btn-primary float-end view-details" data-title="${movie.title}">View Details</a>
                </div>
            </div>
        `;
        
        row.appendChild(col);
    });
    
    resultsContainer.appendChild(row);
    
    // Add event listeners to view details buttons
    document.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            loadMovieDetails(button.dataset.title);
        });
    });
    
    // Scroll to results
    resultsContainer.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Display movie details
 */
function displayMovieDetails(movie) {
    // This would redirect to a movie details page in a real implementation
    // For now, we'll just show an alert
    alert(`Movie Details: ${movie.title} (${movie.year})\n\n${movie.overview || 'No description available.'}`);
}

/**
 * Display similar movies
 */
function displaySimilarMovies(movies) {
    const similarMoviesContainer = document.getElementById('similar-movies');
    if (!similarMoviesContainer) return;
    
    similarMoviesContainer.innerHTML = '';
    
    if (!movies || movies.length === 0) {
        similarMoviesContainer.innerHTML = '<p>No similar movies found.</p>';
        return;
    }
    
    const row = document.createElement('div');
    row.className = 'row';
    
    movies.slice(0, 4).forEach(movie => {
        const col = document.createElement('div');
        col.className = 'col-md-3 mb-3';
        
        // Get image URL or use placeholder
        const imageUrl = movie.poster_path 
            ? `https://image.tmdb.org/t/p/w500${movie.poster_path}`
            : '/static/movies.webp';
        
        col.innerHTML = `
            <div class="card h-100">
                <img src="${imageUrl}" class="card-img-top" alt="${movie.title}">
                <div class="card-body">
                    <h5 class="card-title">${movie.title}</h5>
                </div>
                <div class="card-footer">
                    <a href="#" class="btn btn-sm btn-primary view-details" data-title="${movie.title}">View Details</a>
                </div>
            </div>
        `;
        
        row.appendChild(col);
    });
    
    similarMoviesContainer.appendChild(row);
    
    // Add event listeners to view details buttons
    similarMoviesContainer.querySelectorAll('.view-details').forEach(button => {
        button.addEventListener('click', (event) => {
            event.preventDefault();
            loadMovieDetails(button.dataset.title);
        });
    });
}

/**
 * Display history
 */
function displayHistory(history) {
    const historyContainer = document.getElementById('history-container');
    if (!historyContainer) return;
    
    historyContainer.innerHTML = '';
    
    if (!history || history.length === 0) {
        historyContainer.innerHTML = '<p>No recommendation history found.</p>';
        return;
    }
    
    const list = document.createElement('ul');
    list.className = 'list-group';
    
    history.forEach(item => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item';
        
        const timestamp = new Date(item.timestamp).toLocaleString();
        const mood = item.mood || 'Unknown mood';
        
        let recommendationsHtml = '';
        if (item.recommendations && item.recommendations.length > 0) {
            recommendationsHtml = '<ul>';
            item.recommendations.forEach(movie => {
                recommendationsHtml += `<li>${movie.title}</li>`;
            });
            recommendationsHtml += '</ul>';
        } else {
            recommendationsHtml = '<p>No recommendations</p>';
        }
        
        listItem.innerHTML = `
            <div class="d-flex w-100 justify-content-between">
                <h5 class="mb-1">Mood: ${mood}</h5>
                <small>${timestamp}</small>
            </div>
            <p class="mb-1">Recommendations:</p>
            ${recommendationsHtml}
        `;
        
        list.appendChild(listItem);
    });
    
    historyContainer.appendChild(list);
}

/**
 * Show loader
 */
function showLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'block';
    }
}

/**
 * Hide loader
 */
function hideLoader() {
    const loader = document.getElementById('loader');
    if (loader) {
        loader.style.display = 'none';
    }
}

/**
 * Show error
 */
function showError(message) {
    const errorContainer = document.getElementById('error-container');
    if (!errorContainer) return;
    
    errorContainer.innerHTML = `<div class="alert alert-danger" role="alert">${message}</div>`;
    errorContainer.style.display = 'block';
    
    // Hide after 5 seconds
    setTimeout(() => {
        errorContainer.style.display = 'none';
    }, 5000);
}
