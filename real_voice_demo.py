import os
import sys
import time
import tempfile
import random
import pygame
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import pyttsx3  # Add text-to-speech engine

# Initialize Flask app
app = Flask(__name__)

# Initialize text-to-speech engine
try:
    tts_engine = pyttsx3.init()
    # Set properties for the voice
    tts_engine.setProperty('rate', 150)  # Speed of speech
    tts_engine.setProperty('volume', 0.9)  # Volume (0-1)
    voices = tts_engine.getProperty('voices')
    # Try to set a more natural sounding voice if available
    for voice in voices:
        if "female" in voice.name.lower():
            tts_engine.setProperty('voice', voice.id)
            break
    print("Text-to-speech initialized successfully")
    TTS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize text-to-speech: {e}")
    TTS_AVAILABLE = False

# Simple movie database for testing
SAMPLE_MOVIES = [
    {
        "title": "The Shawshank Redemption",
        "year": 1994,
        "genres": ["Drama"],
        "plot": "Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
        "poster": "https://m.media-amazon.com/images/M/MV5BNDE3ODcxYzMtY2YzZC00NmNlLWJiNDMtZDViZWM2MzIxZDYwXkEyXkFqcGdeQXVyNjAwNDUxODI@._V1_.jpg"
    },
    {
        "title": "The Godfather",
        "year": 1972,
        "genres": ["Crime", "Drama"],
        "plot": "The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
        "poster": "https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg"
    },
    {
        "title": "Pulp Fiction",
        "year": 1994,
        "genres": ["Crime", "Drama"],
        "plot": "The lives of two mob hitmen, a boxer, a gangster and his wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
        "poster": "https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg"
    },
    {
        "title": "Forrest Gump",
        "year": 1994,
        "genres": ["Drama", "Romance"],
        "plot": "The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate, and other historical events unfold through the perspective of an Alabama man.",
        "poster": "https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg"
    },
    {
        "title": "The Dark Knight",
        "year": 2008,
        "genres": ["Action", "Crime", "Drama"],
        "plot": "When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, Batman must accept one of the greatest psychological and physical tests of his ability to fight injustice.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_.jpg"
    },
    {
        "title": "Inception",
        "year": 2010,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "plot": "A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_.jpg"
    },
    {
        "title": "Toy Story",
        "year": 1995,
        "genres": ["Animation", "Adventure", "Comedy"],
        "plot": "A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMDU2ZWJlMjktMTRhMy00ZTA5LWEzNDgtYmNmZTEwZTViZWJkXkEyXkFqcGdeQXVyNDQ2OTk4MzI@._V1_.jpg"
    },
    {
        "title": "The Matrix",
        "year": 1999,
        "genres": ["Action", "Sci-Fi"],
        "plot": "A computer hacker learns from mysterious rebels about the true nature of his reality and his role in the war against its controllers.",
        "poster": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_.jpg"
    },
    {
        "title": "Finding Nemo",
        "year": 2003,
        "genres": ["Animation", "Adventure", "Comedy"],
        "plot": "After his son is captured in the Great Barrier Reef and taken to Sydney, a timid clownfish sets out on a journey to bring him home.",
        "poster": "https://m.media-amazon.com/images/M/MV5BZTAzNWZlNmUtZDEzYi00ZjA5LWIwYjEtZGM1NWE1MjE4YWRhXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_.jpg"
    },
    {
        "title": "The Lion King",
        "year": 1994,
        "genres": ["Animation", "Adventure", "Drama"],
        "plot": "Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.",
        "poster": "https://m.media-amazon.com/images/M/MV5BYTYxNGMyZTYtMjE3MS00MzNjLWFjNmYtMDk3N2FmM2JiM2M1XkEyXkFqcGdeQXVyNjY5NDU4NzI@._V1_.jpg"
    },
    {
        "title": "Interstellar",
        "year": 2014,
        "genres": ["Adventure", "Drama", "Sci-Fi"],
        "plot": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.",
        "poster": "https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZkNWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg"
    },
    {
        "title": "The Silence of the Lambs",
        "year": 1991,
        "genres": ["Crime", "Drama", "Thriller"],
        "plot": "A young F.B.I. cadet must receive the help of an incarcerated and manipulative cannibal killer to help catch another serial killer.",
        "poster": "https://m.media-amazon.com/images/M/MV5BNjNhZTk0ZmEtNjJhMi00YzFlLWE1MmEtYzM1M2ZmMGMwMTU4XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_.jpg"
    },
    {
        "title": "Titanic",
        "year": 1997,
        "genres": ["Drama", "Romance"],
        "plot": "A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMDdmZGU3NDQtY2E5My00ZTliLWIzOTUtMTY4ZGI1YjdiNjk3XkEyXkFqcGdeQXVyNTA4NzY1MzY@._V1_.jpg"
    },
    {
        "title": "The Avengers",
        "year": 2012,
        "genres": ["Action", "Adventure", "Sci-Fi"],
        "plot": "Earth's mightiest heroes must come together and learn to fight as a team if they are going to stop the mischievous Loki from enslaving humanity.",
        "poster": "https://m.media-amazon.com/images/M/MV5BNDYxNjQyMjAtNTdiOS00NGYwLWFmNTAtNThmYjU5ZGI2YTI1XkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg"
    },
    {
        "title": "Spirited Away",
        "year": 2001,
        "genres": ["Animation", "Adventure", "Family"],
        "plot": "During her family's move to the suburbs, a sullen 10-year-old girl wanders into a world ruled by gods, witches, and spirits, where humans are changed into beasts.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMjlmZmI5MDctNDE2YS00YWE0LWE5ZWItZDBhYWQ0NTcxNWRhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg"
    },
    {
        "title": "Fight Club",
        "year": 1999,
        "genres": ["Drama", "Thriller"],
        "plot": "An insomniac office worker and a devil-may-care soapmaker form an underground fight club that evolves into something much, much more.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMmEzNTkxYjQtZTc0MC00YTVjLTg5ZTEtZWMwOWVlYzY0NWIwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg"
    },
    {
        "title": "The Notebook",
        "year": 2004,
        "genres": ["Drama", "Romance"],
        "plot": "A poor yet passionate young man falls in love with a rich young woman, giving her a sense of freedom, but they are soon separated because of their social differences.",
        "poster": "https://m.media-amazon.com/images/M/MV5BMTk3OTM5Njg5M15BMl5BanBnXkFtZTYwMzA0ODI3._V1_.jpg"
    },
    {
        "title": "Memento",
        "year": 2000,
        "genres": ["Mystery", "Thriller"],
        "plot": "A man with short-term memory loss attempts to track down his wife's murderer.",
        "poster": "https://m.media-amazon.com/images/M/MV5BZTcyNjk1MjgtOWI3Mi00YzQwLWI5MTktMzY4ZmI2NDAyNzYzXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_.jpg"
    },
    {
        "title": "Back to the Future",
        "year": 1985,
        "genres": ["Adventure", "Comedy", "Sci-Fi"],
        "plot": "Marty McFly, a 17-year-old high school student, is accidentally sent thirty years into the past in a time-traveling DeLorean.",
        "poster": "https://m.media-amazon.com/images/M/MV5BZmU0M2Y1OGUtZjIxNi00ZjBkLTg1MjgtOWIyNThiZWIwYjRiXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg"
    },
    {
        "title": "The Shining",
        "year": 1980,
        "genres": ["Drama", "Horror"],
        "plot": "A family heads to an isolated hotel for the winter where a sinister presence influences the father into violence.",
        "poster": "https://m.media-amazon.com/images/M/MV5BZWFlYmY2MGEtZjVkYS00YzU4LTg0YjQtYzY1ZGE3NTA5NGQxXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg"
    }
]

# Mood mappings for recommendations
MOOD_MAPPINGS = {
    "sad": ["Drama", "Romance"],
    "happy": ["Comedy", "Animation", "Adventure"],
    "bad": ["Comedy", "Adventure", "Animation"],
    "excited": ["Action", "Adventure", "Sci-Fi"],
    "bored": ["Action", "Thriller", "Comedy"],
    "relaxed": ["Animation", "Comedy", "Romance"],
    "angry": ["Action", "Crime", "Thriller"],
    "scared": ["Drama", "Crime", "Thriller"],
    "nostalgic": ["Drama", "Romance", "Animation"],
    "curious": ["Sci-Fi", "Adventure", "Mystery"],
    "tired": ["Comedy", "Animation", "Romance"],
    "confused": ["Sci-Fi", "Thriller", "Mystery"]
}

class RealVoiceMovieBuddy:
    """MovieBuddy AI with real voice recognition"""
    
    def __init__(self):
        """Initialize the movie buddy AI"""
        print("Initializing RealVoiceMovieBuddy...")
        self.movies = SAMPLE_MOVIES
        self.recommendation_history = []  # Add this line to store past recommendations
        
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 4000  # Higher for noisy environments
        self.recognizer.dynamic_energy_threshold = True
        
        # Initialize pygame for audio playback (optional)
        try:
            pygame.mixer.init()
            print("Audio playback initialized")
        except:
            print("Warning: Pygame mixer initialization failed. Audio playback may not work.")
    
    def speak(self, text):
        """Speak the given text using text-to-speech"""
        print(f"Speaking: {text}")
        if TTS_AVAILABLE:
            try:
                tts_engine.say(text)
                tts_engine.runAndWait()
                return True
            except Exception as e:
                print(f"Error speaking text: {e}")
                return False
        return False
    
    def introduce(self):
        """Basic introduction function with speech"""
        intro = "Hey, I'm MovieBuddy AI! Your personal movie recommendation assistant. How can I help you today?"
        print(f"MovieBuddy says: {intro}")
        self.speak(intro)
        return intro
    
    def listen(self):
        """Listen for user input using the microphone with improved recognition"""
        text = None
        try:
            with sr.Microphone() as source:
                print("Adjusting for ambient noise...")
                # Longer adjustment for better ambient noise handling
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                print("Listening...")
                
                # Increase timeout and phrase time limit for better capture
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=8)
                
                try:
                    print("Recognizing speech...")
                    # Try with Google first (most accurate)
                    try:
                        text = self.recognizer.recognize_google(audio)
                        print(f"Google recognized: {text}")
                    except:
                        # Fall back to Sphinx (works offline but less accurate)
                        try:
                            import speech_recognition as sr_fallback
                            text = self.recognizer.recognize_sphinx(audio)
                            print(f"Sphinx recognized: {text}")
                        except:
                            # Last resort - just try Google again with a different API key
                            text = self.recognizer.recognize_google(audio)
                            print(f"Second attempt, Google recognized: {text}")
                    
                    if text:
                        print(f"You said: {text}")
                except sr.UnknownValueError:
                    print("Could not understand audio")
                    self.speak("I'm sorry, I couldn't understand what you said. Could you please try again?")
                except sr.RequestError as e:
                    print(f"Error with the speech recognition service: {e}")
                    self.speak("I'm having trouble with my hearing. Could you please try again?")
        except Exception as e:
            print(f"Error listening: {e}")
            self.speak("I encountered a problem while listening. Please try again.")
        
        return text
    
    def demo_listen(self, demo_phrase):
        """Simulate listening by returning a demo phrase without using the microphone"""
        print(f"DEMO MODE: Simulating voice input: '{demo_phrase}'")
        return demo_phrase
    
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
            recommendations = []
            if len(matching_movies) > count:
                recommendations = random.sample(matching_movies, count)
            else:
                recommendations = matching_movies
                
            # Add to history with timestamp
            if recommendations:
                self.recommendation_history.append({
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "mood": mood,
                    "recommendations": recommendations
                })
                # Keep only the last 10 recommendations
                if len(self.recommendation_history) > 10:
                    self.recommendation_history = self.recommendation_history[-10:]
                    
            return recommendations
        else:
            # Return random movies if mood not recognized
            recommendations = random.sample(self.movies, min(count, len(self.movies)))
            
            # Add to history with timestamp
            self.recommendation_history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "mood": "random",
                "recommendations": recommendations
            })
            # Keep only the last 10 recommendations
            if len(self.recommendation_history) > 10:
                self.recommendation_history = self.recommendation_history[-10:]
                
            return recommendations
    
    def get_recommendation_history(self):
        """Return the recommendation history"""
        return self.recommendation_history
    
    def process_input(self, user_input):
        """Process user input and return appropriate response"""
        if not user_input:
            return {
                "success": False,
                "error": "Sorry, I couldn't hear that. Could you please try again?"
            }
            
        user_input = user_input.lower().strip()
        
        # Check for greetings - make this more robust by looking for keywords
        greeting_keywords = ['hey', 'hello', 'hi']
        is_greeting = False
        
        # Check if any greeting keyword is in the input
        for keyword in greeting_keywords:
            if keyword in user_input:
                is_greeting = True
                break
                
        # Also check for variations of MovieBuddy
        movie_buddy_variations = ['moviebuddyai', 'movie buddy ai', 'movie buddy', 'moviebuddy']
        for variation in movie_buddy_variations:
            if variation in user_input:
                is_greeting = True
                break
        
        if is_greeting:
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
            'bad': ['i feel bad', 'feeling bad', 'i am feeling bad', 'i\'m feeling bad', 'i feel bad', 'feeling bad'],
            'bored': ['i feel bored', 'feeling bored', 'i am bored', 'i\'m bored'],
            'excited': ['i feel excited', 'feeling excited', 'i am excited', 'i\'m excited'],
            'relaxed': ['i feel relaxed', 'feeling relaxed', 'i am relaxed', 'i\'m relaxed'],
            'angry': ['i feel angry', 'feeling angry', 'i am angry', 'i\'m angry', 'i\'m mad', 'i am mad'],
            'scared': ['i feel scared', 'feeling scared', 'i am scared', 'i\'m scared', 'i\'m afraid', 'i am afraid'],
            'nostalgic': ['i feel nostalgic', 'feeling nostalgic', 'i am nostalgic', 'i\'m nostalgic', 'i miss the old days'],
            'curious': ['i feel curious', 'feeling curious', 'i am curious', 'i\'m curious', 'i want to learn'],
            'tired': ['i feel tired', 'feeling tired', 'i am tired', 'i\'m tired', 'i\'m exhausted'],
            'confused': ['i feel confused', 'feeling confused', 'i am confused', 'i\'m confused', 'i don\'t understand']
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
            elif matched_mood == 'angry':
                response = f"I understand you're feeling {matched_mood}. These intense movies might help channel that energy. "
            elif matched_mood == 'scared':
                response = f"If you're feeling {matched_mood}, these thrilling films might help you process those emotions. "
            elif matched_mood == 'nostalgic':
                response = f"Feeling {matched_mood}? These classic films should satisfy your yearning for the good old days. "
            elif matched_mood == 'curious':
                response = f"For someone feeling {matched_mood}, these thought-provoking movies will feed your inquisitive mind. "
            elif matched_mood == 'tired':
                response = f"When you're feeling {matched_mood}, these light-hearted movies are perfect for relaxation. "
            elif matched_mood == 'confused':
                response = f"If you're feeling {matched_mood}, these mind-bending films might actually make sense to you right now. "
            else:
                response = f"I see you're feeling {matched_mood}. Here are some movies that match your mood. "
            
            # Add recommendations to response
            for i, movie in enumerate(recommendations, 1):
                response += f"Movie {i}: {movie['title']} from {movie['year']}. "
                if movie.get('genres'):
                    response += f"It's a {', '.join(movie['genres'][:2])} movie. "
            
            print(f"MovieBuddy says: {response}")
            self.speak(response)
            
            return {
                "success": True,
                "transcript": user_input,
                "response": response,
                "recommendations": recommendations
            }
        
        # Default response for other inputs
        response = "I'm not sure what you're looking for. Try saying something like 'I feel sad' or 'I'm bored' for movie recommendations."
        
        print(f"MovieBuddy says: {response}")
        self.speak(response)
        
        return {
            "success": True,
            "transcript": user_input,
            "response": response,
            "recommendations": random.sample(self.movies, 3)  # Random recommendations as fallback
        }

    def set_speech_volume(self, volume):
        """Set the volume for text-to-speech (0.0 to 1.0)"""
        global TTS_AVAILABLE
        if TTS_AVAILABLE:
            try:
                volume = float(volume)
                if 0.0 <= volume <= 1.0:
                    tts_engine.setProperty('volume', volume)
                    return True
                else:
                    print(f"Volume must be between 0.0 and 1.0, got: {volume}")
                    return False
            except Exception as e:
                print(f"Error setting speech volume: {e}")
                return False
        return False

# Create an instance of the MovieBuddy AI
movie_buddy = RealVoiceMovieBuddy()

# Flask routes
@app.route("/")
def home():
    """Render the interface"""
    return render_template("real_voice_interface.html")

@app.route("/listen", methods=["POST"])
def listen():
    """Listen for voice input and process it"""
    try:
        user_input = movie_buddy.listen()
        if user_input:
            result = movie_buddy.process_input(user_input)
            # Add TTS status to the response
            result["tts_available"] = TTS_AVAILABLE
            return jsonify(result)
        else:
            return jsonify({
                "success": False,
                "error": "I couldn't hear what you said. Please try again.",
                "tts_available": TTS_AVAILABLE
            })
    except Exception as e:
        print(f"Error in listen route: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}",
            "tts_available": TTS_AVAILABLE
        })

@app.route("/process_text", methods=["POST"])
def process_text():
    """Process text input for backup when voice isn't working"""
    text = request.json.get("text", "")
    
    if not text:
        return jsonify({
            "success": False,
            "error": "No input provided",
            "tts_available": TTS_AVAILABLE
        })
    
    result = movie_buddy.process_input(text)
    # Add TTS status to the response
    result["tts_available"] = TTS_AVAILABLE
    return jsonify(result)

@app.route("/demo_listen", methods=["POST"])
def demo_listen():
    """Simulate voice input for demo purposes"""
    try:
        demo_phrase = request.json.get("demo_phrase", "")
        if not demo_phrase:
            return jsonify({
                "success": False,
                "error": "No demo phrase provided",
                "tts_available": TTS_AVAILABLE
            })
            
        user_input = movie_buddy.demo_listen(demo_phrase)
        result = movie_buddy.process_input(user_input)
        # Add TTS status to the response
        result["tts_available"] = TTS_AVAILABLE
        return jsonify(result)
    except Exception as e:
        print(f"Error in demo_listen route: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}",
            "tts_available": TTS_AVAILABLE
        })

@app.route("/set_volume", methods=["POST"])
def set_volume():
    """Set the speech volume"""
    try:
        volume = request.json.get("volume", 0.9)
        success = movie_buddy.set_speech_volume(volume)
        return jsonify({
            "success": success,
            "volume": volume,
            "tts_available": TTS_AVAILABLE
        })
    except Exception as e:
        print(f"Error in set_volume route: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}",
            "tts_available": TTS_AVAILABLE
        })

@app.route("/history", methods=["GET"])
def get_history():
    """Get the recommendation history"""
    try:
        history = movie_buddy.get_recommendation_history()
        return jsonify({
            "success": True,
            "history": history
        })
    except Exception as e:
        print(f"Error in history route: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"An error occurred: {str(e)}"
        })

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    if not os.path.exists("templates"):
        os.makedirs("templates")
    
    # Create the HTML interface
    with open("templates/real_voice_interface.html", "w", encoding="utf-8") as f:
        f.write("""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MovieBuddy AI - Voice Demo</title>
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
        button {
            padding: 15px 30px;
            background-color: #e50914;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 0;
            display: block;
            width: 100%;
        }
        .mic-button {
            border-radius: 50%;
            width: 80px;
            height: 80px;
            margin: 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            background-color: #e50914;
        }
        .mic-button.listening {
            background-color: #cc0000;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        .conversation-area {
            background-color: #222;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
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
        .status {
            text-align: center;
            margin: 10px 0;
            font-weight: bold;
            min-height: 20px;
        }
        .instructions {
            text-align: center;
            margin-bottom: 20px;
        }
        .movie-card {
            background-color: #2a2a2a;
            border-radius: 8px;
            padding: 15px;
            margin-top: 10px;
            opacity: 0;
            transform: translateY(20px);
            animation: fadeIn 0.6s forwards;
            animation-delay: calc(var(--animation-order, 0) * 0.2s);
            display: flex;
            align-items: flex-start;
        }
        .movie-poster {
            width: 100px;
            height: 150px;
            object-fit: cover;
            border-radius: 4px;
            margin-right: 15px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5);
        }
        .movie-info {
            flex: 1;
        }
        @keyframes fadeIn {
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        .backup-input {
            display: flex;
            margin-top: 20px;
        }
        .backup-input input {
            flex: 1;
            padding: 10px;
            border: none;
            border-radius: 5px 0 0 5px;
            font-size: 16px;
        }
        .backup-input button {
            width: auto;
            border-radius: 0 5px 5px 0;
            margin: 0;
        }
        .speaking-indicator {
            background-color: #e50914;
            padding: 8px 15px;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin: 10px auto;
            max-width: 250px;
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 0.7; }
            50% { opacity: 1; }
            100% { opacity: 0.7; }
        }
        .demo-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 20px 0;
        }
        .demo-btn {
            flex: 1;
            min-width: 200px;
            text-align: center;
        }
        .demo-section {
            background-color: #333;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .demo-section h3 {
            text-align: center;
            margin-top: 0;
            color: #e50914;
        }
        .volume-control {
            margin: 20px 0;
            background-color: #333;
            padding: 15px;
            border-radius: 8px;
        }
        .slider {
            width: 100%;
            height: 10px;
            border-radius: 5px;
            background: #444;
            outline: none;
            -webkit-appearance: none;
        }
        .slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%; 
            background: #e50914;
            cursor: pointer;
        }
        .slider::-moz-range-thumb {
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #e50914;
            cursor: pointer;
        }
        .history-button-container {
            margin-top: 20px;
            text-align: center;
        }
        #historyButton {
            background-color: #333;
            color: white;
            width: auto;
            display: inline-block;
        }
        .modal {
            display: none;
            position: fixed;
            z-index: 999;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            overflow: auto;
            background-color: rgba(0,0,0,0.8);
        }
        .modal-content {
            background-color: #1a1a1a;
            margin: 10% auto;
            padding: 20px;
            border: 1px solid #333;
            border-radius: 10px;
            width: 80%;
            max-width: 700px;
            color: white;
        }
        .close {
            color: #aaa;
            float: right;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }
        .close:hover {
            color: white;
        }
        .history-item {
            background-color: #333;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
        }
        .history-timestamp {
            color: #888;
            font-size: 0.8em;
        }
        .history-mood {
            font-weight: bold;
            color: #e50914;
            margin: 10px 0;
        }
        .history-movies {
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <h1>MovieBuddy AI Voice Assistant</h1>
    
    <div class="container">
        <div class="instructions">
            <p>Try these voice commands:</p>
            <p><strong>Say "Hey MovieBuddy AI"</strong> to get an introduction</p>
            <p><strong>Say "I feel bad"</strong> to get mood-based recommendations</p>
        </div>
        
        <div class="mic-button" id="micButton">MIC</div>
        
        <div class="status" id="status">Click the microphone to start</div>
        
        <div class="demo-section">
            <h3>EXAM DEMO BUTTONS</h3>
            <p style="text-align: center;">For guaranteed demonstration during your exam:</p>
            <div class="demo-buttons">
                <button class="demo-btn" id="demoGreeting">Demo: "Hey MovieBuddy AI"</button>
                <button class="demo-btn" id="demoFeelBad">Demo: "I feel bad"</button>
                <button class="demo-btn" id="demoFeelSad">Demo: "I'm feeling sad"</button>
                <button class="demo-btn" id="demoFeelBored">Demo: "I'm bored"</button>
                <button class="demo-btn" id="demoFeelAngry">Demo: "I'm angry"</button>
                <button class="demo-btn" id="demoFeelScared">Demo: "I'm scared"</button>
                <button class="demo-btn" id="demoFeelNostalgic">Demo: "I feel nostalgic"</button>
                <button class="demo-btn" id="demoFeelCurious">Demo: "I'm curious"</button>
                <button class="demo-btn" id="demoFeelTired">Demo: "I feel tired"</button>
                <button class="demo-btn" id="demoFeelConfused">Demo: "I'm confused"</button>
            </div>
            <p style="text-align: center; font-size: 0.9em;">These buttons simulate voice input for reliable demo</p>
        </div>
        
        <div class="conversation-area" id="conversationArea"></div>
        
        <div class="backup-input">
            <input type="text" id="textInput" placeholder="Type here if voice isn't working...">
            <button id="sendButton">Send</button>
        </div>
        
        <div class="volume-control">
            <label for="volumeSlider">Speech Volume: <span id="volumeValue">90%</span></label>
            <input type="range" id="volumeSlider" min="0" max="100" value="90" class="slider">
        </div>
        
        <div class="history-button-container">
            <button id="historyButton">View Recommendation History</button>
        </div>
        
        <div id="historyModal" class="modal">
            <div class="modal-content">
                <span class="close">&times;</span>
                <h2>Your Recommendation History</h2>
                <div id="historyContent"></div>
            </div>
        </div>
    </div>
    
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const micButton = document.getElementById('micButton');
            const status = document.getElementById('status');
            const conversationArea = document.getElementById('conversationArea');
            const textInput = document.getElementById('textInput');
            const sendButton = document.getElementById('sendButton');
            
            // Demo buttons
            const demoGreeting = document.getElementById('demoGreeting');
            const demoFeelBad = document.getElementById('demoFeelBad');
            const demoFeelSad = document.getElementById('demoFeelSad');
            const demoFeelBored = document.getElementById('demoFeelBored');
            const demoFeelAngry = document.getElementById('demoFeelAngry');
            const demoFeelScared = document.getElementById('demoFeelScared');
            const demoFeelNostalgic = document.getElementById('demoFeelNostalgic');
            const demoFeelCurious = document.getElementById('demoFeelCurious');
            const demoFeelTired = document.getElementById('demoFeelTired');
            const demoFeelConfused = document.getElementById('demoFeelConfused');
            
            let isListening = false;
            
            // Add message to conversation
            function addMessage(text, isUser) {
                const messageDiv = document.createElement('div');
                messageDiv.className = isUser ? 'message user-message' : 'message ai-message';
                
                if (isUser) {
                    messageDiv.innerHTML = `<strong>You said:</strong> ${text}`;
                } else {
                    messageDiv.innerHTML = `<strong>MovieBuddy AI:</strong> ${text}`;
                }
                
                conversationArea.appendChild(messageDiv);
                conversationArea.scrollTop = conversationArea.scrollHeight;
            }
            
            // Add recommendations to conversation
            function addRecommendations(recommendations) {
                if (!recommendations || recommendations.length === 0) return;
                
                const recsDiv = document.createElement('div');
                recsDiv.className = 'message ai-message';
                
                let recsHtml = '<strong>Recommended Movies:</strong><br>';
                recommendations.forEach((movie, index) => {
                    recsHtml += `
                        <div class="movie-card" style="--animation-order: ${index}">
                            <img class="movie-poster" src="${movie.poster || 'https://via.placeholder.com/100x150?text=No+Poster'}" alt="${movie.title} poster">
                            <div class="movie-info">
                                <h4>${movie.title} (${movie.year})</h4>
                                <p><strong>Genres:</strong> ${movie.genres.join(', ')}</p>
                                <p>${movie.plot}</p>
                            </div>
                        </div>
                    `;
                });
                
                recsDiv.innerHTML = recsHtml;
                conversationArea.appendChild(recsDiv);
                conversationArea.scrollTop = conversationArea.scrollHeight;
            }
            
            // Handle microphone button click
            micButton.addEventListener('click', function() {
                if (isListening) {
                    // Do nothing, wait for response
                    return;
                }
                
                // Start listening
                isListening = true;
                micButton.classList.add('listening');
                status.textContent = 'Listening...';
                
                // Make request to server
                fetch('/listen', {
                    method: 'POST'
                })
                .then(response => response.json())
                .then(data => {
                    isListening = false;
                    micButton.classList.remove('listening');
                    
                    if (data.success) {
                        status.textContent = 'MovieBuddy AI is responding...';
                        
                        // Add the conversation to the UI
                        if (data.transcript) {
                            addMessage(data.transcript, true);
                        }
                        
                        if (data.response) {
                            // Visual indication that MovieBuddy is speaking
                            const speakingDiv = document.createElement('div');
                            speakingDiv.className = 'speaking-indicator';
                            speakingDiv.innerHTML = '<span>MovieBuddy AI is speaking...</span>';
                            conversationArea.appendChild(speakingDiv);
                            
                            // Add the actual response
                            setTimeout(() => {
                                // Remove speaking indicator
                                conversationArea.removeChild(speakingDiv);
                                // Add the response
                                addMessage(data.response, false);
                                
                                // Add recommendations if any
                                if (data.recommendations && data.recommendations.length > 0) {
                                    addRecommendations(data.recommendations);
                                }
                                
                                status.textContent = 'Click the microphone to speak again';
                            }, data.response.length * 50); // Rough estimate of speaking time
                        } else {
                            status.textContent = 'Click the microphone to speak again';
                        }
                    } else {
                        status.textContent = data.error || 'Error processing voice input';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    isListening = false;
                    micButton.classList.remove('listening');
                    status.textContent = 'Error connecting to server. Please try again.';
                });
            });
            
            // Handle text input as backup
            sendButton.addEventListener('click', function() {
                const text = textInput.value.trim();
                if (!text) return;
                
                status.textContent = 'Processing...';
                
                fetch('/process_text', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: text })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Add the conversation to the UI
                        addMessage(text, true);
                        
                        if (data.response) {
                            addMessage(data.response, false);
                        }
                        
                        if (data.recommendations && data.recommendations.length > 0) {
                            addRecommendations(data.recommendations);
                        }
                        
                        status.textContent = 'Click the microphone to speak again';
                    } else {
                        status.textContent = data.error || 'Error processing input';
                    }
                    
                    textInput.value = '';
                })
                .catch(error => {
                    console.error('Error:', error);
                    status.textContent = 'Error connecting to server. Please try again.';
                });
            });
            
            // Handle Enter key in text input
            textInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendButton.click();
                }
            });
            
            // Handle demo button clicks
            function handleDemoButton(demoPhrase) {
                status.textContent = `Demo: Simulating saying "${demoPhrase}"...`;
                
                fetch('/demo_listen', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ demo_phrase: demoPhrase })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        status.textContent = 'MovieBuddy AI is responding...';
                        
                        // Add user message to the UI
                        addMessage(demoPhrase, true);
                        
                        if (data.response) {
                            // Visual indication that MovieBuddy is speaking
                            const speakingDiv = document.createElement('div');
                            speakingDiv.className = 'speaking-indicator';
                            speakingDiv.innerHTML = '<span>MovieBuddy AI is speaking...</span>';
                            conversationArea.appendChild(speakingDiv);
                            
                            // Add the actual response after a delay
                            setTimeout(() => {
                                // Remove speaking indicator
                                conversationArea.removeChild(speakingDiv);
                                // Add the response
                                addMessage(data.response, false);
                                
                                // Add recommendations if any
                                if (data.recommendations && data.recommendations.length > 0) {
                                    addRecommendations(data.recommendations);
                                }
                                
                                status.textContent = 'Demo completed successfully';
                            }, data.response.length * 50); // Rough estimate of speaking time
                        } else {
                            status.textContent = 'Demo completed successfully';
                        }
                    } else {
                        status.textContent = data.error || 'Error in demo';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    status.textContent = 'Error connecting to server. Please try again.';
                });
            }
            
            // Add event listeners for demo buttons
            demoGreeting.addEventListener('click', function() {
                status.textContent = `Demo: Simulating saying "Hey MovieBuddy AI"...`;
                
                fetch('/demo_listen', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ demo_phrase: "Hey MovieBuddy AI" })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        status.textContent = 'MovieBuddy AI is responding...';
                        
                        // Add the conversation to the UI
                        addMessage("Hey MovieBuddy AI", true);
                        
                        if (data.response) {
                            addMessage(data.response, false);
                        }
                        
                        // Don't show recommendations for greeting
                        
                        status.textContent = 'Demo completed successfully';
                    } else {
                        status.textContent = data.error || 'Error in demo';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    status.textContent = 'Error connecting to server. Please try again.';
                });
            });
            
            demoFeelBad.addEventListener('click', function() {
                handleDemoButton("I feel bad");
            });
            
            demoFeelSad.addEventListener('click', function() {
                handleDemoButton("I'm feeling sad");
            });
            
            demoFeelBored.addEventListener('click', function() {
                handleDemoButton("I'm bored");
            });
            
            demoFeelAngry.addEventListener('click', function() {
                handleDemoButton("I'm angry");
            });
            
            demoFeelScared.addEventListener('click', function() {
                handleDemoButton("I'm scared");
            });
            
            demoFeelNostalgic.addEventListener('click', function() {
                handleDemoButton("I feel nostalgic");
            });
            
            demoFeelCurious.addEventListener('click', function() {
                handleDemoButton("I'm curious");
            });
            
            demoFeelTired.addEventListener('click', function() {
                handleDemoButton("I feel tired");
            });
            
            demoFeelConfused.addEventListener('click', function() {
                handleDemoButton("I'm confused");
            });
            
            // Add volume slider event listener
            const volumeSlider = document.getElementById('volumeSlider');
            const volumeValue = document.getElementById('volumeValue');
            
            volumeSlider.addEventListener('input', function() {
                const volume = this.value / 100;
                volumeValue.textContent = `${this.value}%`;
                
                fetch('/set_volume', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ volume: volume })
                })
                .then(response => response.json())
                .then(data => {
                    console.log("Volume set:", data);
                })
                .catch(error => {
                    console.error('Error setting volume:', error);
                });
            });
            
            // History modal functionality
            const historyButton = document.getElementById('historyButton');
            const historyModal = document.getElementById('historyModal');
            const historyContent = document.getElementById('historyContent');
            const closeBtn = document.getElementsByClassName('close')[0];
            
            historyButton.addEventListener('click', function() {
                // Fetch history and populate modal
                fetch('/history')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.history.length > 0) {
                            let historyHTML = '';
                            data.history.forEach(item => {
                                historyHTML += `
                                    <div class="history-item">
                                        <div class="history-timestamp">${item.timestamp}</div>
                                        <div class="history-mood">Mood: ${item.mood}</div>
                                        <div class="history-movies">
                                            <strong>Recommended movies:</strong>
                                            <ul>
                                                ${item.recommendations.map(movie => 
                                                    `<li>${movie.title} (${movie.year}) - ${movie.genres.join(', ')}</li>`
                                                ).join('')}
                                            </ul>
                                        </div>
                                    </div>
                                `;
                            });
                            historyContent.innerHTML = historyHTML;
                        } else {
                            historyContent.innerHTML = '<p>No recommendation history found.</p>';
                        }
                        historyModal.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('Error fetching history:', error);
                        historyContent.innerHTML = '<p>Error loading recommendation history.</p>';
                        historyModal.style.display = 'block';
                    });
            });
            
            closeBtn.addEventListener('click', function() {
                historyModal.style.display = 'none';
            });
            
            window.addEventListener('click', function(event) {
                if (event.target == historyModal) {
                    historyModal.style.display = 'none';
                }
            });
        });
    </script>
</body>
</html>
""")
    
    print("Starting MovieBuddy AI with real voice recognition...")
    app.run(debug=True, port=5001) 