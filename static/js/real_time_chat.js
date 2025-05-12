 /**
 * Enhanced real-time chat interface for MovieBuddyAI using AJAX
 */

// Initialize variables
let sessionId = null;
let recorder = null;
let isRecording = false;
let audioChunks = [];
let isTyping = false;
let currentMovieCards = [];
let pollInterval = null;
let lastResponseTimestamp = 0;

// DOM elements for caching
let chatMessages;
let messageInput;
let sendButton;
let recordButton;
let movieRecommendations;
let typingIndicator;

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    // Cache DOM elements
    chatMessages = document.getElementById('chat-messages');
    messageInput = document.getElementById('message-input');
    sendButton = document.getElementById('send-button');
    recordButton = document.getElementById('record-button');
    movieRecommendations = document.getElementById('movie-recommendations');
    typingIndicator = document.getElementById('typing-indicator');
    
    // Initialize chat UI
    initializeChatUI();
    
    // Initialize real-time chat connection
    initializeConnection();

    // Add event listeners for user interactions
    messageInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendTextMessage();
        }
    });

    // Add event listeners for buttons
    sendButton.addEventListener('click', sendTextMessage);
    recordButton.addEventListener('click', toggleRecording);
    
    // Add listener for clear chat button
    const clearChatButton = document.getElementById('clear-chat');
    if (clearChatButton) {
        clearChatButton.addEventListener('click', () => {
            chatMessages.innerHTML = '';
            addSystemMessage("Chat history cleared. What would you like to talk about?");
            // Also clear on server
            fetch(`/api/clear_chat?session_id=${sessionId}`, {
                method: 'POST'
            });
        });
    }
});

/**
 * Initialize the chat UI and session
 */
function initializeChatUI() {
    // Set up initial session ID or retrieve from storage
    sessionId = localStorage.getItem('moodflix_session_id') || generateSessionId();
    localStorage.setItem('moodflix_session_id', sessionId);
    
    // Display welcome message
    addSystemMessage("👋 Welcome to MovieBuddyAI! I can help you find the perfect movie for your mood. Try asking for a recommendation or tell me what kind of movie you're looking for.");
    
    // Set up microphone if available
    setupMicrophone();
}

/**
 * Initialize the real-time chat connection
 */
function initializeConnection() {
    // Display connected status
    showConnectionStatus(true);
    console.log('Chat interface initialized');
    
    // Start polling for messages
    startPolling();
    
    // Send a ping to establish session
    fetch('/api/check_response?session_id=' + sessionId)
        .then(response => response.json())
        .then(data => {
            console.log('Session established:', sessionId);
        })
        .catch(error => {
            console.error('Error establishing session:', error);
            showConnectionStatus(false);
        });
}

/**
 * Start polling for new messages
 */
function startPolling() {
    // Clear any existing interval
    if (pollInterval) {
        clearInterval(pollInterval);
    }
    
    // Poll for new messages every 2 seconds
    pollInterval = setInterval(() => {
        checkForNewResponses();
    }, 2000);
}

/**
 * Check for new responses from the server
 */
function checkForNewResponses() {
    if (!sessionId) return;
    
    fetch(`/api/check_response_v2?session_id=${sessionId}&timestamp=${lastResponseTimestamp}`)
        .then(response => response.json())
        .then(data => {
            if (data && data.status === 'success') {
                // Update last timestamp
                if (data.timestamp) {
                    lastResponseTimestamp = data.timestamp;
                }
                
                // Process new messages
                handleChatResponse(data);
                
                // ENHANCEMENT: Also check for recommendations in the response
                if (data.recommendations && Array.isArray(data.recommendations) && data.recommendations.length > 0) {
                    console.log('Found recommendations in response:', data.recommendations.length);
                    displayMovieRecommendations(data.recommendations);
                }
            }
        })
        .catch(error => {
            console.error('Error checking for new responses:', error);
            showConnectionStatus(false);
        });
}

/**
 * Handle chat responses from the server
 */
function handleChatResponse(data) {
    // Handle text response
    if (data.content) {
        if (data.is_final) {
            // This is the final chunk, add it and any recommendations
            addAIMessage(data.content);
            
            // Display movie recommendations if available
            if (data.recommendations && data.recommendations.length > 0) {
                displayMovieRecommendations(data.recommendations);
            }
            
            // Display transcript if available
            if (data.transcript) {
                // If transcript differs significantly from what was shown in user message
                // we might want to show the actual transcript
                const lastUserMessage = document.querySelector('.message.user:last-child .message-content');
                if (lastUserMessage && shouldUpdateTranscript(lastUserMessage.textContent, data.transcript)) {
                    lastUserMessage.textContent = data.transcript;
                    lastUserMessage.setAttribute('title', 'Transcribed from voice input');
                }
            }
        } else {
            // This is a streaming chunk, update the current message or create new one
            updateOrCreateAIMessage(data.content);
        }
    }
    
    // Hide typing indicator when done
    if (data.is_final) {
        isTyping = false;
        updateTypingIndicator();
    }
}

/**
 * Send a text message to the server
 */
function sendTextMessage() {
    const message = messageInput.value.trim();
    
    if (!message || !sessionId) return;
    
    // Add user message to the chat
    addUserMessage(message);
    
    // Clear input and show typing indicator
    messageInput.value = '';
    isTyping = true;
    updateTypingIndicator();
    
    // Send to server
    fetch('/api/real_time_text_v2', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            session_id: sessionId,
            message: message
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Process any immediate recommendations
            if (data.recommendations && Array.isArray(data.recommendations) && data.recommendations.length > 0) {
                console.log('Direct recommendations received:', data.recommendations.length);
                displayMovieRecommendations(data.recommendations);
            }
            
            // Check immediately for response
            checkForNewResponses();
            
            // Start polling more aggressively for responses
            if (!pollInterval) {
                startPolling();
            }
            
            // Set up a direct recommendation check after a short delay
            setTimeout(function() {
                fetch(`/api/check_response_v2?session_id=${sessionId}&timestamp=0`)
                    .then(response => response.json())
                    .then(data => {
                        if (data && data.recommendations && 
                            Array.isArray(data.recommendations) && 
                            data.recommendations.length > 0) {
                            console.log('Delayed recommendations found:', data.recommendations.length);
                            displayMovieRecommendations(data.recommendations);
                        }
                    })
                    .catch(err => console.error('Error in delayed check:', err));
            }, 1500); // Check after 1.5 seconds
        } else {
            addSystemMessage('Failed to send message. Please try again.', 'error');
            isTyping = false;
            updateTypingIndicator();
        }
    })
    .catch(error => {
        console.error('Error sending message:', error);
        addSystemMessage('Error sending message. Please check your connection.', 'error');
        isTyping = false;
        updateTypingIndicator();
    });
}

/**
 * Add a user message to the chat UI
 */
function addUserMessage(message) {
    const messageElement = document.createElement('div');
    messageElement.className = 'message user';
    messageElement.innerHTML = `
        <div class="avatar">👤</div>
        <div class="message-content">${message}</div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

/**
 * Add an AI message to the chat UI
 */
function addAIMessage(message) {
    // Check if there's a partial AI message to update
    const partialMsg = document.querySelector('.message.ai.partial');
    
    if (partialMsg) {
        // Update existing partial message
        partialMsg.querySelector('.message-content').innerHTML = formatMessage(message);
        partialMsg.classList.remove('partial');
    } else {
        // Create new message
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai';
        messageElement.innerHTML = `
            <div class="avatar">🎬</div>
            <div class="message-content">${formatMessage(message)}</div>
        `;
        chatMessages.appendChild(messageElement);
    }
    
    scrollToBottom();
}

/**
 * Update an existing AI message or create a new partial one
 */
function updateOrCreateAIMessage(message) {
    const partialMsg = document.querySelector('.message.ai.partial');
    
    if (partialMsg) {
        // Update existing partial message
        partialMsg.querySelector('.message-content').innerHTML = formatMessage(message);
    } else {
        // Create new partial message
        const messageElement = document.createElement('div');
        messageElement.className = 'message ai partial';
        messageElement.innerHTML = `
            <div class="avatar">🎬</div>
            <div class="message-content">${formatMessage(message)}</div>
        `;
        chatMessages.appendChild(messageElement);
    }
    
    scrollToBottom();
}

/**
 * Add a system message to the chat UI
 */
function addSystemMessage(message, type = 'info') {
    const messageElement = document.createElement('div');
    messageElement.className = `message system ${type}`;
    messageElement.innerHTML = `
        <div class="message-content">${message}</div>
    `;
    chatMessages.appendChild(messageElement);
    scrollToBottom();
}

/**
 * Display movie recommendations in the UI
 */
function displayMovieRecommendations(movies) {
    console.log('Displaying movie recommendations:', JSON.stringify(movies, null, 2));
    movieRecommendations.innerHTML = '';
    currentMovieCards = [];

    if (!movies || movies.length === 0) {
        movieRecommendations.style.display = 'none';
        return;
    }
    
    // Debug alert to inform user about movies received
    console.log(`Received ${movies.length} movie recommendations`);
    
    // Create cards for each movie
    movies.forEach(movie => {
        const movieCard = createMovieCard(movie);
        movieRecommendations.appendChild(movieCard);
        currentMovieCards.push(movieCard);
    });
    
    // Show recommendations container
    movieRecommendations.style.display = 'flex';
    
    // Add animation to cards
    animateMovieCards();
}

/**
 * Create a movie recommendation card
 */
function createMovieCard(movie) {
    console.log('Creating card for movie:', movie);
    const card = document.createElement('div');
    card.className = 'movie-card';
    
    // Extract movie data safely
    const title = movie.title || 'Unknown Title';
    const year = movie.year || 'Unknown Year';
    const plot = movie.plot || 'No plot information available';
    
    // Generate genres text - handle both string and array formats
    let genresText = 'Unknown Genre';
    if (movie.genres) {
        if (Array.isArray(movie.genres)) {
            genresText = movie.genres.join(', ');
        } else if (typeof movie.genres === 'string') {
            genresText = movie.genres;
        }
    }
    
    // Construct TMDB image URL if we have a poster_path, or use tmdb_id to get one
    let imageUrl = '/static/img/movie_placeholder.jpg';
    
    if (movie.poster_path) {
        imageUrl = `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
    } else if (movie.tmdb_id) {
        // If we have a TMDB ID but no poster path, construct the URL
        imageUrl = `https://image.tmdb.org/t/p/w500/movie-poster-${movie.tmdb_id}.jpg`;
    } else if (movie.id && !isNaN(movie.id)) {
        // Try using the ID directly if it looks like a number
        imageUrl = `https://image.tmdb.org/t/p/w500/movie-poster-${movie.id}.jpg`;
    }
    
    // Generate a unique ID if not present
    const movieId = movie.id || movie.index || Math.random().toString(36).substr(2, 9);
    
    // Make entire card clickable but prevent default navigation
    card.onclick = function(e) {
        e.preventDefault();
        e.stopPropagation();
        showMovieDetails(movie);
        return false;
    };
    
    card.innerHTML = `
        <div class="movie-poster">
            <img src="${imageUrl}" alt="${title}" onerror="this.src='/static/img/movie_placeholder.jpg'">
        </div>
        <div class="movie-info">
            <h3 class="movie-title">${title}</h3>
            <p class="movie-year">${year}</p>
            <p class="movie-genres">${genresText}</p>
            <p class="movie-plot">${plot.length > 100 ? plot.substring(0, 100) + '...' : plot}</p>
        </div>
        <div class="movie-actions">
            <button class="action-button details-button">Details</button>
        </div>
    `;
    
    // Add event listeners to buttons
    card.querySelector('.details-button').addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showMovieDetails(movie);
        return false;
    });
    
    return card;
}

/**
 * Animate movie cards with staggered entrance
 */
function animateMovieCards() {
    currentMovieCards.forEach((card, index) => {
        // Add initial hidden class
        card.classList.add('hidden');
        
        // Trigger animation with delay based on index
        setTimeout(() => {
            card.classList.remove('hidden');
            card.classList.add('visible');
        }, 100 * index);
    });
}

/**
 * Set up microphone access for voice recording
 */
function setupMicrophone() {
    // Check if browser supports audio recording
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.log('Browser does not support audio recording');
        recordButton.disabled = true;
        recordButton.title = 'Audio recording not supported in this browser';
        return;
    }
    
    // Set up audio context
    try {
        window.AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioContext = new AudioContext();
    } catch (e) {
        console.error('Web Audio API not supported:', e);
    }
}

/**
 * Toggle voice recording on/off
 */
function toggleRecording() {
    if (isRecording) {
        // Stop recording
        stopRecording();
    } else {
        // Start recording
        startRecording();
    }
}

/**
 * Start voice recording
 */
function startRecording() {
    if (isRecording) return;
    
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            isRecording = true;
            recordButton.classList.add('recording');
            recordButton.innerHTML = '<i class="fas fa-stop"></i>';
            audioChunks = [];
            
            // Create MediaRecorder
            recorder = new MediaRecorder(stream);
            
            // Collect audio chunks
            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunks.push(e.data);
                }
            };
            
            // Handle recording stop
            recorder.onstop = processAudioRecording;
            
            // Start recording (stop after 15 seconds max)
            recorder.start();
            setTimeout(() => {
                if (isRecording) {
                    stopRecording();
                }
            }, 15000);
            
            // Add visual feedback
            addSystemMessage("🎙️ Recording... (tap again to stop)", "recording");
        })
        .catch(err => {
            console.error('Error accessing microphone:', err);
            addSystemMessage("⚠️ Could not access your microphone", "error");
        });
}

/**
 * Stop voice recording
 */
function stopRecording() {
    if (!isRecording || !recorder) return;
    
    isRecording = false;
    recordButton.classList.remove('recording');
    recordButton.innerHTML = '<i class="fas fa-microphone"></i>';
    
    // Stop recorder
    recorder.stop();
    
    // Add visual feedback
    const recordingMsg = document.querySelector('.message.system.recording');
    if (recordingMsg) {
        recordingMsg.remove();
    }
    addSystemMessage("Processing your voice input...");
}

/**
 * Process the recorded audio and send to server
 */
function processAudioRecording() {
    // Create blob from audio chunks
    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    
    // Create form data to send to server
    const formData = new FormData();
    formData.append('audio_data', audioBlob, 'recording.webm');
    formData.append('session_id', sessionId);
    
    // Send recording to processing endpoint
    fetch('/api/real_time_voice', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show transcription as user message
            if (data.transcript) {
                addUserMessage(data.transcript);
            } else {
                addSystemMessage("I couldn't understand what you said. Please try again.");
            }
            
            // The response will come through the WebSocket
        } else {
            console.error('Error processing voice:', data.error);
            addSystemMessage(`⚠️ ${data.error || 'Error processing your voice input'}`, "error");
        }
    })
    .catch(err => {
        console.error('Error sending voice recording:', err);
        addSystemMessage("⚠️ Error sending your voice recording", "error");
    });
}

/**
 * Update the typing indicator based on server state
 */
function updateTypingIndicator() {
    if (isTyping) {
        typingIndicator.style.display = 'block';
    } else {
        typingIndicator.style.display = 'none';
    }
}

/**
 * Show connection status
 */
function showConnectionStatus(connected) {
    const statusElement = document.getElementById('connection-status');
    if (connected) {
        statusElement.textContent = 'Connected';
        statusElement.className = 'connected';
    } else {
        statusElement.textContent = 'Disconnected';
        statusElement.className = 'disconnected';
    }
}

/**
 * Format message text with markdown-like syntax
 */
function formatMessage(message) {
    let formatted = message;
    
    // Convert movie titles to bold
    formatted = formatted.replace(/"([^"]+)"/g, '<strong>"$1"</strong>');
    
    // Convert newlines to <br>
    formatted = formatted.replace(/\n/g, '<br>');
    
    return formatted;
}

/**
 * Determine if we should update the transcript
 */
function shouldUpdateTranscript(shown, actual) {
    // If they're very different in length or content
    if (Math.abs(shown.length - actual.length) > 10) {
        return true;
    }
    
    return false;
}

/**
 * Generate a random session ID
 */
function generateSessionId() {
    return 'moodflix_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

/**
 * Scroll chat to the bottom
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Add a movie to the user's watchlist
 */
function addToWatchlist(movieId) {
    fetch('/add_to_watchlist', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ movie_id: movieId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addSystemMessage(`✅ Added to your watchlist!`);
        } else {
            addSystemMessage(`⚠️ ${data.error || 'Error adding to watchlist'}`, "error");
        }
    })
    .catch(err => {
        console.error('Error adding to watchlist:', err);
        addSystemMessage(`⚠️ Error adding to watchlist`, "error");
    });
}

/**
 * Show detailed information about a movie
 */
function showMovieDetails(movie) {
    console.log('Showing details for movie:', movie);
    
    // Create modal element
    const modal = document.createElement('div');
    modal.className = 'movie-modal';
    
    // Extract movie data safely
    const title = movie.title || 'Unknown Title';
    const year = movie.year || 'Unknown Year';
    const plot = movie.plot || 'No plot information available';
    
    // Generate an ID if not present
    const movieId = movie.id || movie.index || Math.random().toString(36).substr(2, 9);
    
    // Construct TMDB image URL using the same approach as createMovieCard
    let imageUrl = '/static/img/movie_placeholder.jpg';
    
    if (movie.poster_path) {
        imageUrl = `https://image.tmdb.org/t/p/w500${movie.poster_path}`;
    } else if (movie.tmdb_id) {
        // If we have a TMDB ID but no poster path, construct the URL
        imageUrl = `https://image.tmdb.org/t/p/w500/movie-poster-${movie.tmdb_id}.jpg`;
    } else if (movie.id && !isNaN(movie.id)) {
        // Try using the ID directly if it looks like a number
        imageUrl = `https://image.tmdb.org/t/p/w500/movie-poster-${movie.id}.jpg`;
    }
    
    // Process genres
    let genresText = 'Unknown';
    if (movie.genres) {
        if (Array.isArray(movie.genres)) {
            genresText = movie.genres.join(', ');
        } else if (typeof movie.genres === 'string') {
            genresText = movie.genres;
        }
    }
    
    // Format cast and crew if available
    let castText = '';
    if (movie.actors) {
        if (Array.isArray(movie.actors) && movie.actors.length > 0) {
            castText = `<p><strong>Cast:</strong> ${movie.actors.join(', ')}</p>`;
        } else if (typeof movie.actors === 'string') {
            castText = `<p><strong>Cast:</strong> ${movie.actors}</p>`;
        }
    }
    
    let directorsText = '';
    if (movie.directors) {
        if (Array.isArray(movie.directors) && movie.directors.length > 0) {
            directorsText = `<p><strong>Director:</strong> ${movie.directors.join(', ')}</p>`;
        } else if (typeof movie.directors === 'string') {
            directorsText = `<p><strong>Director:</strong> ${movie.directors}</p>`;
        }
    }
    
    // Fill modal content
    modal.innerHTML = `
        <div class="modal-content">
            <span class="close-button">&times;</span>
            <div class="movie-detail-content">
                <div class="movie-poster">
                    <img src="${imageUrl}" alt="${title}" onerror="this.src='/static/img/movie_placeholder.jpg'">
                </div>
                <div class="movie-info">
                    <h2>${title} (${year})</h2>
                    <p><strong>Genres:</strong> ${genresText}</p>
                    ${castText}
                    ${directorsText}
                    <div class="plot">
                        <p><strong>Plot:</strong> ${plot}</p>
                    </div>
                    <div class="movie-actions">
                        <button class="action-button ask-more">Ask for more information</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Add event listeners
    modal.querySelector('.close-button').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    // Add a button to ask for more information
    modal.querySelector('.ask-more').addEventListener('click', () => {
        if (messageInput) {
            messageInput.value = `Tell me more about "${title}"`;
            document.body.removeChild(modal);
            // Trigger send
            if (sendButton) sendButton.click();
        }
    });
    
    // Add click outside to close
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            document.body.removeChild(modal);
        }
    });
    
    // Add to body
    document.body.appendChild(modal);
}

/**
 * Mark a movie as watched
 */
function markAsWatched(movieId) {
    fetch('/mark_as_watched', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ movie_id: movieId })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            addSystemMessage(`✅ Marked as watched!`);
        } else {
            addSystemMessage(`⚠️ ${data.error || 'Error marking as watched'}`, "error");
        }
    })
    .catch(err => {
        console.error('Error marking as watched:', err);
        addSystemMessage(`⚠️ Error marking as watched`, "error");
    });
}
