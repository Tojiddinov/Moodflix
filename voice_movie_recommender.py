import os
import sys
import time
import json
import requests
import random
import tempfile
import re
from pathlib import Path

# Check if required packages are installed, if not install them
try:
    from pydub import AudioSegment
    from pydub.playback import play
except ImportError:
    print("Installing required packages...")
    os.system('pip install pydub')
    from pydub import AudioSegment
    from pydub.playback import play

try:
    import sounddevice as sd
    import scipy.io.wavfile as wav
except ImportError:
    print("Installing required packages for microphone recording...")
    os.system('pip install sounddevice scipy')
    import sounddevice as sd
    import scipy.io.wavfile as wav

# Your Deepgram API key
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"

class VoiceMovieRecommender:
    def __init__(self):
        self.conversation_history = []
        self.user_preferences = {
            "genres": [],
            "mood": None,
            "era": None,
            "actors": [],
            "directors": [],
            "themes": []
        }
        
        # For demo purposes, define some movie categories
        self.genres = ["action", "comedy", "drama", "horror", "sci-fi", "romance", "thriller", "documentary"]
        self.moods = ["happy", "sad", "excited", "relaxed", "scared", "inspired", "tense"]
        self.eras = ["80s", "90s", "2000s", "2010s", "2020s", "classic", "modern"]
        
        # Sample movie database
        self.movie_database = self._load_movie_database()
        
    def _load_movie_database(self):
        """Load or create a sample movie database for testing"""
        # In a real system, this would load from your actual database
        # For this demo, we'll create a small sample
        return [
            {"title": "The Matrix", "year": 1999, "genres": ["sci-fi", "action"], "mood": "excited", "era": "90s", 
             "actors": ["Keanu Reeves", "Laurence Fishburne"], "directors": ["Wachowski Sisters"], 
             "themes": ["cyberpunk", "dystopia"], "plot": "A computer hacker learns about the true nature of reality."},
            
            {"title": "The Shawshank Redemption", "year": 1994, "genres": ["drama"], "mood": "inspired", "era": "90s", 
             "actors": ["Tim Robbins", "Morgan Freeman"], "directors": ["Frank Darabont"], 
             "themes": ["prison", "friendship"], "plot": "Two imprisoned men bond over a number of years."},
            
            {"title": "The Dark Knight", "year": 2008, "genres": ["action", "thriller"], "mood": "tense", "era": "2000s", 
             "actors": ["Christian Bale", "Heath Ledger"], "directors": ["Christopher Nolan"], 
             "themes": ["superhero", "crime"], "plot": "Batman fights the menace known as the Joker."},
            
            {"title": "Pulp Fiction", "year": 1994, "genres": ["crime", "drama"], "mood": "tense", "era": "90s", 
             "actors": ["John Travolta", "Samuel L. Jackson"], "directors": ["Quentin Tarantino"], 
             "themes": ["crime", "redemption"], "plot": "Various interconnected crime stories."},
            
            {"title": "Forrest Gump", "year": 1994, "genres": ["drama", "comedy"], "mood": "inspired", "era": "90s", 
             "actors": ["Tom Hanks"], "directors": ["Robert Zemeckis"], 
             "themes": ["life", "love"], "plot": "The life story of a man with a low IQ but good intentions."},
            
            {"title": "Inception", "year": 2010, "genres": ["sci-fi", "action"], "mood": "tense", "era": "2010s", 
             "actors": ["Leonardo DiCaprio"], "directors": ["Christopher Nolan"], 
             "themes": ["dreams", "heist"], "plot": "A thief who steals corporate secrets through dream-sharing technology."},
            
            {"title": "The Godfather", "year": 1972, "genres": ["crime", "drama"], "mood": "tense", "era": "classic", 
             "actors": ["Marlon Brando", "Al Pacino"], "directors": ["Francis Ford Coppola"], 
             "themes": ["mafia", "family"], "plot": "The aging patriarch of an organized crime dynasty transfers control to his son."},
            
            {"title": "The Lion King", "year": 1994, "genres": ["animation", "adventure"], "mood": "happy", "era": "90s", 
             "actors": ["Matthew Broderick", "James Earl Jones"], "directors": ["Roger Allers", "Rob Minkoff"], 
             "themes": ["coming of age", "family"], "plot": "A young lion prince flees his kingdom after his father is murdered."},
            
            {"title": "Get Out", "year": 2017, "genres": ["horror", "thriller"], "mood": "scared", "era": "2010s", 
             "actors": ["Daniel Kaluuya"], "directors": ["Jordan Peele"], 
             "themes": ["race", "social commentary"], "plot": "A young African-American visits his white girlfriend's parents."},
            
            {"title": "La La Land", "year": 2016, "genres": ["romance", "musical"], "mood": "happy", "era": "2010s", 
             "actors": ["Ryan Gosling", "Emma Stone"], "directors": ["Damien Chazelle"], 
             "themes": ["dreams", "love"], "plot": "A pianist and an actress fall in love while pursuing their dreams."}
        ]
    
    def record_audio(self, duration=5):
        """Record audio from the microphone"""
        print(f"\n🎤 Recording for {duration} seconds... Speak now!")
        
        # Record audio
        fs = 16000  # Sample rate
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()  # Wait until recording is finished
        
        # Save recording to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_filename = temp_file.name
            wav.write(temp_filename, fs, recording)
        
        print("✅ Recording finished.")
        return temp_filename
    
    def transcribe_audio(self, file_path):
        """Transcribe audio using Deepgram"""
        print("🔍 Transcribing...")
        
        try:
            url = "https://api.deepgram.com/v1/listen"
            
            headers = {
                "Authorization": f"Token {DEEPGRAM_API_KEY}",
                "Content-Type": "audio/wav"
            }
            
            params = {
                "model": "nova-2",
                "smart_format": "true",
                "punctuate": "true"
            }
            
            with open(file_path, "rb") as audio:
                audio_data = audio.read()
                response = requests.post(url, headers=headers, params=params, data=audio_data)
            
            if response.status_code != 200:
                print(f"Error: API returned status {response.status_code}")
                print(response.text)
                return None
            
            data = response.json()
            transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
            
            # Clean up the temporary file
            os.unlink(file_path)
            
            return transcript
            
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            return None
    
    def extract_preferences(self, text):
        """Extract movie preferences from user text"""
        text = text.lower()
        
        # Extract genres
        for genre in self.genres:
            if genre in text:
                if genre not in self.user_preferences["genres"]:
                    self.user_preferences["genres"].append(genre)
        
        # Extract mood
        for mood in self.moods:
            if mood in text:
                self.user_preferences["mood"] = mood
                break
        
        # Extract era
        for era in self.eras:
            if era in text:
                self.user_preferences["era"] = era
                break
        
        # Extract actors, directors and themes
        # This would be more sophisticated in a real system
        # For demo purposes, we're just looking for common patterns
        
        # Look for actor names (very simplistic)
        actor_match = re.findall(r'with ([\w\s]+)', text)
        if actor_match:
            potential_actors = [name.strip() for name in actor_match[0].split('and')]
            for actor in potential_actors:
                if actor and actor not in self.user_preferences["actors"]:
                    self.user_preferences["actors"].append(actor)
        
        # Extract themes based on specific keywords
        themes = ["adventure", "love", "friendship", "family", "war", "crime", 
                 "dystopia", "fantasy", "superhero", "magic", "history"]
        for theme in themes:
            if theme in text:
                if theme not in self.user_preferences["themes"]:
                    self.user_preferences["themes"].append(theme)
    
    def recommend_movies(self, limit=3):
        """Recommend movies based on user preferences"""
        if not any(self.user_preferences.values()):
            return []
        
        # Score each movie based on matching preferences
        scored_movies = []
        for movie in self.movie_database:
            score = 0
            
            # Score for matching genres
            if self.user_preferences["genres"]:
                for genre in self.user_preferences["genres"]:
                    if genre in movie["genres"]:
                        score += 3
            
            # Score for matching mood
            if self.user_preferences["mood"] and self.user_preferences["mood"] == movie["mood"]:
                score += 2
            
            # Score for matching era
            if self.user_preferences["era"] and self.user_preferences["era"] == movie["era"]:
                score += 2
            
            # Score for matching actors
            if self.user_preferences["actors"]:
                for actor in self.user_preferences["actors"]:
                    if any(actor.lower() in a.lower() for a in movie["actors"]):
                        score += 2
            
            # Score for matching themes
            if self.user_preferences["themes"]:
                for theme in self.user_preferences["themes"]:
                    if theme in movie["themes"]:
                        score += 1
            
            if score > 0:
                scored_movies.append((movie, score))
        
        # Sort by score
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        
        # Return top movies
        return [movie for movie, score in scored_movies[:limit]]
    
    def get_system_response(self, user_input):
        """Generate a system response based on the conversation state"""
        # Extract preferences from user input
        self.extract_preferences(user_input)
        
        # Update conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        
        # If this is the first interaction, ask about preferences
        if len(self.conversation_history) == 1:
            response = "Hi there! I'd be happy to recommend some movies for you. What kind of movies do you like? Do you prefer any specific genres, actors, or time periods?"
        
        # If we have some preferences but not enough, ask more questions
        elif len(self.conversation_history) < 4 and not self.user_preferences["mood"]:
            response = "That's helpful! Are you in the mood for something happy, sad, exciting, or something else?"
        
        # After gathering preferences, provide recommendations
        else:
            recommendations = self.recommend_movies()
            
            if recommendations:
                response = "Based on our conversation, I think you might enjoy these movies:\n\n"
                for i, movie in enumerate(recommendations, 1):
                    response += f"{i}. {movie['title']} ({movie['year']}) - {movie['plot']}\n"
                
                response += "\nWould you like more recommendations or different ones?"
            else:
                response = "I'm having trouble finding movies that match your preferences. Could you tell me more about what you're looking for?"
        
        # Add response to conversation history
        self.conversation_history.append({"role": "system", "content": response})
        
        return response
    
    def conversation_loop(self):
        """Run the main conversation loop"""
        print("=" * 50)
        print("🎬 Voice Movie Recommendation System 🎬")
        print("=" * 50)
        print("This system will listen to your voice and recommend movies.")
        print("Press Ctrl+C at any time to exit.")
        print("\nSystem: Hello! I can help you find movies to watch. Just speak into your microphone.")
        
        try:
            while True:
                # Record audio
                audio_file = self.record_audio(duration=7)
                
                # Transcribe audio
                transcript = self.transcribe_audio(audio_file)
                
                if transcript:
                    print(f"\nYou said: {transcript}")
                    
                    # Get system response
                    response = self.get_system_response(transcript)
                    print(f"\nSystem: {response}")
                    
                    # Check if the user wants to exit
                    if "exit" in transcript.lower() or "quit" in transcript.lower() or "goodbye" in transcript.lower():
                        print("\nThank you for using the Voice Movie Recommendation System. Goodbye!")
                        break
                else:
                    print("\nSorry, I couldn't understand what you said. Could you try again?")
                
                print("\nSpeak again when ready...")
        
        except KeyboardInterrupt:
            print("\n\nExiting the Voice Movie Recommendation System. Thank you!")

# Run the recommender if this script is executed directly
if __name__ == "__main__":
    recommender = VoiceMovieRecommender()
    recommender.conversation_loop() 