# Moodflix - Voice-Activated Movie Recommendation System

![Moodflix Logo](static/Untitled%20design%20(2).png)

Moodflix is an AI-powered movie recommendation platform that suggests movies based on your current mood and preferences. Using both voice recognition and text input, Moodflix combines advanced sentiment analysis with machine learning algorithms to provide personalized movie recommendations tailored to how you're feeling.

## Key Features

- **Voice-Activated Recommendations**: Speak into your microphone to get movie suggestions based on your preferences
- **Mood-Based Recommendations**: Get movie suggestions based on your emotional state (e.g., joyful, melancholy, inspired)
- **Sentiment Analysis**: Our system analyzes your input to detect your mood and suggest appropriate films
- **Search Functionality**: Find detailed information about specific movies
- **Trending Movies**: Discover what's popular right now
- **Movie Details**: View comprehensive information including cast, reviews, and similar movies
- **Responsive Design**: Optimized for all devices from mobile to desktop
- **Interactive UI**: Modern interface with animations and visual feedback

## Technologies Used

- **Frontend**: HTML5, CSS3, JavaScript, jQuery
- **CSS Framework**: Bootstrap 4
- **Icons**: Font Awesome
- **Autocomplete**: @tarekraafat/autocomplete.js
- **Backend**: Python with Flask framework
- **Speech Recognition**: Deepgram API for voice-to-text conversion
- **Machine Learning**: Sentiment analysis for mood-based recommendations
- **API Integration**: Movie database APIs for content

## Voice Recognition Features

Moodflix uses the Deepgram API to provide state-of-the-art voice recognition capabilities:

- **Speak Your Preferences**: Simply tell the system what kind of movie you want to watch
- **Natural Language Processing**: Our system understands conversational language and extracts preferences
- **Multi-Factor Recommendations**: Voice input is analyzed for both content (what you say) and sentiment (how you say it)
- **Multilingual Support**: Voice recognition works in multiple languages (based on Deepgram's capabilities)

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/AJAX-Movie-Recommendation-System-with-Sentiment-Analysis.git
   cd AJAX-Movie-Recommendation-System-with-Sentiment-Analysis
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up your Deepgram API key:
   - Create an account at [Deepgram](https://console.deepgram.com/signup)
   - Get your API key from the Deepgram console
   - Add your key to the `voice_movie_recommender.py` file or set it as an environment variable:
     ```
     export DEEPGRAM_API_KEY="your_api_key_here"
     ```

5. Run the application:
   ```
   python main.py
   ```

6. Open your browser and navigate to `http://localhost:5000`

## Usage

### Voice-Based Recommendations
Click on the microphone icon, speak about the type of movie you're in the mood for, and get instant recommendations based on your voice input.

### Search for a Movie
Enter a movie title in the search box on the homepage and click "Search" to view details about that specific movie.

### Get Mood-Based Recommendations
Click on any mood button (like "Joy 🌟", "Melancholy 🌧️", etc.) to receive movie recommendations tailored to that mood.

### Explore Trending Movies
Scroll down to see what movies are currently trending and click on any movie poster to see more details.

## Project Structure

```
├── main.py                     # Main Flask application
├── voice_movie_recommender.py  # Voice recognition and recommendation engine
├── deepgram_test.py            # Testing utilities for Deepgram API
├── static/                     # Static assets
│   ├── images/                 # Image files
│   ├── style.css               # CSS styles
│   └── recommend.js            # JavaScript for recommendations
├── templates/                  # HTML templates
│   ├── home.html               # Homepage template
│   ├── movie_details.html      # Movie details page
│   └── recommend.html          # Recommendations page
├── models/                     # Machine learning models
├── requirements.txt            # Project dependencies
└── README.md                   # Project documentation
```

## Example Voice Commands

- "I'm feeling happy and want to watch a comedy from the 90s"
- "Recommend me a sci-fi thriller with suspense"
- "I'm in the mood for an action movie with Keanu Reeves"
- "Show me inspirational movies about overcoming challenges"
- "I want to watch something relaxing and heartwarming tonight"

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Acknowledgments

- Voice recognition powered by [Deepgram](https://deepgram.com/)
- Movie data provided by [TMDb](https://www.themoviedb.org/) or similar APIs
- Inspired by modern streaming platforms and recommendation systems
- Special thanks to all contributors who helped in building this project

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with ❤️ by Moodflix Team


