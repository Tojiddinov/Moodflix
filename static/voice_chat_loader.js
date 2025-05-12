/**
 * MoodFlix Voice Chat Loader
 * This script dynamically loads the voice chat component
 */

// Create a function to load the voice chat component
function loadVoiceChatComponent() {
    // Load CSS
    const cssLink = document.createElement('link');
    cssLink.rel = 'stylesheet';
    cssLink.href = '/static/css/voice_chat.css';
    document.head.appendChild(cssLink);
    
    // Load Font Awesome if not already loaded
    if (!document.querySelector('link[href*="font-awesome"]')) {
        const fontAwesomeLink = document.createElement('link');
        fontAwesomeLink.rel = 'stylesheet';
        fontAwesomeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css';
        document.head.appendChild(fontAwesomeLink);
    }
    
    // Load the voice chat script
    const script = document.createElement('script');
    script.src = '/static/js/voice_chat.js';
    script.onload = function() {
        // Initialize the chat component
        window.movieBuddyChat = new MovieBuddyChat({
            position: 'bottom-right',
            theme: 'dark',
            autoOpen: false
        });
    };
    document.body.appendChild(script);
    
    // Add voice chat button to the navigation menu if it exists
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
            if (window.movieBuddyChat) {
                window.movieBuddyChat.toggleChat(true);
            }
            return false;
        };
        
        // Add the link to the nav item
        navItem.appendChild(link);
        
        // Add the nav item to the menu
        navMenu.appendChild(navItem);
    }
}

// Load the component when the DOM is fully loaded
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadVoiceChatComponent);
} else {
    loadVoiceChatComponent();
}
