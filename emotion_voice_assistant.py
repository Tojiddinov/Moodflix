import asyncio
import json
import os
import time
import tempfile
import pandas as pd
import sounddevice as sd
import numpy as np
import warnings
import requests
from gtts import gTTS
import pygame
import re
from datetime import datetime

warnings.filterwarnings('ignore')

# Your Deepgram API key
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"

class SimpleEmotionDetector:
    """Simple emotion detection based on audio characteristics"""
    
    def __init__(self):
        """Initialize simple emotion detection"""
        pass
    
    def detect_emotion_from_audio_features(self, audio_data, sample_rate=16000):
        """Detect emotion using simple audio features"""
        try:
            # Convert to numpy array if needed
            if isinstance(audio_data, list):
                audio_data = np.array(audio_data, dtype=np.float32)
            
            # Normalize audio
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            # Calculate basic features
            # 1. Energy/Volume (RMS)
            rms_energy = np.sqrt(np.mean(audio_data**2))
            
            # 2. Zero crossing rate (speech characteristics)
            zero_crossings = np.where(np.diff(np.sign(audio_data)))[0]
            zcr = len(zero_crossings) / len(audio_data)
            
            # 3. Spectral characteristics (basic)
            # Use FFT to get frequency content
            fft = np.fft.fft(audio_data)
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            magnitude = np.abs(fft)
            
            # Find dominant frequency (simple pitch estimation)
            positive_freqs = freqs[:len(freqs)//2]
            positive_magnitude = magnitude[:len(magnitude)//2]
            
            if len(positive_magnitude) > 0:
                dominant_freq_idx = np.argmax(positive_magnitude)
                dominant_freq = positive_freqs[dominant_freq_idx]
            else:
                dominant_freq = 100  # Default
            
            # 4. Spectral centroid (brightness)
            spectral_centroid = np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude) if np.sum(positive_magnitude) > 0 else 1000
            
            # Emotion classification based on features
            emotion_scores = {
                'neutral': 0.5,
                'happy': 0.0,
                'sad': 0.0,
                'excited': 0.0,
                'calm': 0.0,
                'tired': 0.0,
                'angry': 0.0
            }
            
            # High energy, high pitch = excited/happy
            if rms_energy > 0.05 and dominant_freq > 200:
                emotion_scores['excited'] += 0.4
                emotion_scores['happy'] += 0.3
            
            # Low energy, low pitch = sad/tired
            elif rms_energy < 0.02 and dominant_freq < 150:
                emotion_scores['sad'] += 0.3
                emotion_scores['tired'] += 0.3
            
            # High energy, low pitch = angry
            elif rms_energy > 0.06 and dominant_freq < 180:
                emotion_scores['angry'] += 0.4
            
            # Medium energy, medium pitch = calm
            elif 0.02 <= rms_energy <= 0.04 and 150 <= dominant_freq <= 200:
                emotion_scores['calm'] += 0.4
            
            # High spectral centroid = bright/happy sound
            if spectral_centroid > 2500:
                emotion_scores['happy'] += 0.2
                emotion_scores['excited'] += 0.1
            
            # Low spectral centroid = dull/sad sound
            elif spectral_centroid < 1500:
                emotion_scores['sad'] += 0.2
                emotion_scores['tired'] += 0.1
            
            # High zero crossing rate = clear speech (confident)
            if zcr > 0.1:
                emotion_scores['happy'] += 0.1
                emotion_scores['excited'] += 0.1
            
            # Find emotion with highest score
            detected_emotion = max(emotion_scores, key=emotion_scores.get)
            confidence = emotion_scores[detected_emotion]
            
            # If confidence is too low, return neutral
            if confidence < 0.3:
                return 'neutral', 0.5
            
            return detected_emotion, confidence
            
        except Exception as e:
            print(f"Error in emotion detection: {str(e)}")
            return 'neutral', 0.5

class EnhancedVoiceRecommender:
    def __init__(self):
        """Initialize the enhanced voice movie recommender with emotion detection"""
        self.movies = []
        self.conversation_active = False
        self.is_speaking = False
        self.conversation_history = []
        
        # Initialize emotion detector
        self.emotion_detector = SimpleEmotionDetector()
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
        
        # Emotion to mood mapping for better recommendations
        self.emotion_to_mood = {
            'sad': ['uplifting', 'hopeful', 'funny', 'romantic'],
            'happy': ['funny', 'adventurous', 'romantic', 'uplifting'],
            'angry': ['calm', 'relaxed', 'thoughtful', 'peaceful'],
            'calm': ['thoughtful', 'mysterious', 'romantic', 'peaceful'],
            'excited': ['adventurous', 'funny', 'thrilling', 'action'],
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
        """Load movie data from CSV file with enhanced information"""
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
                    
                    # Process genres with safety checks
                    genres = []
                    genres_value = row.get('genres')
                    if genres_value is not None and pd.notna(genres_value) and str(genres_value) != 'nan':
                        genres = [g.strip() for g in str(genres_value).split('|') if g.strip()]
                    
                    # Process actors with safety checks
                    actors = []
                    for i in range(1, 4):
                        actor = row.get(f'actor_{i}_name', '')
                        if actor is not None and pd.notna(actor) and str(actor).strip() and str(actor) != 'nan':
                            actors.append(str(actor).strip())
                    
                    # Process director with safety checks
                    director = row.get('director_name', '')
                    directors = []
                    if director is not None and pd.notna(director) and str(director).strip() and str(director) != 'nan':
                        directors = [str(director).strip()]
                    
                    # Process mood with safety checks
                    mood = []
                    mood_value = row.get('mood')
                    if mood_value is not None and pd.notna(mood_value) and str(mood_value) != 'nan':
                        mood = [m.strip() for m in str(mood_value).split('|') if m.strip()]
                    
                    # Get additional details with safety checks
                    try:
                        imdb_score = float(row.get('imdb_score', 0)) if pd.notna(row.get('imdb_score')) else 0
                    except:
                        imdb_score = 0
                    
                    try:
                        duration = int(row.get('duration', 0)) if pd.notna(row.get('duration')) else 0
                    except:
                        duration = 0
                    
                    content_rating = str(row.get('content_rating', '')) if pd.notna(row.get('content_rating')) else ''
                    plot_keywords = str(row.get('plot_keywords', '')) if pd.notna(row.get('plot_keywords')) else ''
                    
                    # Create movie object
                    movie = {
                        'title': title,
                        'year': year or 2000,
                        'genres': genres,
                        'actors': actors,
                        'directors': directors,
                        'mood': mood,
                        'imdb_score': imdb_score,
                        'duration': duration,
                        'content_rating': content_rating,
                        'plot_keywords': plot_keywords,
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
        return temp_filename, recording.flatten()
    
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
    
    def analyze_emotion_from_audio(self, audio_data):
        """Analyze emotion from audio data"""
        try:
            print("🧠 Analyzing voice emotion...")
            emotion, confidence = self.emotion_detector.detect_emotion_from_audio_features(audio_data, self.sample_rate)
            
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
                score += 3
            elif movie.get('imdb_score', 0) > 6:
                score += 2
            elif movie.get('imdb_score', 0) > 5:
                score += 1
            
            # Score based on genres
            for genre in preferences.get('genres', []):
                if genre.lower() in [g.lower() for g in movie.get('genres', [])]:
                    score += 4
            
            # Score based on moods (including emotion-derived moods)
            for mood in preferences.get('moods', []):
                if mood.lower() in [m.lower() for m in movie.get('mood', [])]:
                    score += 3
                # Also check genres that match moods
                mood_genre_map = {
                    'funny': 'comedy', 'adventurous': 'adventure', 
                    'uplifting': 'drama', 'thrilling': 'thriller',
                    'action': 'action', 'romantic': 'romance'
                }
                if mood in mood_genre_map:
                    if mood_genre_map[mood].lower() in [g.lower() for g in movie.get('genres', [])]:
                        score += 3
            
            # Emotional state bonus
            emotion = preferences.get('emotion', 'neutral')
            if emotion == 'sad' and any(g.lower() in ['comedy', 'romance', 'family'] for g in movie.get('genres', [])):
                score += 4  # Boost feel-good movies for sad users
            elif emotion == 'excited' and any(g.lower() in ['action', 'adventure', 'thriller'] for g in movie.get('genres', [])):
                score += 4  # Boost exciting movies for excited users
            elif emotion == 'calm' and any(g.lower() in ['drama', 'romance', 'documentary'] for g in movie.get('genres', [])):
                score += 3  # Boost peaceful movies for calm users
            elif emotion == 'tired' and any(g.lower() in ['comedy', 'family', 'animation'] for g in movie.get('genres', [])):
                score += 3  # Boost easy-watching movies for tired users
            
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
            'sad': "I can sense you might be feeling a bit down. Let me recommend some uplifting movies that could brighten your day. ",
            'happy': "You sound so cheerful! I have some fantastic movies that will match your positive energy. ",
            'excited': "I can hear the excitement in your voice! Here are some thrilling movies perfect for your energetic mood. ",
            'tired': "You sound like you could use some relaxation. Let me suggest some comforting, easy-to-watch movies. ",
            'calm': "You seem very peaceful right now. Here are some thoughtful movies that complement your calm state. ",
            'angry': "I understand you might be feeling frustrated. These movies might help you unwind and feel better. ",
            'neutral': "Here are some excellent movie recommendations carefully selected for you. "
        }
        
        response = emotion_responses.get(emotion, emotion_responses['neutral'])
        
        # Add genre/mood acknowledgment
        if preferences.get('genres'):
            response += f"I found some wonderful {', '.join(preferences['genres'])} movies. "
        
        # Add detailed recommendations
        for i, movie in enumerate(recommendations, 1):
            if i == 1:
                response += f"First, I highly recommend '{movie['title']}'"
            elif i == len(recommendations):
                response += f" And finally, '{movie['title']}'"
            else:
                response += f" Next, '{movie['title']}'"
            
            # Add year and rating
            if movie.get('year'):
                response += f" from {movie['year']}"
            
            if movie.get('imdb_score', 0) > 0:
                response += f", with an IMDB rating of {movie['imdb_score']:.1f}"
            
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
            response += " I hope these movies bring some joy and comfort to your day. Would you like more uplifting recommendations?"
        elif emotion == 'excited':
            response += " These should keep your energy up and give you an amazing experience! Want more action-packed suggestions?"
        elif emotion == 'tired':
            response += " These are perfect for a cozy, relaxing evening. Need any lighter recommendations?"
        else:
            response += " Would you like to hear more detailed information about any of these movies, or should I find something different?"
        
        return response
    
    def process_user_input(self, user_input, audio_data):
        """Process user input and generate appropriate response"""
        if not user_input:
            return
        
        user_input = user_input.lower().strip()
        print(f"📝 Processing: {user_input}")
        
        # Analyze emotion from voice
        self.analyze_emotion_from_audio(audio_data)
        
        # Update last activity
        self.last_activity = time.time()
        
        # Check for wake words
        if not self.is_awake:
            if any(wake_word in user_input for wake_word in self.wake_words):
                self.is_awake = True
                emotion_greetings = {
                    'sad': "Hi there! I'm MovieBuddy AI with emotion detection, and I'm here to help brighten your day with some wonderful movies. What can I recommend for you?",
                    'happy': "Hello! I'm MovieBuddy AI, and I absolutely love your positive energy! What kind of movie would make your day even more amazing?",
                    'excited': "Hey! I'm MovieBuddy AI, and I can feel your excitement! What thrilling movies can I find for you today?",
                    'tired': "Hi! I'm MovieBuddy AI. You sound like you could use some relaxation. What kind of comfortable, easy-watching movie would you enjoy?",
                    'calm': "Hello! I'm MovieBuddy AI. I appreciate your peaceful energy. What thoughtful movie can I recommend for you?",
                    'angry': "Hi! I'm MovieBuddy AI. I sense some tension in your voice. Let me help you find a movie that might help you unwind and feel better.",
                    'neutral': "Hi! I'm MovieBuddy AI with advanced emotion detection. I'm ready to help you find the perfect movie based on your mood. What are you looking for?"
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
                'sad': "Take care of yourself, and I truly hope these movie recommendations help lift your spirits. Remember, better days are ahead. Enjoy your viewing!",
                'happy': "It was absolutely wonderful chatting with someone so cheerful and positive! Have an amazing time with your movies!",
                'excited': "What an incredibly energetic and fun conversation! I hope you have a thrilling time with your movies!",
                'tired': "Rest well and enjoy some peaceful movie time. I hope you get the relaxation you need. Sweet dreams!",
                'calm': "Thank you for such a peaceful conversation. Enjoy your thoughtful movie time and stay zen!",
                'angry': "I hope our chat helped calm you down a bit. Enjoy these movies and take care of yourself!",
                'neutral': "Thanks for chatting with me! I hope you enjoy the movie recommendations. Happy watching!"
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
                empathetic_no_results = {
                    'sad': "I'm sorry I couldn't find specific matches, but don't worry! Let me recommend some universally uplifting movies that might cheer you up.",
                    'excited': "Hmm, let me find something that matches your amazing energy! How about some high-energy action movies?",
                    'tired': "No worries! Let me suggest some gentle, easy-to-follow movies perfect for when you're feeling low-energy.",
                    'neutral': "I couldn't find exact matches, but let me recommend some popular, well-loved movies instead."
                }
                response = empathetic_no_results.get(self.user_emotion, empathetic_no_results['neutral'])
            
            self.speak_text(response)
            
        except Exception as e:
            print(f"Error processing user input: {str(e)}")
            response = "I'm sorry, I had trouble processing that. Could you try again? I'm here to help!"
            self.speak_text(response)
    
    def start_conversation(self):
        """Start the enhanced conversation loop"""
        try:
            print("🚀 Starting Enhanced Movie Buddy AI with Emotion Detection...")
            print("🎬 MovieBuddy AI - Emotion-Aware Movie Recommender 🎬")
            print("=" * 70)
            print("🌟 Advanced Features:")
            print("✅ Real-time speech recognition (6-second windows)")
            print("✅ Voice emotion detection and analysis")
            print("✅ Empathetic responses based on your mood")
            print("✅ Detailed movie information with ratings, cast, and duration")
            print("✅ Personalized recommendations based on emotional state")
            print("✅ Natural conversation flow")
            print("✅ Wake word detection ('Hey Movie Buddy')")
            print("=" * 70)
            print("💡 TIP: Speak naturally - I can detect emotions from your voice tone!")
            print("🗣️  Say 'Hey Movie Buddy' to start!")
            print("⏹️  Press Ctrl+C to exit")
            print("=" * 70)
            
            # Set conversation as active
            self.conversation_active = True
            
            # Initial greeting
            greeting = "Hello! I'm MovieBuddy AI with advanced emotion detection. I can understand your mood from your voice and recommend perfect movies for exactly how you're feeling right now. Say 'Hey Movie Buddy' to wake me up!"
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
                        audio_file, audio_data = self.record_audio(self.recording_duration)
                        transcript = self.transcribe_audio(audio_file)
                        
                        if transcript and transcript.strip():
                            print(f"🗣️  You said: {transcript}")
                            self.process_user_input(transcript, audio_data)
                        else:
                            print("🔇 No speech detected")
                        
                        # Clean up audio file
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
    """Main function to run the enhanced emotion-aware voice recommender"""
    print("🎬 Enhanced MovieBuddy AI with Emotion Detection 🎬")
    print("Initializing emotion detection and movie database...")
    
    recommender = EnhancedVoiceRecommender()
    recommender.start_conversation()

if __name__ == "__main__":
    main() 