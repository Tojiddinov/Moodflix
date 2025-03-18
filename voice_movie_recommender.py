import os
import sys
import time
import json
import requests
import random
import tempfile
import re
import pandas as pd
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
        
        # Define valid categories for detection
        self.genres = ["action", "comedy", "drama", "horror", "sci-fi", "romance", "thriller", 
                      "documentary", "animation", "fantasy", "adventure", "crime", "family", 
                      "mystery", "war", "history", "biography", "music", "sport"]
        
        self.moods = ["happy", "sad", "excited", "relaxed", "scared", "inspired", "tense", 
                     "romantic", "curious", "nostalgic", "emotional", "calm", "mysterious", 
                     "adventurous", "funny", "uplifting", "dark", "thoughtful", "hopeful"]
        
        self.eras = ["80s", "90s", "2000s", "2010s", "2020s", "classic", "modern", "1950s", 
                    "1960s", "1970s", "old", "new", "recent", "vintage", "retro"]
        
        # Load the movie database from CSV
        self.movie_database = self._load_movie_database()
        
    def _load_movie_database(self):
        """Load the movie database from main_data_updated.csv"""
        try:
            # Load the dataset
            data = pd.read_csv('main_data_updated.csv')
            print(f"Loaded {len(data)} movies from main_data_updated.csv")
            
            # Convert to our internal format for processing
            movies = []
            for idx, row in data.iterrows():
                # Extract and clean genres
                genres = row.get('genres', '').lower().split(',')
                genres = [g.strip() for g in genres if g.strip()]
                
                # Extract mood if available
                mood = row.get('mood', '').lower() if 'mood' in row else None
                
                # Extract year from movie title if available
                year = None
                title = row.get('movie_title', '')
                year_match = re.search(r'\((\d{4})\)$', title)
                if year_match:
                    year = int(year_match.group(1))
                    # Remove year from title
                    title = title.replace(f"({year})", "").strip()
                
                # Create movie object
                movie = {
                    "title": title,
                    "year": year,
                    "genres": genres,
                    "mood": mood,
                    "movie_id": row.get('movie_id') if 'movie_id' in row else idx,
                    "plot": row.get('overview', '') if 'overview' in row else row.get('movie_title', ''),
                    "actors": [],  # We don't have actor data in the CSV
                    "directors": [],  # We don't have director data in the CSV
                    "themes": []  # We don't have explicit theme data in the CSV
                }
                movies.append(movie)
            
            return movies
        except Exception as e:
            print(f"Error loading movie database: {e}")
            # Fallback to a small sample database
            return self._create_sample_database()
    
    def _create_sample_database(self):
        """Create a sample movie database for fallback"""
        print("Using sample movie database as fallback")
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
            if os.path.exists(file_path):
                os.unlink(file_path)
            
            return transcript
            
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            return None
    
    def extract_preferences(self, text):
        """Extract movie preferences from user text"""
        # Reset preferences for each new request
        self.user_preferences = {
            "genres": [],
            "mood": None,
            "era": None,
            "actors": [],
            "directors": [],
            "themes": []
        }
        
        text = text.lower()
        
        # Extract genres - check for both direct mentions and related terms
        genre_keywords = {
            "action": ["action", "fighting", "battles", "explosions"],
            "comedy": ["comedy", "funny", "humorous", "hilarious", "laugh"],
            "drama": ["drama", "dramatic", "serious", "intense"],
            "horror": ["horror", "scary", "frightening", "terrifying"],
            "sci-fi": ["sci-fi", "science fiction", "futuristic", "space"],
            "romance": ["romance", "romantic", "love story"],
            "thriller": ["thriller", "suspense", "suspenseful", "tense"],
            "documentary": ["documentary", "real life", "true story"],
            "animation": ["animation", "animated", "cartoon"],
            "fantasy": ["fantasy", "magical", "mythical"],
            "adventure": ["adventure", "adventurous", "journey", "quest"],
            "crime": ["crime", "criminal", "detective", "mystery"],
            "family": ["family", "kids", "children"],
            "war": ["war", "military", "battle"],
            "history": ["history", "historical", "period", "era"],
            "biography": ["biography", "biographical", "true story", "based on"]
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in text for keyword in keywords):
                if genre not in self.user_preferences["genres"]:
                    self.user_preferences["genres"].append(genre)
        
        # Direct genre mentions
        for genre in self.genres:
            if genre in text and genre not in self.user_preferences["genres"]:
                self.user_preferences["genres"].append(genre)
        
        # Extract mood using more sophisticated pattern matching
        mood_keywords = {
            "happy": ["happy", "cheerful", "uplifting", "upbeat", "feel good", "joy", "joyful", "happiness"],
            "sad": ["sad", "melancholy", "depressing", "sorrow", "tragedy", "tragic", "emotional"],
            "excited": ["excited", "thrilling", "adrenaline", "action-packed", "fast-paced", "energetic"],
            "relaxed": ["relaxed", "calm", "soothing", "peaceful", "gentle", "slow", "easy"],
            "scared": ["scared", "frightening", "horror", "terrifying", "spooky", "creepy"],
            "inspired": ["inspired", "motivational", "uplifting", "encouraging", "inspiring"],
            "tense": ["tense", "suspenseful", "edge of seat", "nail-biting", "intense"],
            "romantic": ["romantic", "love", "romance", "heartwarming", "touching", "intimate"],
            "curious": ["curious", "intriguing", "mystery", "puzzling", "thought-provoking"],
            "adventurous": ["adventurous", "journey", "exploration", "quest", "discovery"]
        }
        
        for mood, keywords in mood_keywords.items():
            if any(keyword in text for keyword in keywords):
                self.user_preferences["mood"] = mood
                break
        
        # Extract era
        for era in self.eras:
            if era in text:
                self.user_preferences["era"] = era
                break
        
        # Try to extract year ranges
        year_ranges = {
            r"(?:from |in |)(?:the |)(\d{4})s": lambda x: x,
            r"(?:from |in |)(?:the |)(\d0)s": lambda x: f"19{x}s",
            r"(?:from |in |)(?:the |)(\d{4})": lambda x: x,
            r"recent|new|latest": lambda x: "2020s",
            r"old|classic|older": lambda x: "classic"
        }
        
        for pattern, transform in year_ranges.items():
            match = re.search(pattern, text)
            if match:
                if pattern == r"recent|new|latest" or pattern == r"old|classic|older":
                    self.user_preferences["era"] = transform(match.group(0))
                else:
                    self.user_preferences["era"] = transform(match.group(1))
                break
        
        # Extract actors and directors (very simplistic)
        # Look for patterns like "with Tom Hanks" or "starring Leonardo DiCaprio"
        actor_patterns = [
            r"with ([A-Za-z ]+)",
            r"starring ([A-Za-z ]+)",
            r"featuring ([A-Za-z ]+)",
            r"has ([A-Za-z ]+) in it"
        ]
        
        for pattern in actor_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Clean up and split on "and" or commas
                actors = re.split(r' and |, ', match)
                for actor in actors:
                    actor = actor.strip()
                    if actor and actor not in self.user_preferences["actors"] and len(actor.split()) <= 3:
                        self.user_preferences["actors"].append(actor)
        
        # Extract directors with patterns like "directed by Spielberg"
        director_patterns = [
            r"directed by ([A-Za-z ]+)",
            r"by director ([A-Za-z ]+)",
            r"([A-Za-z ]+)'s film"
        ]
        
        for pattern in director_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                directors = re.split(r' and |, ', match)
                for director in directors:
                    director = director.strip()
                    if director and director not in self.user_preferences["directors"] and len(director.split()) <= 3:
                        self.user_preferences["directors"].append(director)
        
        # Extract themes based on keywords
        theme_keywords = {
            "friendship": ["friendship", "friends", "buddy"],
            "love": ["love", "romance", "relationship"],
            "family": ["family", "parenting", "parents", "father", "mother", "siblings"],
            "revenge": ["revenge", "vengeance", "getting back"],
            "coming of age": ["coming of age", "growing up", "maturity"],
            "survival": ["survival", "surviving", "survive"],
            "war": ["war", "battle", "conflict", "military"],
            "crime": ["crime", "criminal", "heist", "robbery"],
            "mystery": ["mystery", "puzzle", "detective"],
            "adventure": ["adventure", "journey", "quest", "expedition"],
            "dystopia": ["dystopia", "post-apocalyptic", "future", "dystopian"],
            "superhero": ["superhero", "hero", "superpower"],
            "magic": ["magic", "magical", "wizard", "witch", "sorcery"],
            "science": ["science", "scientific", "researcher", "experiment"],
            "sports": ["sports", "sport", "athlete", "competition", "game"],
            "music": ["music", "musical", "musician", "band", "concert"],
            "historical": ["history", "historical", "period", "era"]
        }
        
        for theme, keywords in theme_keywords.items():
            if any(keyword in text for keyword in keywords):
                if theme not in self.user_preferences["themes"]:
                    self.user_preferences["themes"].append(theme)
        
        print(f"Extracted preferences: {self.user_preferences}")
    
    def recommend_movies(self, limit=5):
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
            if self.user_preferences["mood"] and movie.get("mood") and self.user_preferences["mood"] == movie["mood"]:
                score += 2
            
            # Score for matching era
            if self.user_preferences["era"] and movie.get("era") and self.user_preferences["era"] == movie["era"]:
                score += 2
            elif self.user_preferences["era"] and movie.get("year"):
                # Convert era to year range and check if movie year falls within
                era_ranges = {
                    "80s": (1980, 1989),
                    "90s": (1990, 1999),
                    "2000s": (2000, 2009),
                    "2010s": (2010, 2019),
                    "2020s": (2020, 2029),
                    "1950s": (1950, 1959),
                    "1960s": (1960, 1969),
                    "1970s": (1970, 1979),
                    "classic": (1920, 1979),
                    "modern": (1980, 2029),
                    "old": (1920, 1979),
                    "new": (2000, 2029),
                    "recent": (2015, 2029),
                    "vintage": (1950, 1979),
                    "retro": (1970, 1989)
                }
                
                if self.user_preferences["era"] in era_ranges:
                    start_year, end_year = era_ranges[self.user_preferences["era"]]
                    if start_year <= movie["year"] <= end_year:
                        score += 2
            
            # Score for matching actors
            if self.user_preferences["actors"] and movie.get("actors"):
                for actor in self.user_preferences["actors"]:
                    actor_lower = actor.lower()
                    if any(actor_lower in a.lower() for a in movie["actors"]):
                        score += 2
            
            # Score for matching directors
            if self.user_preferences["directors"] and movie.get("directors"):
                for director in self.user_preferences["directors"]:
                    director_lower = director.lower()
                    if any(director_lower in d.lower() for d in movie["directors"]):
                        score += 2
            
            # Score for matching themes
            if self.user_preferences["themes"] and movie.get("themes"):
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
            response = "What kind of movie are you in the mood for? Tell me about genres, actors, or themes you enjoy."
            self.conversation_history.append({"role": "system", "content": response})
            return response
        
        # Get recommendations based on preferences
        recommendations = self.recommend_movies(limit=3)
        
        if not recommendations:
            response = "I'm having trouble finding movies that match your preferences. Could you tell me more about what you're looking for?"
            self.conversation_history.append({"role": "system", "content": response})
            return response
        
        # Format recommendations
        response = "Based on what you've told me, you might enjoy these movies:\n\n"
        for movie in recommendations:
            response += f"• {movie['title']}"
            if movie.get('year'):
                response += f" ({movie['year']})"
            response += "\n"
            if movie.get('genres'):
                response += f"  Genres: {', '.join(movie['genres'])}\n"
            if movie.get('plot'):
                response += f"  Plot: {movie['plot']}\n"
            response += "\n"
        
        response += "Would you like more recommendations or should I refine these based on additional preferences?"
        
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