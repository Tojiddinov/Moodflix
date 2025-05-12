# MovieBuddy AI Demo Version

This is a simplified test version of the MovieBuddy AI voice assistant for demonstration purposes.

## Features Demonstrated

1. **Voice Assistant Interactions**:
   - Basic greeting ("Hey")
   - Mood-based movie recommendations
   - Simulated voice recording

2. **Sample Interactions**:
   - Say "Hey" for an introduction
   - Say "I feel sad" for movie recommendations for sad mood
   - Say "I'm bored" for action/thriller movie recommendations
   - Say "I feel bad" for uplifting movie recommendations

## Running the Demo

### Prerequisites
- Python 3.6 or higher
- Flask
- Pygame (for audio simulation)

### Installation

```bash
# Install required packages
pip install flask pygame
```

### Running the Demo

```bash
# Start the demo server
python test_voice_api.py
```

Then open your browser and navigate to:
```
http://localhost:5001
```

## Using the Demo

1. **Text Interaction**:
   - Type a message in the input box and click "Send"
   - Try typing "Hey" or "I feel sad"

2. **Simulated Voice Interaction**:
   - Click the microphone button to start "recording"
   - Click again to stop and process a random voice input
   - The system will simulate processing and show recommendations

## Demo Presentation Tips

1. **Show the Siri/Alexa-like Experience**:
   - Click the microphone
   - Explain that the user would speak now
   - Click again to "stop recording"
   - Show the response with personalized introduction
   - Point out how it handles emotions like "I feel bad" with appropriate responses

2. **Highlight the Mood-Based Recommendations**:
   - Demonstrate how different moods get different types of movie recommendations
   - Point out the personalized response text (e.g., "I'm sorry to hear you're feeling bad")

3. **Explain the Full Implementation**:
   - This is a simplified version for demonstration
   - The complete version connects to the actual voice recognition system
   - The full system has a more extensive movie database

## Troubleshooting

- If the application doesn't start, check that port 5001 is available
- If no recommendations appear, try refreshing the page

## Next Steps

The full implementation would include:
- Integration with actual voice recognition API
- Complete movie database integration
- User profiles and recommendation history
- Advanced mood detection algorithms 