#!/usr/bin/env python3
"""
Simple Real-Time Voice Movie Recommender
Using Deepgram for STT and TTS with continuous conversation
"""

import asyncio
import json
import os
import time
import re
import pandas as pd
import sounddevice as sd
import numpy as np
import warnings
import websockets
from gtts import gTTS
import pygame
import tempfile
import requests
import threading
import queue
from pathlib import Path
import librosa
from scipy.stats import skew, kurtosis

warnings.filterwarnings('ignore')

# Your Deepgram API key
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"

class EmotionDetector:
    """Detect emotions from voice audio features"""
    
    def __init__(self):
        """Initialize emotion detection parameters"""
        self.emotion_thresholds = {
            'sad': {'pitch_mean': 150, 'energy_mean': 0.01, 'spectral_centroid': 2000},
            'happy': {'pitch_mean': 200, 'energy_mean': 0.05, 'spectral_centroid': 3000},
            'angry': {'pitch_mean': 180, 'energy_mean': 0.08, 'spectral_centroid': 3500},
            'calm': {'pitch_mean': 160, 'energy_mean': 0.02, 'spectral_centroid': 2200},
            'excited': {'pitch_mean': 220, 'energy_mean': 0.06, 'spectral_centroid': 3200},
            'tired': {'pitch_mean': 140, 'energy_mean': 0.015, 'spectral_centroid': 1800}
        }
    
    def extract_audio_features(self, audio_file):
        """Extract audio features for emotion detection"""
        try:
            # Load audio file
            y, sr = librosa.load(audio_file, sr=16000)
            
            if len(y) == 0:
                return None
            
            # Extract features
            features = {}
            
            # Pitch (fundamental frequency)
            pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
            pitch_values = []
            for t in range(pitches.shape[1]):
                index = magnitudes[:, t].argmax()
                pitch = pitches[index, t]
                if pitch > 0:
                    pitch_values.append(pitch)
            
            features['pitch_mean'] = np.mean(pitch_values) if pitch_values else 0
            features['pitch_std'] = np.std(pitch_values) if pitch_values else 0
            
            # Energy/RMS
            rms = librosa.feature.rms(y=y)[0]
            features['energy_mean'] = np.mean(rms)
            features['energy_std'] = np.std(rms)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            features['spectral_centroid'] = np.mean(spectral_centroids)
            
            # MFCC (Mel-frequency cepstral coefficients)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features['mfcc_mean'] = np.mean(mfccs)
            features['mfcc_std'] = np.std(mfccs)
            
            # Zero crossing rate
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            features['zcr_mean'] = np.mean(zcr)
            
            return features
            
        except Exception as e:
            print(f"Error extracting audio features: {str(e)}")
            return None
    
    def detect_emotion(self, audio_file):
        """Detect emotion from audio file"""
        features = self.extract_audio_features(audio_file)
        
        if not features:
            return 'neutral', 0.5
        
        # Score each emotion based on audio features
        emotion_scores = {}
        
        for emotion, thresholds in self.emotion_thresholds.items():
            score = 0
            total_features = len(thresholds)
            
            # Compare pitch
            if 'pitch_mean' in thresholds:
                pitch_diff = abs(features['pitch_mean'] - thresholds['pitch_mean'])
                pitch_score = max(0, 1 - (pitch_diff / 100))  # Normalize
                score += pitch_score
            
            # Compare energy
            if 'energy_mean' in thresholds:
                energy_diff = abs(features['energy_mean'] - thresholds['energy_mean'])
                energy_score = max(0, 1 - (energy_diff / 0.05))  # Normalize
                score += energy_score
            
            # Compare spectral centroid
            if 'spectral_centroid' in thresholds:
                spectral_diff = abs(features['spectral_centroid'] - thresholds['spectral_centroid'])
                spectral_score = max(0, 1 - (spectral_diff / 1000))  # Normalize
                score += spectral_score
            
            emotion_scores[emotion] = score / total_features
        
        # Find the emotion with highest score
        detected_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[detected_emotion]
        
        # If confidence is too low, return neutral
        if confidence < 0.3:
            return 'neutral', confidence
        
        return detected_emotion, confidence

class SimpleRealTimeVoiceRecommender:
    def __init__(self):
        """Initialize the simple real-time voice movie recommender"""
        self.movies = []
        self.conversation_active = False
        self.is_listening = False
        self.is_speaking = False
        self.conversation_history = []
        
        # Initialize emotion detector
        self.emotion_detector = EmotionDetector()
        self.user_emotion = 'neutral'
        self.emotion_confidence = 0.5
        
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
        
        # Emotion to mood mapping
        self.emotion_to_mood = {
            'sad': ['uplifting', 'hopeful', 'emotional', 'romantic'],
            'happy': ['funny', 'adventurous', 'romantic', 'uplifting'],
            'angry': ['calm', 'relaxed', 'thoughtful', 'inspirational'],
            'calm': ['thoughtful', 'mysterious', 'romantic', 'peaceful'],
            'excited': ['adventurous', 'funny', 'action-packed', 'thrilling'],
            'tired': ['calm', 'relaxed', 'comfort', 'easy-watching'],
            'neutral': ['popular', 'well-reviewed', 'balanced']
        }
        
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
                        if pd.notna(actor) and str(actor).strip():
                            actors.append(str(actor).strip())
                    
                    # Process director
                    director = row.get('director_name', '')
                    directors = [str(director).strip()] if pd.notna(director) and str(director).strip() else []
                    
                    # Process mood
                    mood = []
                    if pd.notna(row.get('mood')):
                        mood = [m.strip() for m in str(row.get('mood')).split('|') if m.strip()]
                    
                    # Get additional details
                    imdb_score = row.get('imdb_score', 0)
                    duration = row.get('duration', 0)
                    content_rating = row.get('content_rating', '')
                    plot_keywords = row.get('plot_keywords', '')
                    
                    # Create movie object
                    movie = {
                        'title': title,
                        'year': year or 2000,
                        'genres': genres,
                        'actors': actors,
                        'directors': directors,
                        'mood': mood,
                        'imdb_score': float(imdb_score) if pd.notna(imdb_score) else 0,
                        'duration': int(duration) if pd.notna(duration) else 0,
                        'content_rating': str(content_rating) if pd.notna(content_rating) else '',
                        'plot_keywords': str(plot_keywords) if pd.notna(plot_keywords) else '',
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
        print(f"\n🎤 LISTENING NOW! Speak for up to {duration} seconds...")
        print("💡 Example: 'Hey Movie Buddy, I want a funny action movie'")
        
        # Record audio
        recording = sd.rec(int(duration * self.sample_rate), 
                          samplerate=self.sample_rate, 
                          channels=self.channels, 
                          dtype=np.int16)
        sd.wait()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_filename = temp_file.name
            
            # Convert to WAV format
            import wave
            with wave.open(temp_filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(recording.tobytes())
        
        print("✅ Recording finished. Processing...")
        return temp_filename
    
    def transcribe_audio(self, file_path):
        """Transcribe audio using Deepgram API"""
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
                return None
            
            data = response.json()
            transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
            
            return transcript
            
        except Exception as e:
            print(f"Error during transcription: {str(e)}")
            return None
    
    def analyze_emotion_from_audio(self, audio_file):
        """Analyze emotion from audio file"""
        try:
            print("🧠 Analyzing voice emotion...")
            emotion, confidence = self.emotion_detector.detect_emotion(audio_file)
            
            self.user_emotion = emotion
            self.emotion_confidence = confidence
            
            # Emotional feedback
            emotion_emoji = {
                'sad': '😢', 'happy': '😊', 'angry': '😠', 
                'calm': '😌', 'excited': '🤗', 'tired': '😴', 'neutral': '😐'
            }
            
            emoji = emotion_emoji.get(emotion, '😐')
            print(f"💝 Detected emotion: {emotion} {emoji} (confidence: {confidence:.2f})")
            
            return emotion, confidence
            
        except Exception as e:
            print(f"Error analyzing emotion: {str(e)}")
            return 'neutral', 0.5
    
    def speak_text(self, text):
        """Convert text to speech and play it"""
        if not text:
            return
        
        try:
            self.is_speaking = True
            print(f"🔊 Speaking: {text}")
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
            
            # Generate speech using gTTS
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.music.unload()
            os.unlink(temp_filename)
            
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")
        finally:
            self.is_speaking = False
    
    def extract_preferences(self, user_input):
        """Extract movie preferences from user input"""
        preferences = {
            'genres': [],
            'moods': [],
            'actors': [],
            'directors': [],
            'emotion': self.user_emotion
        }
        
        user_input_lower = user_input.lower()
        
        # Check for genres
        for genre in self.genres:
            if genre.lower() in user_input_lower:
                preferences['genres'].append(genre)
        
        # Check for moods
        for mood in self.moods:
            if mood.lower() in user_input_lower:
                preferences['moods'].append(mood)
        
        # Add emotion-based moods if no explicit mood requested
        if not preferences['moods'] and self.user_emotion in self.emotion_to_mood:
            preferences['moods'].extend(self.emotion_to_mood[self.user_emotion])
        
        return preferences
    
    def recommend_movies(self, preferences, n_recommendations=3):
        """Recommend movies based on preferences and emotional state"""
        scored_movies = []
        
        for movie in self.movies:
            score = 0
            
            # Base score for movie quality
            if movie.get('imdb_score', 0) > 7:
                score += 2
            elif movie.get('imdb_score', 0) > 6:
                score += 1
            
            # Score based on genres
            for genre in preferences.get('genres', []):
                if genre.lower() in [g.lower() for g in movie.get('genres', [])]:
                    score += 3
            
            # Score based on moods (including emotion-derived moods)
            for mood in preferences.get('moods', []):
                if mood.lower() in [m.lower() for m in movie.get('mood', [])]:
                    score += 2
                # Also check genres that match moods
                mood_genre_map = {
                    'funny': 'comedy', 'adventurous': 'adventure', 
                    'uplifting': 'drama', 'thrilling': 'thriller'
                }
                if mood in mood_genre_map:
                    if mood_genre_map[mood].lower() in [g.lower() for g in movie.get('genres', [])]:
                        score += 2
            
            # Emotional state bonus
            emotion = preferences.get('emotion', 'neutral')
            if emotion == 'sad' and any(g.lower() in ['comedy', 'romance', 'family'] for g in movie.get('genres', [])):
                score += 3  # Boost feel-good movies for sad users
            elif emotion == 'excited' and any(g.lower() in ['action', 'adventure', 'thriller'] for g in movie.get('genres', [])):
                score += 3  # Boost exciting movies for excited users
            elif emotion == 'calm' and any(g.lower() in ['drama', 'romance', 'documentary'] for g in movie.get('genres', [])):
                score += 2  # Boost peaceful movies for calm users
            
            # Basic scoring for movies without specific matches
            if score == 0 and movie.get('genres'):
                score = 1
            
            if score > 0:
                scored_movies.append((score, movie))
        
        # Sort by score and return top recommendations
        scored_movies.sort(key=lambda x: x[0], reverse=True)
        return [movie for score, movie in scored_movies[:n_recommendations]]
    
    def format_recommendations_for_speech(self, recommendations, preferences):
        """Format recommendations for natural speech with detailed information"""
        if not recommendations:
            return "I'm sorry, I couldn't find any movies matching your preferences. Could you try describing what you're in the mood for differently?"
        
        # Empathetic opening based on detected emotion
        emotion = preferences.get('emotion', 'neutral')
        emotion_responses = {
            'sad': "I sense you might be feeling a bit down. Let me recommend some movies that might lift your spirits. ",
            'happy': "You sound cheerful! Here are some great movies to match your positive energy. ",
            'excited': "I can hear the excitement in your voice! Here are some thrilling movies for you. ",
            'tired': "You sound tired. Let me suggest some relaxing movies that won't require too much energy. ",
            'calm': "You seem peaceful. Here are some thoughtful movies that match your calm mood. ",
            'angry': "I understand you might be feeling frustrated. Here are some movies that might help you unwind. ",
            'neutral': "Here are some excellent movie recommendations for you. "
        }
        
        response = emotion_responses.get(emotion, emotion_responses['neutral'])
        
        # Add genre/mood acknowledgment
        if preferences.get('genres'):
            response += f"I found some wonderful {', '.join(preferences['genres'])} movies. "
        
        # Add detailed recommendations
        for i, movie in enumerate(recommendations, 1):
            if i == 1:
                response += f"First, I highly recommend {movie['title']}"
            elif i == len(recommendations):
                response += f" And finally, {movie['title']}"
            else:
                response += f" Next, {movie['title']}"
            
            # Add year and rating
            if movie.get('year'):
                response += f" from {movie['year']}"
            
            if movie.get('imdb_score', 0) > 0:
                response += f", rated {movie['imdb_score']:.1f} on IMDB"
            
            # Add genre information
            if movie.get('genres'):
                response += f". This is a {', '.join(movie['genres'][:2])} movie"
            
            # Add duration if available
            if movie.get('duration', 0) > 0:
                hours = movie['duration'] // 60
                minutes = movie['duration'] % 60
                if hours > 0:
                    response += f" running {hours} hours"
                    if minutes > 0:
                        response += f" and {minutes} minutes"
                else:
                    response += f" running {minutes} minutes"
            
            # Add director info
            if movie.get('directors'):
                response += f", directed by {movie['directors'][0]}"
            
            # Add main actors
            if movie.get('actors'):
                actors_str = ', '.join(movie['actors'][:2])
                response += f", starring {actors_str}"
            
            response += ". "
        
        # Add empathetic closing based on emotion
        if emotion == 'sad':
            response += " I hope these movies bring some joy to your day. Would you like more uplifting recommendations?"
        elif emotion == 'excited':
            response += " These should keep your energy up! Want more action-packed suggestions?"
        elif emotion == 'tired':
            response += " These are perfect for a relaxing evening. Need any lighter recommendations?"
        else:
            response += " Would you like to hear more about any of these, or should I find something different?"
        
        return response
    
    def process_user_input(self, user_input, audio_file):
        """Process user input and generate appropriate response"""
        if not user_input:
            return
        
        user_input = user_input.lower().strip()
        print(f"📝 Processing: {user_input}")
        
        # Analyze emotion from voice
        self.analyze_emotion_from_audio(audio_file)
        
        # Clean up audio file
        if os.path.exists(audio_file):
            os.unlink(audio_file)
        
        # Update last activity
        self.last_activity = time.time()
        
        # Check for wake words
        if not self.is_awake:
            if any(wake_word in user_input for wake_word in self.wake_words):
                self.is_awake = True
                emotion_greetings = {
                    'sad': "Hi there! I'm MovieBuddy AI, and I'm here to help brighten your day with some great movies. What can I recommend for you?",
                    'happy': "Hello! I'm MovieBuddy AI, and I love your positive energy! What kind of movie would make your day even better?",
                    'excited': "Hey! I'm MovieBuddy AI, and I can feel your excitement! What thrilling movies can I find for you?",
                    'tired': "Hi! I'm MovieBuddy AI. You sound like you could use some relaxation. What kind of easy-watching movie would you enjoy?",
                    'neutral': "Hi! I'm MovieBuddy AI. I'm ready to help you find the perfect movie. What are you in the mood for?"
                }
                response = emotion_greetings.get(self.user_emotion, emotion_greetings['neutral'])
                self.speak_text(response)
                return
            else:
                print("💤 Not awake - ignoring input")
                return
        
        # Check for exit words
        if any(exit_word in user_input for exit_word in self.exit_words):
            emotion_goodbyes = {
                'sad': "Take care, and I hope these movies help brighten your mood. Enjoy your viewing!",
                'happy': "It was wonderful chatting with someone so cheerful! Enjoy your movies!",
                'excited': "What an energetic conversation! Have an amazing time with your movies!",
                'tired': "Rest well and enjoy some relaxing movie time. Sweet dreams!",
                'neutral': "Thanks for chatting with me! Enjoy your movies!"
            }
            response = emotion_goodbyes.get(self.user_emotion, emotion_goodbyes['neutral'])
            self.speak_text(response)
            self.conversation_active = False
            return
        
        # Process movie recommendation request
        try:
            preferences = self.extract_preferences(user_input)
            recommendations = self.recommend_movies(preferences)
            
            if recommendations:
                response = self.format_recommendations_for_speech(recommendations, preferences)
            else:
                response = "I'm sorry, I couldn't find any movies matching your preferences. Could you try describing what you're in the mood for differently?"
            
            self.speak_text(response)
            
        except Exception as e:
            print(f"Error processing user input: {str(e)}")
            response = "I'm sorry, I had trouble processing that. Could you try again?"
            self.speak_text(response)
    
    def start_conversation(self):
        """Start the real-time conversation loop"""
        try:
            print("🚀 Starting Enhanced Real-Time Movie Buddy AI...")
            print("🎬 Real-Time Movie Buddy AI with Emotion Detection 🎬")
            print("=" * 60)
            print("Features:")
            print("✅ Real-time speech recognition (6-second windows)")
            print("✅ Voice emotion detection and empathetic responses")
            print("✅ Detailed movie information and recommendations")
            print("✅ Natural voice responses")
            print("✅ Continuous conversation")
            print("✅ Wake word detection")
            print("✅ Smart movie recommendations based on your mood")
            print("=" * 60)
            print("💡 TIP: You have 6 seconds to speak each time")
            print("🗣️  Say 'Hey Movie Buddy' to start!")
            print("⏹️  Press Ctrl+C to exit")
            print("=" * 60)
            
            # Set conversation as active
            self.conversation_active = True
            
            # Initial greeting
            greeting = "Hello! I'm MovieBuddy AI with emotion detection. I can understand your mood from your voice and recommend perfect movies for how you're feeling. Say 'Hey Movie Buddy' to wake me up!"
            self.speak_text(greeting)
            
            # Main conversation loop
            while self.conversation_active:
                # Check for sleep timeout
                if self.is_awake and time.time() - self.last_activity > self.sleep_timeout:
                    self.is_awake = False
                    print("💤 Going to sleep due to inactivity")
                
                # Record and process audio
                try:
                    if not self.is_speaking:  # Don't record while speaking
                        audio_file = self.record_audio(self.recording_duration)
                        transcript = self.transcribe_audio(audio_file)
                        
                        if transcript and transcript.strip():
                            print(f"🗣️  You said: {transcript}")
                            self.process_user_input(transcript, audio_file)
                        else:
                            print("🔇 No speech detected")
                            # Clean up audio file if no transcript
                            if os.path.exists(audio_file):
                                os.unlink(audio_file)
                    
                    # Short pause between recordings
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error in conversation loop: {str(e)}")
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down...")
        except Exception as e:
            print(f"❌ Error in conversation: {str(e)}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.conversation_active = False
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")

def main():
    """Main function to run the enhanced real-time voice recommender"""
    print("🎬 Enhanced Real-Time Movie Buddy AI with Emotion Detection 🎬")
    print("Initializing emotion detection and movie database...")
    
    recommender = SimpleRealTimeVoiceRecommender()
    recommender.start_conversation()

if __name__ == "__main__":
    main() 