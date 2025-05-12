/**
 * MoodFlix Voice Chat Integration Script
 * This script injects the voice chat component into any page
 */

// Function to load CSS file
function loadCSS(url) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = url;
    document.head.appendChild(link);
}

// Function to load JavaScript file
function loadScript(url, callback) {
    const script = document.createElement('script');
    script.src = url;
    script.onload = callback || function() {};
    document.head.appendChild(script);
}

// Function to load Font Awesome if not already loaded
function loadFontAwesome() {
    if (!document.querySelector('link[href*="font-awesome"]')) {
        loadCSS('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css');
    }
}

// Main initialization function
function initializeVoiceChat() {
    // Load dependencies
    loadFontAwesome();
    loadCSS('/static/css/voice_chat.css');
    
    // Set global variable to initialize chat
    window.INIT_MOVIE_BUDDY_CHAT = true;
    
    // Load the main chat script
    loadScript('/static/js/voice_chat.js');
}

// Initialize when the DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeVoiceChat);
} else {
    initializeVoiceChat();
}

// Add a function to open the chat programmatically
window.openMovieBuddyChat = function() {
    if (window.movieBuddyChat) {
        window.movieBuddyChat.toggleChat(true);
    } else {
        // If the chat isn't initialized yet, wait and try again
        setTimeout(() => {
            if (window.movieBuddyChat) {
                window.movieBuddyChat.toggleChat(true);
            }
        }, 1000);
    }
};

// Add voice chat button to the navigation menu
document.addEventListener('DOMContentLoaded', function() {
    // Find the navigation menu
    const navMenu = document.querySelector('.navbar-nav');
    if (navMenu) {
        // Create a new nav item
        const navItem = document.createElement('li');
        navItem.className = 'nav-item';
        
        // Create the link
        const link = document.createElement('a');
        link.className = 'nav-link';
        link.href = 'javascript:void(0);';
        link.innerHTML = '<i class="fas fa-microphone"></i> Voice Chat';
        link.onclick = function() {
            window.openMovieBuddyChat();
            return false;
        };
        
        // Add the link to the nav item
        navItem.appendChild(link);
        
        // Add the nav item to the menu
        navMenu.appendChild(navItem);
    }
});
