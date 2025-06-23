import asyncio
import json
import os
import time
import tempfile
import threading
import queue
import pandas as pd
import sounddevice as sd
import numpy as np
from pathlib import Path
import warnings
import requests
from gtts import gTTS
import pygame
import re
from datetime import datetime

warnings.filterwarnings('ignore')

# Your Deepgram API key
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"

class RealTimeVoiceRecommender:
    def __init__(self):
        """Initialize the real-time voice movie recommender"""
        self.movies = []
        self.conversation_active = False
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        self.conversation_history = []
        
        # Initialize pygame for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Audio recording parameters
        self.sample_rate = 16000
        self.channels = 1
        self.recording_duration = 6  # seconds - longer for better conversation
        
        # Load movie database
        print("Loading movie database...")
        self.load_movie_database()
        
        # Define recommendation categories
        self.genres = ["action", "comedy", "drama", "horror", "sci-fi", "romance", "thriller", 
                      "documentary", "animation", "fantasy", "adventure", "crime", "family", 
                      "mystery", "war", "history", "biography", "music", "sport"]
        
        self.moods = ["happy", "sad", "excited", "relaxed", "scared", "inspired", "tense", 
                     "romantic", "curious", "nostalgic", "emotional", "calm", "mysterious", 
                     "adventurous", "funny", "uplifting", "dark", "thoughtful", "hopeful"]
        
        # Conversation state
        self.wake_words = ["hey movie buddy", "movie buddy", "recommend", "suggest"]
        self.exit_words = ["goodbye", "bye", "exit", "quit", "stop"]
        self.is_awake = False
        self.last_activity = time.time()
        self.sleep_timeout = 30  # seconds
        
    def load_movie_database(self):
        """Load movie data from CSV file"""
        try:
            # Load the dataset
            df = pd.read_csv('main_data_updated.csv')
            
            for _, row in df.iterrows():
                try:
                    # Clean and process title
                    title = str(row.get('movie_title', '')).strip()
                    if not title or title == 'nan':
                        continue
                    
                    # Try to get year from title first
                    year = None
                    title_year_match = re.search(r'\((\d{4})\)', title)
                    if title_year_match:
                        year = int(title_year_match.group(1))
                        title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
                    
                    # Process genres
                    genres = []
                    genres_value = row.get('genres')
                    if genres_value is not None and pd.notna(genres_value):
                        genres = [g.strip() for g in str(genres_value).split('|') if g.strip()]
                    
                    # Process actors
                    actors = []
                    for i in range(1, 4):
                        actor = row.get(f'actor_{i}_name', '')
                        if actor is not None and pd.notna(actor) and str(actor).strip():
                            actors.append(str(actor).strip())
                    
                    # Process director
                    director = row.get('director_name', '')
                    directors = []
                    if director is not None and pd.notna(director) and str(director).strip():
                        directors = [str(director).strip()]
                    
                    # Process mood
                    mood = []
                    mood_value = row.get('mood')
                    if mood_value is not None and pd.notna(mood_value):
                        mood = [m.strip() for m in str(mood_value).split('|') if m.strip()]
                    
                    # Create movie object
                    movie = {
                        'title': title,
                        'year': year or 2000,
                        'genres': genres,
                        'actors': actors,
                        'directors': directors,
                        'mood': mood,
                        'plot': f"A {', '.join(genres).lower()} movie" if genres else "A great movie"
                    }
                    
                    self.movies.append(movie)
                    
                except Exception as e:
                    continue
            
            print(f"Loaded {len(self.movies)} movies from main_data_updated.csv")
            
        except Exception as e:
            print(f"Error loading movie database: {str(e)}")
            self.movies = []
    
    def record_audio(self, duration=6):
        """Record audio from microphone"""
        try:
            print(f"\n🎤 LISTENING NOW! Speak for up to {duration} seconds...")
            print("💡 Example: 'Hey Movie Buddy, I want a funny action movie'")
            audio = sd.rec(int(duration * self.sample_rate), 
                          samplerate=self.sample_rate, 
                          channels=self.channels)
            sd.wait()
            print("✅ Recording finished. Processing...")
            return audio.flatten()
        except Exception as e:
            print(f"Error recording audio: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio using Deepgram API"""
        try:
            # Convert audio to bytes
            audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
            
            # Make request to Deepgram
            headers = {
                'Authorization': f'Token {DEEPGRAM_API_KEY}',
                'Content-Type': 'audio/wav'
            }
            
            params = {
                'model': 'nova-2',
                'language': 'en-US',
                'smart_format': 'true'
            }
            
            response = requests.post(
                'https://api.deepgram.com/v1/listen',
                headers=headers,
                params=params,
                data=audio_bytes,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['results']['channels'][0]['alternatives']:
                    transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                    return transcript.strip()
            
            return None
            
        except Exception as e:
            print(f"Error transcribing audio: {str(e)}")
            return None
    
    def speak_text(self, text):
        """Convert text to speech and play it"""
        try:
            self.is_speaking = True
            print(f"🔊 Speaking: {text}")
            
            # Create TTS audio
            tts = gTTS(text=text, lang='en', slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tts.save(tmp_file.name)
                
                # Play audio
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clean up
                os.unlink(tmp_file.name)
                
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
        finally:
            self.is_speaking = False
    
    def process_user_input(self, user_input):
        """Process user input and generate appropriate response"""
        if not user_input:
            return
            
        user_input = user_input.lower().strip()
        print(f"🗣️  User said: {user_input}")
        
        # Update last activity
        self.last_activity = time.time()
        
        # Check for wake words
        if not self.is_awake:
            if any(wake_word in user_input for wake_word in self.wake_words):
                self.is_awake = True
                self.speak_text("Hi! I'm MovieBuddy AI. I'm ready to help you find the perfect movie. What kind of movie are you in the mood for?")
                return
            else:
                return  # Ignore input when not awake
        
        # Check for exit words
        if any(exit_word in user_input for exit_word in self.exit_words):
            self.speak_text("Thanks for chatting with me! Enjoy your movies!")
            self.conversation_active = False
            return
        
        # Process movie recommendation request
        try:
            self.is_processing = True
            preferences = self.extract_preferences(user_input)
            recommendations = self.recommend_movies(preferences)
            
            if recommendations:
                response = self.format_recommendations_for_speech(recommendations, preferences)
            else:
                response = "I'm sorry, I couldn't find any movies matching your preferences. Could you try describing what you're in the mood for differently?"
            
            self.speak_text(response)
            
        except Exception as e:
            print(f"Error processing user input: {str(e)}")
            self.speak_text("I'm sorry, I had trouble processing that. Could you try again?")
        finally:
            self.is_processing = False
    
    def extract_preferences(self, user_input):
        """Extract movie preferences from user input"""
        preferences = {
            'genres': [],
            'moods': [],
            'actors': [],
            'directors': [],
            'year_range': None
        }
        
        # Check for genres
        for genre in self.genres:
            if genre.lower() in user_input.lower():
                preferences['genres'].append(genre)
        
        # Check for moods
        for mood in self.moods:
            if mood.lower() in user_input.lower():
                preferences['moods'].append(mood)
        
        # Check for actors (sample search through our database)
        for movie in self.movies[:100]:  # Sample check
            for actor in movie.get('actors', []):
                if actor.lower() in user_input.lower():
                    preferences['actors'].append(actor)
                    break
        
        return preferences
    
    def recommend_movies(self, preferences, n_recommendations=3):
        """Recommend movies based on preferences"""
        scored_movies = []
        
        for movie in self.movies:
            score = 0
            
            # Score based on genres
            for genre in preferences.get('genres', []):
                if genre.lower() in [g.lower() for g in movie.get('genres', [])]:
                    score += 3
            
            # Score based on moods
            for mood in preferences.get('moods', []):
                if mood.lower() in [m.lower() for m in movie.get('mood', [])]:
                    score += 2
            
            # Score based on actors
            for actor in preferences.get('actors', []):
                if actor.lower() in [a.lower() for a in movie.get('actors', [])]:
                    score += 4
            
            if score > 0:
                scored_movies.append((score, movie))
        
        # Sort by score and return top recommendations
        scored_movies.sort(key=lambda x: x[0], reverse=True)
        return [movie for score, movie in scored_movies[:n_recommendations]]
    
    def format_recommendations_for_speech(self, recommendations, preferences):
        """Format recommendations for natural speech"""
        if not recommendations:
            return "I couldn't find any movies matching your preferences."
        
        # Start with acknowledgment
        response = ""
        if preferences.get('genres'):
            response += f"Great! I found some {', '.join(preferences['genres'])} movies for you. "
        elif preferences.get('moods'):
            response += f"Perfect! Here are some movies for when you're feeling {', '.join(preferences['moods'])}. "
        else:
            response += "Here are some movies I think you'll enjoy. "
        
        # Add recommendations
        for i, movie in enumerate(recommendations, 1):
            if i == 1:
                response += f"First, I recommend {movie['title']}"
            elif i == len(recommendations):
                response += f" And finally, {movie['title']}"
            else:
                response += f" Next, {movie['title']}"
            
            if movie.get('year'):
                response += f" from {movie['year']}"
            
            if movie.get('genres'):
                response += f", which is a {', '.join(movie['genres'][:2])} movie"
            
            if movie.get('directors'):
                response += f" directed by {movie['directors'][0]}"
            
            response += ". "
        
        response += " Would you like to hear more about any of these, or should I find something different?"
        
        return response
    
    def check_inactivity(self):
        """Check if the system should go to sleep due to inactivity"""
        if self.is_awake and time.time() - self.last_activity > self.sleep_timeout:
            self.is_awake = False
            print("💤 Going to sleep due to inactivity")
    
    def start_conversation(self):
        """Start the real-time conversation loop"""
        try:
            print("🚀 Starting Real-Time Movie Buddy AI...")
            print("🎤 Listening for wake word: 'Hey Movie Buddy'")
            
            # Set conversation as active
            self.conversation_active = True
            
            # Initial greeting
            self.speak_text("Hello! I'm MovieBuddy AI. Say 'Hey Movie Buddy' to wake me up and get movie recommendations!")
            
            # Main conversation loop
            while self.conversation_active:
                try:
                    # Check for inactivity
                    self.check_inactivity()
                    
                    # Record audio
                    audio_data = self.record_audio(self.recording_duration)
                    if audio_data is None:
                        continue
                    
                    # Transcribe audio
                    transcript = self.transcribe_audio(audio_data)
                    if transcript:
                        self.process_user_input(transcript)
                    
                    # Small delay to prevent overwhelming the API
                    time.sleep(0.5)
                    
                except KeyboardInterrupt:
                    print("\n🛑 Shutting down...")
                    break
                except Exception as e:
                    print(f"Error in conversation loop: {str(e)}")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"❌ Error starting conversation: {str(e)}")
        finally:
            self.conversation_active = False
            print("✅ Conversation ended")

def main():
    """Main function to run the real-time voice recommender"""
    recommender = RealTimeVoiceRecommender()
    recommender.start_conversation()

if __name__ == "__main__":
    print("🎬 Real-Time Movie Buddy AI 🎬")
    print("=" * 50)
    print("Features:")
    print("✅ Real-time speech recognition")
    print("✅ Real-time text-to-speech")
    print("✅ Continuous conversation")
    print("✅ Wake word detection")
    print("✅ Natural movie recommendations")
    print("=" * 50)
    print("Say 'Hey Movie Buddy' to start!")
    print("Press Ctrl+C to exit")
    print("=" * 50)
    
    # Run the main function
    main() 