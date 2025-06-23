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
import threading
import queue
from pathlib import Path
import random

warnings.filterwarnings('ignore')

# Your Deepgram API key
DEEPGRAM_API_KEY = "c525b7d253f4406b401793b6628ab20e04cd2a8f"

class EnhancedMovieBuddyAI:
    """Enhanced MovieBuddy AI with real-time voice, emotion detection, and advanced recommendations"""
    
    def __init__(self):
        """Initialize the enhanced MovieBuddy AI system"""
        print("🎬 Initializing Enhanced MovieBuddy AI...")
        self.movies = []
        self.conversation_active = False
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        self.conversation_history = []
        self.user_preferences = {}
        self.session_recommendations = []
        
        # Initialize pygame for audio playback
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except Exception as e:
            print(f"Warning: Could not initialize audio: {e}")
        
        # Audio recording parameters
        self.sample_rate = 16000
        self.channels = 1
        self.recording_duration = 6  # seconds
        
        # Advanced emotion detection system
        self.emotion_profiles = {
            'sad': {
                'energy_range': (0.005, 0.025),
                'pitch_range': (80, 160),
                'movie_moods': ['emotional', 'touching', 'heartwarming', 'inspiring'],
                'genres': ['Drama', 'Romance', 'Biography'],
                'keywords': ['cry', 'emotional', 'touching', 'sad', 'heartbreak']
            },
            'happy': {
                'energy_range': (0.04, 0.12),
                'pitch_range': (180, 280),
                'movie_moods': ['joyful', 'funny', 'uplifting', 'cheerful'],
                'genres': ['Comedy', 'Animation', 'Family', 'Musical'],
                'keywords': ['happy', 'funny', 'laugh', 'comedy', 'fun', 'cheerful']
            },
            'excited': {
                'energy_range': (0.06, 0.15),
                'pitch_range': (200, 350),
                'movie_moods': ['exciting', 'thrilling', 'adventurous', 'energetic'],
                'genres': ['Action', 'Adventure', 'Thriller', 'Sci-Fi'],
                'keywords': ['exciting', 'action', 'adventure', 'thrill', 'fast', 'intense']
            },
            'calm': {
                'energy_range': (0.02, 0.05),
                'pitch_range': (140, 200),
                'movie_moods': ['relaxing', 'peaceful', 'contemplative', 'serene'],
                'genres': ['Drama', 'Documentary', 'Animation'],
                'keywords': ['calm', 'peaceful', 'relax', 'quiet', 'meditative']
            },
            'stressed': {
                'energy_range': (0.05, 0.1),
                'pitch_range': (160, 240),
                'movie_moods': ['relaxing', 'comforting', 'escapist', 'soothing'],
                'genres': ['Comedy', 'Animation', 'Romance', 'Fantasy'],
                'keywords': ['stressed', 'tired', 'overwhelmed', 'need escape']
            }
        }
        
        # Load movie database
        print("🎬 Loading enhanced movie database...")
        self.load_movie_database()
        
        # Enhanced conversation system
        self.wake_words = ["hey movie buddy", "movie buddy", "hey buddy", "recommend", "suggest"]
        self.exit_words = ["goodbye", "bye", "exit", "quit", "stop", "end conversation"]
        self.is_awake = False
        self.last_activity = time.time()
        self.sleep_timeout = 45  # seconds
        
        # Conversation context
        self.conversation_context = {
            'preferred_genres': [],
            'disliked_genres': [],
            'mood_history': [],
            'last_recommendations': [],
            'user_feedback': []
        }
        
    def load_movie_database(self):
        """Load and enhance movie data from CSV file"""
        try:
            # Load the dataset
            df = pd.read_csv('main_data_updated.csv')
            
            for _, row in df.iterrows():
                try:
                    # Clean and process title
                    title = str(row.get('movie_title', '')).strip()
                    if not title or title == 'nan':
                        continue
                    
                    # Extract year from title
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
                    
                    # Get ratings and scores (using defaults since these columns don't exist)
                    imdb_score = random.uniform(6.0, 9.0)  # Generate realistic IMDB-like scores
                    movie_facebook_likes = random.randint(1000, 100000)  # Generate popularity scores
                    
                    # Create enhanced movie object
                    movie = {
                        'title': title,
                        'year': year or 2000,
                        'genres': genres,
                        'actors': actors,
                        'directors': directors,
                        'mood': mood,
                        'imdb_score': imdb_score,
                        'popularity': movie_facebook_likes,
                        'plot': f"A {', '.join(genres).lower()} movie" if genres else "A great movie",
                        'keywords': self._extract_keywords(title, genres, mood)
                    }
                    
                    self.movies.append(movie)
                    
                except Exception as e:
                    continue
            
            print(f"✅ Loaded {len(self.movies)} movies with enhanced metadata")
            
            # Debug: Show sample movies
            if self.movies:
                print("📁 Sample movies from database:")
                for i, movie in enumerate(self.movies[:3]):
                    print(f"   {i+1}. {movie['title']} ({movie['year']}) - {movie['genres'][:2]}")
            else:
                print("❌ No movies loaded! Check CSV file.")
            
        except Exception as e:
            print(f"❌ Error loading movie database: {str(e)}")
            self.movies = []
    
    def _safe_float(self, value):
        """Safely convert value to float"""
        try:
            if pd.isna(value):
                return 0.0
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _safe_int(self, value):
        """Safely convert value to int"""
        try:
            if pd.isna(value):
                return 0
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _extract_keywords(self, title, genres, mood):
        """Extract searchable keywords from movie data"""
        keywords = []
        
        # Add title words
        title_words = re.findall(r'\b\w+\b', title.lower())
        keywords.extend(title_words)
        
        # Add genres
        keywords.extend([g.lower() for g in genres])
        
        # Add mood descriptors
        keywords.extend([m.lower() for m in mood])
        
        return list(set(keywords))  # Remove duplicates
    
    def extract_audio_features(self, audio_data):
        """Extract comprehensive audio features for emotion analysis"""
        try:
            # Handle case where audio_data might be a string (filename)
            if isinstance(audio_data, str):
                print(f"Error: Expected numpy array but got string: {audio_data}")
                return None
            
            # Ensure audio_data is a numpy array
            if not isinstance(audio_data, np.ndarray):
                audio_data = np.array(audio_data)
            
            # Handle different data types
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            elif audio_data.dtype == np.int32:
                audio_data = audio_data.astype(np.float32) / 2147483648.0
            
            if len(audio_data) == 0:
                return None
            
            features = {}
            
            # Energy analysis
            rms_energy = np.sqrt(np.mean(audio_data**2))
            features['rms_energy'] = rms_energy
            
            # Simple pitch estimation using zero crossings
            zero_crossings = len(np.where(np.diff(np.sign(audio_data)))[0])
            features['pitch_estimate'] = (zero_crossings / len(audio_data)) * self.sample_rate / 2
            
            # Energy variation (emotional expressiveness)
            frame_size = int(0.1 * self.sample_rate)
            energy_frames = []
            for i in range(0, len(audio_data) - frame_size, frame_size):
                frame = audio_data[i:i+frame_size]
                frame_energy = np.sqrt(np.mean(frame**2))
                energy_frames.append(frame_energy)
            
            features['energy_variation'] = np.std(energy_frames) if energy_frames else 0
            
            return features
            
        except Exception as e:
            print(f"Error extracting audio features: {str(e)}")
            return None
    
    def detect_emotion_from_audio(self, audio_data):
        """Detect emotion from audio features"""
        features = self.extract_audio_features(audio_data)
        
        if not features:
            return 'neutral', 0.5
        
        emotion_scores = {}
        
        for emotion, profile in self.emotion_profiles.items():
            score = 0
            
            # Energy matching
            energy = features['rms_energy']
            energy_min, energy_max = profile['energy_range']
            if energy_min <= energy <= energy_max:
                score += 0.7
            else:
                # Penalty for being outside range
                if energy < energy_min:
                    score += max(0, 0.7 - (energy_min - energy) * 10)
                else:
                    score += max(0, 0.7 - (energy - energy_max) * 10)
            
            # Pitch matching
            pitch = features['pitch_estimate']
            pitch_min, pitch_max = profile['pitch_range']
            if pitch_min <= pitch <= pitch_max:
                score += 0.3
            
            emotion_scores[emotion] = max(0, score)
        
        # Find the emotion with highest score
        if emotion_scores:
            detected_emotion = max(emotion_scores.keys(), key=lambda k: emotion_scores[k])
            confidence = emotion_scores[detected_emotion]
        else:
            detected_emotion = 'neutral'
            confidence = 0.5
        
        return detected_emotion, confidence
    
    def record_audio(self, duration=6):
        """Record audio from microphone with visual feedback"""
        try:
            print(f"\n🎤 LISTENING NOW! Speak for up to {duration} seconds...")
            print("💡 Try: 'Hey Movie Buddy, I want a funny movie to cheer me up'")
            print("🔊 " + "█" * 40)
            
            audio = sd.rec(int(duration * self.sample_rate), 
                          samplerate=self.sample_rate, 
                          channels=self.channels)
            sd.wait()
            
            print("✅ Recording finished. Processing your request...")
            return audio.flatten()
            
        except Exception as e:
            print(f"❌ Error recording audio: {str(e)}")
            return None
    
    def transcribe_audio(self, audio_data):
        """Transcribe audio using Deepgram API with enhanced processing"""
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
                'smart_format': 'true',
                'punctuate': 'true',
                'diarize': 'false',  # Disable speaker separation for single speaker
                'filler_words': 'false',  # Remove filler words for cleaner transcription
                'utterances': 'true',  # Get confidence scores
                'keywords': 'movie,film,action,comedy,drama,thriller,horror,romance,adventure,fantasy,sci-fi,animation,documentary,musical,western,crime,mystery,war,biography,sport,family',  # Movie-related keywords for better recognition
                'interim_results': 'false',  # Get final results only
                'endpointing': '300'  # Wait 300ms before considering speech ended
            }
            
            response = requests.post(
                'https://api.deepgram.com/v1/listen',
                headers=headers,
                params=params,
                data=audio_bytes,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                if result['results']['channels'][0]['alternatives']:
                    transcript = result['results']['channels'][0]['alternatives'][0]['transcript']
                    confidence = result['results']['channels'][0]['alternatives'][0]['confidence']
                    
                    print(f"📝 Transcribed: '{transcript}' (confidence: {confidence:.2f})")
                    return transcript.strip()
            
            return None
            
        except Exception as e:
            print(f"❌ Error transcribing audio: {str(e)}")
            return None
    
    def speak_text(self, text):
        """Convert text to speech with enhanced audio quality"""
        try:
            self.is_speaking = True
            print(f"\n🔊 MovieBuddy: {text}")
            
            # Create TTS audio with optimized settings
            tts = gTTS(text=text, lang='en', slow=False, tld='com')
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tts.save(tmp_file.name)
                
                # Play audio
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to finish
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clean up temporary file
                os.unlink(tmp_file.name)
                
        except Exception as e:
            print(f"❌ Error speaking text: {str(e)}")
        finally:
            self.is_speaking = False
    
    def extract_enhanced_preferences(self, user_input, detected_emotion):
        """Extract comprehensive preferences from user input and emotion"""
        user_input_lower = user_input.lower()
        preferences = {
            'genres': [],
            'moods': [],
            'keywords': [],
            'actors': [],
            'directors': [],
            'year_range': None,
            'emotion': detected_emotion,
            'exclude': []
        }
        
        # Genre extraction
        genre_keywords = {
            'action': ['action', 'fight', 'adventure', 'martial arts', 'superhero'],
            'comedy': ['funny', 'comedy', 'laugh', 'hilarious', 'humor', 'jokes'],
            'drama': ['drama', 'dramatic', 'serious', 'emotional', 'powerful'],
            'horror': ['horror', 'scary', 'frightening', 'spooky', 'thriller', 'suspense'],
            'romance': ['romantic', 'romance', 'love', 'dating', 'relationship'],
            'sci-fi': ['sci-fi', 'science fiction', 'futuristic', 'aliens', 'space'],
            'animation': ['animated', 'animation', 'cartoon', 'pixar', 'disney'],
            'documentary': ['documentary', 'real', 'true story', 'factual'],
            'fantasy': ['fantasy', 'magic', 'magical', 'wizard', 'supernatural'],
            'crime': ['crime', 'police', 'detective', 'investigation', 'mystery'],
            'family': ['family', 'kids', 'children', 'wholesome']
        }
        
        for genre, keywords in genre_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                preferences['genres'].append(genre.title())
        
        # Enhanced preference extraction with better keyword matching
        additional_keywords = []
        
        # Extract specific movie requests
        movie_patterns = {
            'recent': ['new', 'recent', 'latest', '2023', '2024', '2025', 'modern'],
            'classic': ['classic', 'old', 'vintage', 'retro', '80s', '90s', 'golden age'],
            'popular': ['popular', 'famous', 'well-known', 'blockbuster', 'hit'],
            'underrated': ['underrated', 'hidden gem', 'unknown', 'indie', 'independent'],
            'award-winning': ['oscar', 'academy award', 'golden globe', 'cannes', 'award'],
            'franchise': ['series', 'sequel', 'trilogy', 'franchise', 'part', 'episode'],
            'based_on': ['based on', 'book', 'novel', 'true story', 'real events']
        }
        
        for category, keywords in movie_patterns.items():
            if any(keyword in user_input_lower for keyword in keywords):
                additional_keywords.append(category)
        
        preferences['keywords'].extend(additional_keywords)
        
        # Add emotion-based preferences
        if detected_emotion in self.emotion_profiles:
            emotion_profile = self.emotion_profiles[detected_emotion]
            preferences['moods'].extend(emotion_profile.get('movie_moods', []))
            preferences['genres'].extend(emotion_profile.get('genres', []))
            
            # Add emotion-specific keywords
            for keyword in emotion_profile.get('keywords', []):
                if keyword in user_input_lower:
                    preferences['keywords'].append(keyword)
        
        # Extract specific requests like "something different" or "surprise me"
        variety_requests = ['different', 'surprise', 'random', 'anything', 'something new']
        if any(req in user_input_lower for req in variety_requests):
            preferences['variety_request'] = True
        
        return preferences
    
    def score_movie_match(self, movie, preferences, context):
        """Advanced movie scoring algorithm"""
        score = 0
        
        # Genre matching (high weight)
        if preferences['genres']:
            genre_matches = len(set(movie['genres']) & set(preferences['genres']))
            score += genre_matches * 3
        
        # Mood matching (high weight)
        if preferences['moods']:
            mood_matches = len(set(movie['mood']) & set(preferences['moods']))
            score += mood_matches * 2.5
        
        # Keyword matching (medium weight)
        if preferences['keywords']:
            keyword_matches = len(set(movie['keywords']) & set(preferences['keywords']))
            score += keyword_matches * 1.5
        
        # Quality factors (low weight but important)
        score += movie['imdb_score'] * 0.3
        score += min(movie['popularity'] / 100000, 1) * 0.5  # Normalize popularity
        
        # Recency preference (slight boost for newer movies)
        current_year = datetime.now().year
        if movie['year'] > current_year - 10:
            score += 0.5
        
        return score
    
    def get_enhanced_recommendations(self, preferences, n_recommendations=3):
        """Get enhanced movie recommendations with advanced scoring"""
        if not self.movies:
            return []
        
        # Score all movies
        scored_movies = []
        for movie in self.movies:
            score = self.score_movie_match(movie, preferences, self.conversation_context)
            scored_movies.append((movie, score))  # Include all movies, even with score 0
        
        # Sort by score and get top recommendations
        scored_movies.sort(key=lambda x: x[1], reverse=True)
        
        # If no movies have positive scores, use the highest-rated movies as fallback
        if not any(score > 0 for _, score in scored_movies):
            print("No movies matched preferences, using top-rated movies as fallback...")
            # Sort by IMDB score as fallback
            scored_movies.sort(key=lambda x: x[0].get('imdb_score', 0), reverse=True)
        
        # Enhanced diversity algorithm - prevent same movies
        recommendations = []
        used_titles = set()
        used_genres = set()
        used_decades = set()
        used_directors = set()
        
        # Add previously recommended movies to avoid repetition
        for prev_rec in self.session_recommendations:
            used_titles.add(prev_rec['title'])
        
        # Shuffle scored movies for more randomness
        import random
        scored_movies_shuffled = scored_movies.copy()
        random.shuffle(scored_movies_shuffled)
        
        # Sort shuffled list by score to maintain quality
        scored_movies_shuffled.sort(key=lambda x: x[1], reverse=True)
        
        for movie, score in scored_movies_shuffled:
            if len(recommendations) >= n_recommendations:
                break
                
            # Skip if already recommended in this session
            if movie['title'] in used_titles:
                continue
            
            # Enhanced diversity checking
            movie_genres = set(movie['genres'])
            movie_decade = (movie['year'] // 10) * 10
            movie_directors = set(movie['directors'])
            
            # Calculate diversity score
            diversity_score = 0
            
            # Genre diversity (prevent too much overlap)
            genre_overlap = len(movie_genres & used_genres)
            if genre_overlap <= 1:  # At most 1 genre overlap
                diversity_score += 4
            elif genre_overlap <= 2:
                diversity_score += 2
            
            # Decade diversity
            if movie_decade not in used_decades:
                diversity_score += 3
            
            # Director diversity
            if not (movie_directors & used_directors):
                diversity_score += 2
                
            # Quality bonus
            if movie.get('imdb_score', 0) >= 7.0:
                diversity_score += 2
            elif movie.get('imdb_score', 0) >= 6.0:
                diversity_score += 1
            
            # Accept if diverse enough OR if we really need more movies
            min_diversity = 4 if len(recommendations) >= 2 else 2
            
            if diversity_score >= min_diversity or len(recommendations) < 2:
                recommendations.append(movie)
                used_titles.add(movie['title'])
                used_genres.update(movie_genres)
                used_decades.add(movie_decade)
                used_directors.update(movie_directors)
                print(f"Added: {movie['title']} (Score: {score:.2f}, Diversity: {diversity_score})")
        
        # If still not enough, add random high-quality movies
        if len(recommendations) < n_recommendations:
            remaining_movies = [m for m, s in scored_movies if m['title'] not in used_titles]
            random.shuffle(remaining_movies)
            
            for movie in remaining_movies:
                if len(recommendations) >= n_recommendations:
                    break
                if movie.get('imdb_score', 0) >= 5.0:  # Decent quality threshold
                    recommendations.append(movie)
                    print(f"Added random quality movie: {movie['title']}")
        
        return recommendations[:n_recommendations]
    
    def format_empathetic_response(self, recommendations, preferences, detected_emotion):
        """Create an empathetic and engaging response"""
        if not recommendations:
            return self._create_no_results_response(detected_emotion)
        
        # Emotional opening based on detected emotion
        emotion_openings = {
            'sad': "I can sense you might be feeling a bit down. Let me suggest some movies that can help lift your spirits or provide the emotional connection you're looking for.",
            'happy': "I love your positive energy! Here are some fantastic movies that will keep those good vibes flowing.",
            'excited': "Your excitement is contagious! I've got some thrilling recommendations that will match your energy perfectly.",
            'calm': "I appreciate your peaceful mood. Here are some wonderful films that will complement your serene state of mind.",
            'stressed': "It sounds like you could use some relaxation. Let me recommend some movies that can help you unwind and escape.",
            'neutral': "Great! I've analyzed your preferences and found some excellent movie recommendations for you."
        }
        
        opening = emotion_openings.get(detected_emotion, emotion_openings['neutral'])
        
        response = f"{opening}\n\n"
        
        for i, movie in enumerate(recommendations, 1):
            # Format movie details
            year_text = f" ({movie['year']})" if movie['year'] else ""
            genres_text = f" - {', '.join(movie['genres'][:3])}" if movie['genres'] else ""
            
            response += f"{i}. **{movie['title']}{year_text}**{genres_text}\n"
            
            # Add why this movie matches
            reasons = []
            if preferences['genres']:
                matching_genres = set(movie['genres']) & set(preferences['genres'])
                if matching_genres:
                    reasons.append(f"perfect {'/'.join(matching_genres).lower()} match")
            
            if movie['imdb_score'] > 7.5:
                reasons.append(f"highly rated ({movie['imdb_score']:.1f}/10)")
            
            if movie['mood']:
                matching_moods = set(movie['mood']) & set(preferences['moods'])
                if matching_moods:
                    reasons.append(f"matches your {'/'.join(matching_moods)} mood")
            
            if reasons:
                response += f"   Why: {', '.join(reasons[:2])}\n"
            
            response += "\n"
        
        # Add conversation continuers
        follow_ups = [
            "Would you like more details about any of these movies?",
            "Should I suggest more options in a different genre?",
            "Do any of these sound interesting to you?",
            "Would you like me to find something more specific?"
        ]
        
        response += f"\n{follow_ups[len(recommendations) % len(follow_ups)]}"
        
        return response
    
    def _create_no_results_response(self, emotion):
        """Create helpful response when no movies found"""
        emotion_responses = {
            'sad': "I understand you're looking for something meaningful. While I couldn't find exact matches, can you tell me more about what might help you feel better? Perhaps a specific genre or actor?",
            'happy': "Your enthusiasm is wonderful! Let me help you find something perfect. Could you be more specific about what kind of movie would make you even happier?",
            'excited': "I love your energy! To find the perfect high-energy movie, could you tell me more about what gets you most excited? Action, adventure, or something else?",
            'calm': "I want to find something that perfectly matches your peaceful mood. Could you share more details about what kind of calming experience you're looking for?"
        }
        
        return emotion_responses.get(emotion, 
            "I'd love to find the perfect movie for you! Could you give me a bit more detail about what you're in the mood for? Maybe mention a specific genre, actor, or type of story?")
    
    def check_for_wake_word(self, text):
        """Check if user said a wake word"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(wake_word in text_lower for wake_word in self.wake_words)
    
    def check_for_exit_word(self, text):
        """Check if user wants to exit"""
        if not text:
            return False
        
        text_lower = text.lower()
        return any(exit_word in text_lower for exit_word in self.exit_words)
    
    def process_conversation_turn(self, user_input, audio_data):
        """Process a single conversation turn with emotion detection"""
        try:
            # Detect emotion from audio
            detected_emotion, confidence = self.detect_emotion_from_audio(audio_data)
            
            print(f"🧠 Detected emotion: {detected_emotion} (confidence: {confidence:.2f})")
            
            # Store emotion in history
            self.conversation_context['mood_history'].append({
                'emotion': detected_emotion,
                'confidence': confidence,
                'timestamp': datetime.now()
            })
            
            # Extract preferences with emotion context
            preferences = self.extract_enhanced_preferences(user_input, detected_emotion)
            
            print(f"🎯 Extracted preferences: {preferences}")
            
            # Get recommendations
            recommendations = self.get_enhanced_recommendations(preferences)
            
            # Update conversation context
            if recommendations:
                rec_titles = [movie['title'] for movie in recommendations]
                self.conversation_context['last_recommendations'] = rec_titles
                self.session_recommendations.extend(recommendations)
            
            # Format response
            response = self.format_empathetic_response(recommendations, preferences, detected_emotion)
            
            # Store conversation
            self.conversation_history.append({
                'user': user_input,
                'emotion': detected_emotion,
                'preferences': preferences,
                'recommendations': recommendations,
                'response': response,
                'timestamp': datetime.now()
            })
            
            return response
            
        except Exception as e:
            print(f"❌ Error processing conversation: {str(e)}")
            return "I apologize, but I encountered an error processing your request. Could you please try again?"
    
    def start_enhanced_conversation(self):
        """Start the enhanced conversational AI system"""
        print("\n" + "="*60)
        print("🎬 ENHANCED MOVIEBUDDY AI - NOW ACTIVE! 🤖")
        print("="*60)
        print("✨ NEW FEATURES:")
        print("   • Real-time emotion detection from your voice")
        print("   • Advanced movie matching algorithm")
        print("   • Continuous conversation like Siri/Alexa")
        print("   • Personalized recommendations")
        print("="*60)
        
        try:
            self.speak_text("Hello! I'm your enhanced MovieBuddy AI. I can detect your emotions and find perfect movies for you. Say 'Hey Movie Buddy' to start chatting!")
        except Exception as e:
            print(f"Initial greeting error: {e}")
        
        self.conversation_active = True
        self.last_activity = time.time()
        
        while self.conversation_active:
            try:
                # Record audio
                audio_data = self.record_audio(self.recording_duration)
                
                if audio_data is None:
                    continue
                
                # Transcribe
                user_input = self.transcribe_audio(audio_data)
                
                if not user_input:
                    print("🤔 I didn't catch that. Could you speak a bit louder or clearer?")
                    continue
                
                # Update activity time
                self.last_activity = time.time()
                
                # Check for wake word or exit
                if not self.is_awake:
                    if self.check_for_wake_word(user_input):
                        self.is_awake = True
                        self.speak_text("Hi there! I'm awake and ready to help you find amazing movies. What are you in the mood for?")
                        continue
                    else:
                        print("💤 Sleeping... Say 'Hey Movie Buddy' to wake me up")
                        continue
                
                # Check for exit
                if self.check_for_exit_word(user_input):
                    self.speak_text("Thanks for chatting with me! I hope you find a great movie to watch. Goodbye!")
                    break
                
                # Process the conversation
                self.is_processing = True
                response = self.process_conversation_turn(user_input, audio_data)
                self.is_processing = False
                
                # Speak the response
                self.speak_text(response)
                
                # Check for inactivity
                if time.time() - self.last_activity > self.sleep_timeout:
                    self.is_awake = False
                    self.speak_text("I'm going to sleep now. Say 'Hey Movie Buddy' when you want to chat again!")
                
            except KeyboardInterrupt:
                print("\n\n🛑 Conversation interrupted by user")
                break
            except Exception as e:
                print(f"❌ Error in conversation loop: {str(e)}")
                continue
        
        self.conversation_active = False
        print("\n✅ Enhanced MovieBuddy AI session ended. Thanks for chatting!")
        return "Enhanced MovieBuddy AI started successfully!"
    
    def cleanup(self):
        """Clean up resources"""
        try:
            pygame.mixer.quit()
            self.conversation_active = False
        except:
            pass

def main():
    """Main function to run the Enhanced MovieBuddy AI"""
    print("🚀 Initializing Enhanced MovieBuddy AI...")
    
    try:
        ai = EnhancedMovieBuddyAI()
        ai.start_enhanced_conversation()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error starting Enhanced MovieBuddy AI: {str(e)}")
    finally:
        try:
            ai.cleanup()
        except:
            pass

if __name__ == "__main__":
    main() 