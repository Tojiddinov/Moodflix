# MoodFlix: Emotion-Driven Movie Recommendation System

MoodFlix is an AI-powered movie recommendation system that suggests films based on your current mood. Using voice recognition technology, MoodFlix listens to how you're feeling and provides tailored movie recommendations to match or enhance your emotional state.

## Features

- **Voice-Activated Recommendations**: Speak naturally about how you're feeling, and MoodFlix will understand your mood
- **Text-to-Speech Responses**: MoodFlix responds with a natural-sounding voice for a conversational experience
- **10 Mood Categories**: Get recommendations based on feeling happy, sad, excited, bored, angry, scared, nostalgic, curious, tired, or confused
- **Movie Posters & Details**: See visual movie posters along with year, genre, and plot information
- **Recommendation History**: Track your past recommendations and moods over time
- **Adjustable Voice Volume**: Control the AI's speaking volume with an easy slider
- **Demo Buttons**: Reliable demonstration options for showcasing the system
- **Animated UI**: Enjoy a visually appealing interface with smooth animations

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/moodflix.git
cd moodflix
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

3. Run the application:
```
python real_voice_demo.py
```

4. Open your browser and navigate to:
```
http://localhost:5001
```

## Usage

1. Click the microphone button and speak how you're feeling:
   - "I feel happy"
   - "I'm sad today"
   - "I'm feeling bored"
   - "I'm curious about something new"

2. MoodFlix will process your mood and recommend appropriate movies, speaking its response aloud.

3. Adjust the voice volume using the slider if needed.

4. View your recommendation history by clicking the "View Recommendation History" button.

5. For reliable demonstrations, use the demo buttons at the bottom of the interface.

## Requirements

- Python 3.6+
- Flask
- SpeechRecognition
- PyAudio
- pyttsx3
- Pygame

## Project Structure

- `real_voice_demo.py`: Main application file
- `templates/`: Generated HTML templates
- `README.md`: Project documentation
- `requirements.txt`: Required Python packages

## Future Enhancements

- Expanded movie database with more titles
- Additional mood categories for more precise recommendations
- User profiles to store preferences
- Movie poster image retrieval from TMDB API
- Mobile app integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Developed as part of a research project on emotion-driven recommendation systems
- Movie data adapted from public datasets 
