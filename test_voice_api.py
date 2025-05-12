import os
import time
import json
import tempfile
import random
import pygame
from flask import Flask, render_template, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Simple movie database for testing
SAMPLE_MOVIES = [
    {
        "title": "The Shawshank Redemption",
        "year": 1994,
        "genres": ["Drama"],
        "plot": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency."
    },
    {
        "title": "The Godfather",
        "year": 1972,
        "genres": ["Crime", "Drama"],
        "plot": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son."
    },
    {
        "title": "Pulp Fiction",
        "year": 1994,
        "genres": ["Crime", "Drama"],
        "plot": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption."
    },
    {
        "title": "Forrest Gump",
        "year": 1994,
        "genres": ["Drama", "Romance"],
        "plot": "The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate, and other historical events unfold through the perspective of an Alabama man."
    },
    {
        "title": "The Dark Knight",
        "year": 2008,
        "genres": ["Action", "Crime", "Drama"],
        "plot": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice."
    },
    {
        "title": "Inception",
        "year": 2010,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "plot": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O."
    },
    {
        "title": "Toy Story",
        "year": 1995,
        "genres": ["Animation", "Adventure", "Comedy"],
        "plot": "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room."
    },
    {
        "title": "The Matrix",
        "year": 1999,
        "genres": ["Action", "Sci-Fi"],
        "plot": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers."
    },
    {
        "title": "Finding Nemo",
        "year": 2003,
        "genres": ["Animation", "Adventure", "Comedy"],
        "plot": "After his son is captured in the Great Barrier Reef and taken to Sydney, a timid clownfish sets out on a journey to bring him home."
    },
    {
        "title": "The Lion King",
        "year": 1994,
        "genres": ["Animation", "Adventure", "Drama"],
        "plot": "Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself."
    }
]

# Mood mappings for recommendations
MOOD_MAPPINGS = {
    "sad": ["Drama", "Romance"],
    "happy": ["Comedy", "Animation", "Adventure"],
    "bad": ["Comedy", "Adventure", "Animation"],
    "excited": ["Action", "Adventure", "Sci-Fi"],
    "bored": ["Action", "Thriller", "Comedy"],
    "relaxed": ["Animation", "Comedy", "Romance"]
}

class TestMovieBuddyAI:
    """Simple MovieBuddy AI for testing purposes"""
    
    def __init__(self):
        """Initialize the test movie buddy AI"""
        print("Initializing TestMovieBuddyAI...")
        self.movies = SAMPLE_MOVIES
        
        # Initialize pygame for audio playback (optional)
        try:
            pygame.mixer.init()
        except:
            print("Warning: Pygame mixer initialization failed. Audio playback may not work.")
    
    def introduce(self):
        """Basic introduction function"""
        intro = "Hey, I'm MovieBuddy AI! Your personal movie recommendation assistant. How can I help you today?"
        print(f"MovieBuddy says: {intro}")
        return intro
    
    def recommend_movies(self, mood, count=3):
        """Recommend movies based on mood"""
        if mood.lower() in MOOD_MAPPINGS:
            genres = MOOD_MAPPINGS[mood.lower()]
            
            # Filter movies by genre
            matching_movies = []
            for movie in self.movies:
                for genre in movie["genres"]:
                    if genre in genres and movie not in matching_movies:
                        matching_movies.append(movie)
                        break
            
            # Return random sample of matching movies
            if len(matching_movies) > count:
                return random.sample(matching_movies, count)
            else:
                return matching_movies
        else:
            # Return random movies if mood not recognized
            return random.sample(self.movies, min(count, len(self.movies)))
    
    def process_input(self, user_input):
        """Process user input and return appropriate response"""
        user_input = user_input.lower().strip()
        
        # Check for greetings
        if user_input in ['hey', 'hello', 'hi', 'hey there', 'hello there', 'hi there', 'hey moviebuddyai', 'hey movie buddy ai', 'hey movie buddy']:
            response = self.introduce()
            return {
                "success": True,
                "transcript": user_input,
                "response": response,
                "recommendations": [],
                "waiting_for_follow_up": True
            }
        
        # Check for mood-based recommendations
        mood_phrases = {
            'sad': ['i feel sad', 'feeling sad', 'i am sad', 'i\'m sad'],
            'happy': ['i feel happy', 'feeling happy', 'i am happy', 'i\'m happy'],
            'bad': ['i feel bad', 'feeling bad', 'i am feeling bad', 'i\'m feeling bad'],
            'bored': ['i feel bored', 'feeling bored', 'i am bored', 'i\'m bored'],
            'excited': ['i feel excited', 'feeling excited', 'i am excited', 'i\'m excited'],
            'relaxed': ['i feel relaxed', 'feeling relaxed', 'i am relaxed', 'i\'m relaxed']
        }
        
        matched_mood = None
        for mood, phrases in mood_phrases.items():
            for phrase in phrases:
                if phrase in user_input:
                    matched_mood = mood
                    break
            if matched_mood:
                break
        
        if matched_mood:
            # Get recommendations
            recommendations = self.recommend_movies(matched_mood)
            
            # Create response
            if matched_mood == 'bad':
                response = f"I'm sorry to hear you're feeling {matched_mood}. Let me recommend some movies to cheer you up. "
            elif matched_mood == 'sad':
                response = f"I understand you're feeling {matched_mood}. Here are some movies that might help lift your spirits. "
            elif matched_mood == 'bored':
                response = f"Feeling {matched_mood}? I've got some exciting movies that will definitely entertain you. "
            else:
                response = f"I see you're feeling {matched_mood}. Here are some movies that match your mood. "
            
            # Add recommendations to response
            for i, movie in enumerate(recommendations, 1):
                response += f"Movie {i}: {movie['title']} from {movie['year']}. "
                if movie.get('genres'):
                    response += f"It's a {', '.join(movie['genres'][:2])} movie. "
            
            print(f"MovieBuddy says: {response}")
            
            return {
                "success": True,
                "transcript": user_input,
                "response": response,
                "recommendations": recommendations
            }
        
        # Default response for other inputs
        response = "I'm not sure what you're looking for. Try saying something like 'I feel sad' or 'I'm bored' for movie recommendations."
        
        print(f"MovieBuddy says: {response}")
        
        return {
            "success": True,
            "transcript": user_input,
            "response": response,
            "recommendations": random.sample(self.movies, 3)  # Random recommendations as fallback
        }

# Create an instance of the MovieBuddy AI
movie_buddy = TestMovieBuddyAI()

# Flask routes
@app.route("/")
def home():
    """Render the test interface"""
    return render_template("test_interface.html")

@app.route("/process_input", methods=["POST"])
def process_input():
    """Process text input for testing without audio"""
    text = request.json.get("text", "")
    
    if not text:
        return jsonify({
            "success": False,
            "error": "No input provided"
        })
    
    result = movie_buddy.process_input(text)
    return jsonify(result)

@app.route("/voice_recommend", methods=["POST"])
def voice_recommend():
    """Handle simulated voice input (just use text in this test version)"""
    # In a real implementation, this would process audio
    # For the test version, we just extract text from the form data
    
    # Check if audio file exists (for compatibility with the real version)
    if 'audio_data' in request.files:
        # Return a mock response for the audio file
        return jsonify({
            "success": True,
            "transcript": "This is a simulated voice transcript",
            "response": "I understood your request. Here are some movie recommendations for you.",
            "recommendations": random.sample(SAMPLE_MOVIES, 3)
        })
    
    # If no audio but text is provided
    text = request.form.get("text", "")
    if text:
        result = movie_buddy.process_input(text)
        return jsonify(result)
    
    # Demo mode - return a predefined response
    return jsonify({
        "success": True,
        "transcript": "I feel sad",
        "response": "I understand you're feeling sad. Here are some movies that might help lift your spirits.",
        "recommendations": random.sample(SAMPLE_MOVIES, 3)
    })

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    if not os.path.exists("templates"):
        os.makedirs("templates")
    
    # Create a simple HTML interface for testing
    with open("templates/test_interface.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieBuddy AI - Test Interface</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #0c0c0c;
            color: #fff;
        }
        h1 {
            color: #e50914;
            text-align: center;
        }
        .container {
            background-color: #1a1a1a;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
        }
        .input-area {
            display: flex;
            margin-bottom: 20px;
        }
        input {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 5px 0 0 5px;
            font-size: 16px;
        }
        button {
            padding: 10px 20px;
            background-color: #e50914;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 5px;
        }
        .demo-button {
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            width: 300px;
            display: block;
            margin: 0 auto 20px;
        }
        .response-area {
            background-color: #333;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .movie-card {
            background-color: #2a2a2a;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 10px;
        }
        .intro-section {
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            text-align: center;
            color: #e50914;
            margin: 15px 0;
            font-weight: bold;
        }
        .hidden {
            display: none;
        }
        .conversation-flow {
            background-color: #222;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 8px;
        }
        .user-message {
            background-color: #444;
            text-align: right;
        }
        .ai-message {
            background-color: #333;
        }
    </style>
</head>
<body>
    <h1>MovieBuddy AI Test Interface</h1>
    
    <div class="container intro-section">
        <p><strong>EXAM DEMO:</strong> This test shows how MovieBuddy AI works like Siri or Alexa.</p>
        <p>Click the button below to simulate a complete voice conversation with MovieBuddy AI:</p>
        <ol>
            <li>User says "Hey MovieBuddyAI" → AI introduces itself</li>
            <li>User says "I feel bad" → AI recommends mood-based movies</li>
        </ol>
    </div>
    
    <div class="container">
        <button id="startDemoButton" class="demo-button">Start Complete Demo</button>
        
        <div class="status" id="status">Click the button above to start the demo</div>
        
        <div class="conversation-flow hidden" id="conversationFlow">
            <!-- Conversation will be shown here -->
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const startDemoButton = document.getElementById('startDemoButton');
            const status = document.getElementById('status');
            const conversationFlow = document.getElementById('conversationFlow');
            
            // Function to add message to conversation
            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.className = isUser ? 'message user-message' : 'message ai-message';
                
                if (isUser) {
                    messageDiv.innerHTML = `<strong>You said:</strong> ${text}`;
                } else {
                    messageDiv.innerHTML = `<strong>MovieBuddy AI:</strong> ${text}`;
                }
                
                conversationFlow.appendChild(messageDiv);
                
                // Scroll to bottom of conversation
                conversationFlow.scrollTop = conversationFlow.scrollHeight;
            }
            
            // Function to process demo input
            function processDemo(demoText) {
                return new Promise((resolve, reject) => {
                    status.textContent = "Processing: " + demoText;
                    
                    fetch('/process_input', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ text: demoText })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            resolve(data);
                        } else {
                            status.textContent = data.error || "An error occurred";
                            reject(data.error || "An error occurred");
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        status.textContent = "Error processing request";
                        reject(error);
                    });
                });
            }
            
            // Function to show recommendations
            function showRecommendations(recommendations) {
                let recsHtml = '<div class="recommendations-section">';
                recsHtml += '<h4>Recommended Movies:</h4>';
                
                recommendations.forEach(movie => {
                    recsHtml += `
                        <div class="movie-card">
                            <h4>${movie.title} (${movie.year})</h4>
                            <p><strong>Genres:</strong> ${movie.genres.join(', ')}</p>
                            <p>${movie.plot}</p>
                        </div>
                    `;
                });
                
                recsHtml += '</div>';
                
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ai-message';
                messageDiv.innerHTML = recsHtml;
                conversationFlow.appendChild(messageDiv);
            }
            
            // Complete demo sequence
            async function runFullDemo() {
                try {
                    startDemoButton.disabled = true;
                    conversationFlow.classList.remove('hidden');
                    conversationFlow.innerHTML = '';
                    
                    // Step 1: Greeting
                    status.textContent = "Step 1: User says 'Hey MovieBuddyAI'";
                    const greeting = "Hey MovieBuddyAI";
                    addMessage(greeting, true);
                    
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Delay for realism
                    
                    const greetingResponse = await processDemo(greeting);
                    addMessage(greetingResponse.response, false);
                    
                    await new Promise(resolve => setTimeout(resolve, 3000)); // Pause between steps
                    
                    // Step 2: Mood-based recommendation
                    status.textContent = "Step 2: User says 'I feel bad'";
                    const moodRequest = "I feel bad";
                    addMessage(moodRequest, true);
                    
                    await new Promise(resolve => setTimeout(resolve, 1000)); // Delay for realism
                    
                    const moodResponse = await processDemo(moodRequest);
                    addMessage(moodResponse.response, false);
                    
                    if (moodResponse.recommendations && moodResponse.recommendations.length > 0) {
                        await new Promise(resolve => setTimeout(resolve, 1000)); // Slight delay before showing recs
                        showRecommendations(moodResponse.recommendations);
                    }
                    
                    status.textContent = "Demo completed! This is how MovieBuddy AI works like Siri/Alexa";
                    startDemoButton.disabled = false;
                    startDemoButton.textContent = "Restart Demo";
                    
                } catch (error) {
                    console.error('Demo error:', error);
                    status.textContent = "Demo failed. Please try again.";
                    startDemoButton.disabled = false;
                }
            }
            
            // Demo button click event
            startDemoButton.addEventListener('click', runFullDemo);
        });
    </script>
</body>
</html>
""")
    
    print("Starting MovieBuddy AI test server...")
    app.run(debug=True, port=5001) 