# MoodFlix 3.0: Enhanced Real-Time AI Movie Recommendation System

MoodFlix is an AI-powered movie recommendation system that suggests films based on your current mood. Using advanced voice recognition technology, MoodFlix listens to how you're feeling and provides tailored movie recommendations to match or enhance your emotional state. Now featuring real-time chat with MovieBuddyAI for instant, conversational movie recommendations.

## 🚀 New in Version 3.0

- **Real-Time Chat with MovieBuddyAI**: Instantly chat with our AI assistant for immediate movie recommendations
- **Enhanced Voice Processing**: Optimized audio handling with browser-compatible WebM/Opus format
- **No FFmpeg Dependency**: Streamlined audio processing without external dependencies
- **Robust Voice Recognition**: Multi-stage recognition with improved fallback mechanisms
- **Better Error Handling**: Enhanced feedback and recovery from recognition errors
- **Optimized Audio Processing**: Mono channel, 16kHz optimization for speech recognition
- **Improved Temporary File Management**: Better cleanup of audio processing artifacts

## 🚀 Features from Version 2.0

- **Modernized Architecture**: Completely refactored with a modular, maintainable codebase
- **Enhanced API**: RESTful API endpoints for all functionality
- **Improved Speech Recognition**: Multi-engine speech recognition with fallback options
- **Better Mood Detection**: Advanced natural language processing for mood detection
- **Docker Support**: Easy deployment with Docker and Docker Compose
- **Environment Configuration**: Secure configuration using environment variables
- **Expanded Movie Database**: Support for larger movie datasets
- **User Profiles**: Support for user accounts and personalized recommendations (coming soon)

## 🎯 Features

- **Real-Time Chat Interface**: Converse naturally with MovieBuddyAI for immediate recommendations
- **Enhanced Voice-Activated Recommendations**: More reliable speech recognition across browsers
- **Cross-Browser Audio Support**: Works consistently across different browsers and setups
- **Text-to-Speech Responses**: Natural-sounding voice for a conversational experience
- **Multiple Mood Categories**: Get recommendations based on 15+ mood categories
- **Movie Posters & Details**: Visual movie posters with comprehensive information
- **Recommendation History**: Track your past recommendations and moods
- **Adjustable Voice Volume**: Control the AI's speaking volume
- **Demo Options**: Reliable demonstration options for showcasing the system
- **Modern UI**: Clean, responsive interface with smooth animations

## 🛠️ Installation

### Option 1: Standard Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/moodflix.git
cd moodflix
```

2. Create and activate a virtual environment:
```
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install the required dependencies:
```
pip install -r requirements.txt
```

4. Set up environment variables:
```
# Copy the example environment file
copy .env.example .env
# Edit the .env file with your configuration
```

5. Run the application:
```
python app_main.py
```

6. Open your browser and navigate to:
```
http://localhost:5000
```

### Option 2: Docker Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/moodflix.git
cd moodflix
```

2. Set up environment variables:
```
# Copy the example environment file
copy .env.example .env
# Edit the .env file with your configuration
```

3. Build and run with Docker Compose:
```
docker-compose up -d
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## 🎮 Usage

1. Choose your preferred interaction method:
   - **Real-time Chat**: Start chatting with MovieBuddyAI for instant recommendations
   - **Voice Input**: Click the microphone button and speak naturally
   - **Text Input**: Type your request directly

2. Express what you're looking for in natural language:
   - "I need an action movie"
   - "I feel happy"
   - "I'm sad today"
   - "I'm feeling bored"
   - "Show me action movies from the 90s"
   - "I want to watch something with Tom Hanks"

3. MovieBuddyAI will respond immediately with appropriate recommendations.

4. Click on a movie to see more details or find similar movies.

5. Continue the conversation to refine recommendations or explore new options.

6. View your recommendation history to see past suggestions.

## 📁 Project Structure

```
moodflix/
├── app/                      # Application package
│   ├── api/                  # API endpoints
│   ├── core/                 # Core functionality
│   ├── models/               # Data models
│   ├── services/             # Business logic
│   ├── static/               # Static files
│   └── templates/            # HTML templates
├── scripts/                  # Utility scripts
├── tests/                    # Test suite
├── .env.example              # Example environment variables
├── app_main.py              # Application entry point
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose configuration
├── requirements.txt         # Project dependencies
└── README.md                # Project documentation
```

## 🔧 API Endpoints

- `GET /api/health`: Health check endpoint
- `POST /api/chat`: Process text chat input
- `POST /api/voice`: Process voice input with enhanced audio handling
- `POST /api/real_time_chat`: Connect to MovieBuddyAI for real-time conversations
- `GET /api/history`: Get recommendation history
- `POST /api/movie_details`: Get details for a specific movie
- `POST /api/similar_movies`: Get similar movies
- `POST /api/set_volume`: Set the text-to-speech volume
- `WS /socket.io`: WebSocket endpoint for real-time chat functionality

## 🔜 Future Enhancements

- Advanced context-aware conversations with MovieBuddyAI
- Voice personality customization
- Integration with more streaming services for direct viewing
- Offline voice recognition for privacy-focused users
- User accounts with personalized recommendation profiles
- Collaborative filtering for improved social recommendations
- Mobile app with cross-platform support
- Watchlist and favorites functionality
- Streaming service availability information

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👏 Acknowledgments

- Developed as part of a research project on emotion-driven recommendation systems
- Movie data adapted from public datasets
