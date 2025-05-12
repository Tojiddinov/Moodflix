/**
 * MoodFlix Real-Time Voice Chat Component
 * Provides voice and text chat functionality for movie recommendations
 */

class MovieBuddyChat {
    constructor(options = {}) {
        // Configuration
        this.containerId = options.containerId || 'movie-buddy-chat';
        this.position = options.position || 'bottom-right';
        this.theme = options.theme || 'dark';
        this.initialMessage = options.initialMessage || "Hi there! I'm MovieBuddy AI. How can I help you find the perfect movie today?";
        this.autoOpen = options.autoOpen || false;
        this.apiBasePath = options.apiBasePath || '';
        
        // Make the instance globally accessible
        window.movieBuddyChat = this;
        
        // Real-time chat settings
        this.sessionId = this._generateSessionId();
        this.conversationActive = false;
        this.pollInterval = options.pollInterval || 1000; // ms
        this.pollTimer = null;
        this.lastMessageTimestamp = 0;
        
        // UI State
        this.isOpen = false;
        this.isRecording = false;
        this.isTyping = false;
        this.isWaitingForResponse = false;
        
        // Audio handling
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.audioContext = null;
        this.analyser = null;
        this.audioStream = null;
        
        // Voice detection
        this.silenceDetectionThreshold = options.silenceThreshold || 15;
        this.silenceTimer = null;
        this.maxSilenceDuration = options.maxSilenceDuration || 1500; // ms
        this.recordingTimeout = null;
        this.maxRecordingTime = options.maxRecordingTime || 15000; // ms
        
        // Create and initialize the chat interface
        this.createChatInterface();
        this.setupEventListeners();
        
        // Auto-open if configured
        if (this.autoOpen) {
            setTimeout(() => this.toggleChat(), 1000);
        }
    }
    
    createChatInterface() {
        // Create the main container
        this.container = document.createElement('div');
        this.container.id = this.containerId;
        this.container.className = `movie-buddy-chat ${this.position} ${this.theme}`;
        
        // Create the chat button
        this.chatButton = document.createElement('button');
        this.chatButton.className = 'chat-toggle-btn';
        this.chatButton.innerHTML = '<i class="fas fa-comment"></i>';
        this.chatButton.setAttribute('aria-label', 'Toggle chat');
        this.chatButton.setAttribute('title', 'Chat with MovieBuddy AI');
        
        // Create the chat panel
        this.chatPanel = document.createElement('div');
        this.chatPanel.className = 'chat-panel';
        
        // Create the chat header
        const chatHeader = document.createElement('div');
        chatHeader.className = 'chat-header';
        
        const chatTitle = document.createElement('div');
        chatTitle.className = 'chat-title';
        chatTitle.innerHTML = '<i class="fas fa-film"></i> MovieBuddy AI';
        
        this.closeButton = document.createElement('button');
        this.closeButton.className = 'close-button';
        this.closeButton.innerHTML = '<i class="fas fa-times"></i>';
        this.closeButton.setAttribute('aria-label', 'Close chat');
        
        chatHeader.appendChild(chatTitle);
        chatHeader.appendChild(this.closeButton);
        
        // Create the chat messages container
        this.chatMessages = document.createElement('div');
        this.chatMessages.className = 'chat-messages';
        
        // Create the chat input area
        const chatInput = document.createElement('div');
        chatInput.className = 'chat-input';
        chatInput.innerHTML = `
            <input type="text" placeholder="Type your message here..." aria-label="Message input">
            <div class="chat-controls">
                <button class="voice-btn" aria-label="Record voice message">
                    <i class="fas fa-microphone"></i>
                </button>
                <button class="send-btn" aria-label="Send message" disabled>
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        `;
        
        // Assemble the chat panel
        this.chatPanel.appendChild(chatHeader);
        this.chatPanel.appendChild(this.chatMessages);
        this.chatPanel.appendChild(chatInput);
        
        // Add everything to the container
        this.container.appendChild(this.chatButton);
        this.container.appendChild(this.chatPanel);
        
        // Add the container to the document
        document.body.appendChild(this.container);
        
        // Store references to elements
        this.inputField = this.chatPanel.querySelector('input');
        this.sendButton = this.chatPanel.querySelector('.send-btn');
        this.voiceButton = this.chatPanel.querySelector('.voice-btn');
        
        // Add initial message
        this.appendMessage(this.initialMessage, 'system');
        
        // Add attention animation to the chat button after a delay
        setTimeout(() => {
            this.container.classList.add('attention');
            // Remove attention after a while
            setTimeout(() => {
                this.container.classList.remove('attention');
            }, 6000);
        }, 10000);
    }
    
    setupEventListeners() {
        // Toggle chat open/closed
        this.chatButton.addEventListener('click', () => this.toggleChat());
        this.closeButton.addEventListener('click', () => this.toggleChat(false));
        
        // Send message on button click
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Send message on Enter key
        this.inputField.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                this.sendMessage();
            }
        });
        
        // Enable/disable send button based on input
        this.inputField.addEventListener('input', () => {
            this.sendButton.disabled = this.inputField.value.trim() === '';
        });
        
        // Voice recording
        this.voiceButton.addEventListener('click', () => this.toggleRecording());
        
        // Add voice chat button to the navigation menu if it exists
        this.addNavMenuItem();
    }
    
    toggleChat(open = null) {
        // Toggle or set chat state
        this.isOpen = open !== null ? open : !this.isOpen;
        
        // Update UI based on state
        if (this.isOpen) {
            this.chatPanel.classList.add('open');
            this.container.classList.remove('attention'); // Remove attention animation
            
            // Start or resume conversation with server
            if (!this.conversationActive) {
                this.startConversation();
            }
        } else {
            this.chatPanel.classList.remove('open');
        }
    }
    
    startConversation() {
        // Initialize or resume conversation with server
        this.showTypingIndicator();
        
        fetch('/api/real_time_chat', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            this.hideTypingIndicator();
            this.conversationActive = true;
            
            // Display welcome message if this is first open
            if (this.chatMessages.children.length === 0) {
                this.appendMessage(this.initialMessage, 'system');
            }
        })
        .catch(error => {
            console.error('Error starting conversation:', error);
            this.hideTypingIndicator();
            this.appendMessage('Sorry, there was an error connecting to the chat service. Please try again later.', 'system', true);
        });
    }
    
    sendMessage() {
        const message = this.inputField.value.trim();
        if (!message) return;
        
        // Add user message to chat
        this.appendMessage(message, 'user');
        
        // Clear input field
        this.inputField.value = '';
        
        // Send to API and show typing indicator
        this.processMessage(message, 'text');
    }
    
    processMessage(message, type) {
        // Show typing indicator
        this.showTypingIndicator();
        
        // Send message to server using AJAX
        fetch('/api/real_time_text', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                text: message,
                session_id: this.sessionId
            }),
        })
        .then(response => response.json())
        .then(data => {
            // Process response
            this.hideTypingIndicator();
            this.handleResponse(data);
        })
        .catch(error => {
            console.error('Error:', error);
            this.hideTypingIndicator();
            this.appendMessage("Sorry, there was an error processing your request. Please try again.", 'system', true);
        });
    }
    
    handleResponse(data) {
        // Hide typing indicator
        this.hideTypingIndicator();
        this.isWaitingForResponse = false;
        
        if (!data.success) {
            this.appendMessage(`Error: ${data.error || 'Unknown error'}`, 'system', true);
            return;
        }
        
        // Update session ID if provided
        if (data.session_id) {
            this.sessionId = data.session_id;
        }
        
        // Add response to chat
        let responseMessage = data.response || 'Sorry, I could not find a response.';
        
        // Format movie recommendations if any
        if (data.recommendations && data.recommendations.length > 0) {
            responseMessage += '<div class="movie-recommendations">';
            data.recommendations.forEach(movie => {
                responseMessage += this.formatMovieRecommendation(movie);
            });
            responseMessage += '</div>';
        }
        
        this.appendMessage(responseMessage, 'system');
        
        // Start polling for more responses if not already polling
        if (!this.pollTimer && data.recommendations) {
            this.startPolling();
        }
    }
    
    toggleRecording() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            this.startRecording();
        }
    }
    
    startRecording() {
        // Request microphone access
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(stream => {
                this.isRecording = true;
                this.voiceButton.classList.add('recording');
                this.audioStream = stream;
                
                // Add visual recording feedback
                const recordingWave = document.createElement('div');
                recordingWave.className = 'recording-wave';
                this.voiceButton.appendChild(recordingWave);
                
                // Initialize audio context for volume detection
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const source = this.audioContext.createMediaStreamSource(stream);
                this.analyser = this.audioContext.createAnalyser();
                this.analyser.fftSize = 256;
                source.connect(this.analyser);
                
                // Initialize media recorder with better audio quality
                this.mediaRecorder = new MediaRecorder(stream, {
                    mimeType: 'audio/webm;codecs=opus',
                    audioBitsPerSecond: 128000
                });
                this.audioChunks = [];
                
                // Start silence detection
                this.detectSilence();
                
                // Handle data available event
                this.mediaRecorder.addEventListener('dataavailable', event => {
                    this.audioChunks.push(event.data);
                });
                
                // Handle recording stop event
                this.mediaRecorder.addEventListener('stop', () => {
                    // Remove visual recording feedback
                    const wave = this.voiceButton.querySelector('.recording-wave');
                    if (wave) wave.remove();
                    
                    // Create audio blob
                    const audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
                    
                    // Only process if the blob has meaningful content
                    if (audioBlob.size > 1000) { // Arbitrary threshold
                        // Add a user message indicating voice was recorded
                        this.appendMessage('Voice message sent', 'user');
                        
                        // Process the audio
                        this.processMessage(audioBlob, 'audio');
                    } else {
                        // Too short/empty recording
                        this.appendMessage('Recording was too short. Please try again.', 'system', true);
                    }
                    
                    // Clean up
                    this.isRecording = false;
                    this.voiceButton.classList.remove('recording');
                    this.audioChunks = [];
                    
                    // Stop all tracks in the stream
                    if (this.audioStream) {
                        this.audioStream.getTracks().forEach(track => track.stop());
                        this.audioStream = null;
                    }
                    
                    // Clear timers
                    if (this.silenceTimer) {
                        clearTimeout(this.silenceTimer);
                        this.silenceTimer = null;
                    }
                    if (this.recordingTimeout) {
                        clearTimeout(this.recordingTimeout);
                        this.recordingTimeout = null;
                    }
                });
                
                // Start recording
                this.mediaRecorder.start();
                
                // Set max recording time
                this.recordingTimeout = setTimeout(() => {
                    if (this.isRecording) {
                        this.stopRecording();
                    }
                }, this.maxRecordingTime);
            })
            .catch(error => {
                console.error('Error accessing microphone:', error);
                this.appendMessage('Error accessing microphone. Please check permissions.', 'system', true);
            });
    }
    
    detectSilence() {
        if (!this.isRecording || !this.analyser) return;
        
        // Get volume data
        const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        this.analyser.getByteFrequencyData(dataArray);
        
        // Calculate average volume
        const average = dataArray.reduce((sum, value) => sum + value, 0) / dataArray.length;
        
        // Check if volume is below threshold (silence)
        if (average < this.silenceDetectionThreshold) {
            // Start or continue silence timer
            if (!this.silenceTimer) {
                this.silenceTimer = setTimeout(() => {
                    // Stop recording after silence duration
                    this.stopRecording();
                    this.silenceTimer = null;
                }, this.maxSilenceDuration);
            }
        } else {
            // Reset silence timer if sound detected
            if (this.silenceTimer) {
                clearTimeout(this.silenceTimer);
                this.silenceTimer = null;
            }
        }
        
        // Continue checking while recording
        if (this.isRecording) {
            requestAnimationFrame(() => this.detectSilence());
        }
    }
    
    stopRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.stop();
            this.isRecording = false;
            this.voiceButton.classList.remove('recording');
        }
        messageElement.textContent = message;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = this.getCurrentTime();
        
        messageElement.appendChild(timeElement);
        this.chatMessages.appendChild(messageElement);
        
        this.scrollToBottom();
    }
    
    addBotMessage(message) {
        const messageElement = document.createElement('div');
        messageElement.className = 'message bot-message';
        messageElement.textContent = message;
        
        const timeElement = document.createElement('div');
        timeElement.className = 'message-time';
        timeElement.textContent = this.getCurrentTime();
        
        messageElement.appendChild(timeElement);
        this.chatMessages.appendChild(messageElement);
        
        this.scrollToBottom();
    }
    
    addMovieRecommendations(movies) {
        const container = document.createElement('div');
        container.className = 'bot-message movie-recommendations-container';
        
        const heading = document.createElement('div');
        heading.textContent = 'Here are some recommendations for you:';
        heading.style.marginBottom = '0.5rem';
        container.appendChild(heading);
        
        const recommendationsGrid = document.createElement('div');
        recommendationsGrid.className = 'movie-recommendations';
        
        movies.forEach(movie => {
            const movieCard = document.createElement('div');
            movieCard.className = 'movie-card';
            
            const movieInfo = document.createElement('div');
            movieInfo.className = 'movie-info';
            
            const titleElement = document.createElement('div');
            titleElement.className = 'movie-title';
            titleElement.textContent = movie.title;
            
            const yearElement = document.createElement('div');
            yearElement.className = 'movie-year';
            yearElement.textContent = movie.year || 'N/A';
            
            const genresElement = document.createElement('div');
            genresElement.className = 'movie-genres';
            
            if (movie.genres && movie.genres.length > 0) {
                movie.genres.slice(0, 3).forEach(genre => {
                    const genreTag = document.createElement('span');
                    genreTag.className = 'genre-tag';
                    genreTag.textContent = genre;
                    genresElement.appendChild(genreTag);
                });
            }
            
            const plotElement = document.createElement('div');
            plotElement.className = 'movie-plot';
            plotElement.textContent = movie.plot || 'No plot available';
            
            movieInfo.appendChild(titleElement);
            movieInfo.appendChild(yearElement);
            movieInfo.appendChild(genresElement);
            movieInfo.appendChild(plotElement);
            
            movieCard.appendChild(movieInfo);
            recommendationsGrid.appendChild(movieCard);
        });
        
        container.appendChild(recommendationsGrid);
        this.chatMessages.appendChild(container);
        
        this.scrollToBottom();
    }
    
    showTypingIndicator() {
        // Remove existing typing indicator if any
        this.hideTypingIndicator();
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            indicator.appendChild(dot);
        }
        
        this.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const existingIndicator = this.chatMessages.querySelector('.typing-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }
    }
    
    getCurrentTime() {
        const now = new Date();
        const hours = now.getHours().toString().padStart(2, '0');
        const minutes = now.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }
    
    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showTypingIndicator() {
        if (this.isTyping) return; // Already showing
        
        this.isTyping = true;
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'chat-message system-message typing-indicator-container';
        typingIndicator.innerHTML = `
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        
        // Set an ID so we can remove it later
        typingIndicator.id = 'typing-indicator';
        
        this.chatMessages.appendChild(typingIndicator);
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
        this.isTyping = false;
    }
    
    formatMovieRecommendation(movie) {
        return `
            <div class="movie-recommendation">
                <div class="movie-title">${movie.title} (${movie.year})</div>
                <div class="movie-details">
                    ${movie.genres ? `<span>${movie.genres.slice(0, 3).join(', ')}</span>` : ''}
                    ${movie.plot ? `<p>${movie.plot}</p>` : ''}
                </div>
            </div>
        `;
    }
}

// Initialize the chat component when the page is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if the chat component should be initialized
    if (typeof INIT_MOVIE_BUDDY_CHAT === 'undefined' || INIT_MOVIE_BUDDY_CHAT) {
        window.movieBuddyChat = new MovieBuddyChat({
            position: 'bottom-right',
            theme: 'dark',
            autoOpen: false
        });
    }
});
