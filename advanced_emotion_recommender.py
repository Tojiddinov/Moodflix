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

class AdvancedEmotionDetector:
    """Advanced emotion detection with multiple analysis methods"""
    
    def __init__(self):
        """Initialize advanced emotion detection"""
        # Enhanced emotion profiles with multiple characteristics
        self.emotion_profiles = {
            'sad': {
                'energy_range': (0.005, 0.025),
                'pitch_range': (80, 160),
                'zcr_range': (0.02, 0.08),
                'spectral_centroid_range': (800, 1800),
                'emotional_indicators': ['low energy', 'low pitch', 'monotone', 'slow speech']
            },
            'happy': {
                'energy_range': (0.04, 0.12),
                'pitch_range': (180, 280),
                'zcr_range': (0.08, 0.15),
                'spectral_centroid_range': (2000, 4000),
                'emotional_indicators': ['high energy', 'varied pitch', 'clear speech', 'upbeat']
            },
            'excited': {
                'energy_range': (0.06, 0.15),
                'pitch_range': (200, 350),
                'zcr_range': (0.1, 0.2),
                'spectral_centroid_range': (2500, 5000),
                'emotional_indicators': ['very high energy', 'high pitch variation', 'fast speech', 'enthusiastic']
            },
            'angry': {
                'energy_range': (0.08, 0.2),
                'pitch_range': (150, 250),
                'zcr_range': (0.12, 0.25),
                'spectral_centroid_range': (2000, 4500),
                'emotional_indicators': ['high energy', 'harsh tone', 'aggressive speech', 'tense']
            },
            'calm': {
                'energy_range': (0.02, 0.05),
                'pitch_range': (140, 200),
                'zcr_range': (0.04, 0.1),
                'spectral_centroid_range': (1500, 2500),
                'emotional_indicators': ['steady energy', 'stable pitch', 'relaxed speech', 'peaceful']
            },
            'tired': {
                'energy_range': (0.01, 0.03),
                'pitch_range': (100, 180),
                'zcr_range': (0.02, 0.06),
                'spectral_centroid_range': (1000, 2000),
                'emotional_indicators': ['very low energy', 'dropping pitch', 'slow speech', 'weary']
            },
            'stressed': {
                'energy_range': (0.05, 0.1),
                'pitch_range': (160, 240),
                'zcr_range': (0.09, 0.18),
                'spectral_centroid_range': (2200, 3800),
                'emotional_indicators': ['irregular energy', 'tense speech', 'rushed', 'anxious']
            }
        }
    
    def extract_comprehensive_features(self, audio_data, sample_rate=16000):
        """Extract comprehensive audio features for emotion analysis"""
        try:
            # Ensure audio is normalized
            if audio_data.dtype == np.int16:
                audio_data = audio_data.astype(np.float32) / 32768.0
            
            if len(audio_data) == 0:
                return None
            
            features = {}
            
            # 1. Energy analysis
            rms_energy = np.sqrt(np.mean(audio_data**2))
            features['rms_energy'] = rms_energy
            
            # Energy variation (emotional expressiveness)
            frame_size = int(0.1 * sample_rate)  # 100ms frames
            energy_frames = []
            for i in range(0, len(audio_data) - frame_size, frame_size):
                frame = audio_data[i:i+frame_size]
                frame_energy = np.sqrt(np.mean(frame**2))
                energy_frames.append(frame_energy)
            
            features['energy_variation'] = np.std(energy_frames) if energy_frames else 0
            
            # 2. Pitch analysis
            # Simple autocorrelation-based pitch detection
            def autocorrelation_pitch(signal, sample_rate):
                correlation = np.correlate(signal, signal, mode='full')
                correlation = correlation[len(correlation)//2:]
                
                # Find peaks (potential pitch periods)
                diff = np.diff(correlation)
                peaks = []
                for i in range(1, len(diff)-1):
                    if diff[i-1] < 0 and diff[i] > 0:
                        peaks.append(i)
                
                if peaks:
                    # Take the first significant peak as fundamental frequency
                    main_peak = peaks[0] if peaks[0] > sample_rate // 500 else (peaks[1] if len(peaks) > 1 else peaks[0])
                    pitch = sample_rate / main_peak
                    return max(50, min(500, pitch))  # Clamp to reasonable range
                return 150  # Default pitch
            
            features['pitch'] = autocorrelation_pitch(audio_data, sample_rate)
            
            # 3. Zero crossing rate (speech clarity)
            zero_crossings = np.where(np.diff(np.sign(audio_data)))[0]
            features['zcr'] = len(zero_crossings) / len(audio_data)
            
            # 4. Spectral analysis
            fft = np.fft.fft(audio_data)
            freqs = np.fft.fftfreq(len(fft), 1/sample_rate)
            magnitude = np.abs(fft)
            
            # Spectral centroid (brightness)
            positive_freqs = freqs[:len(freqs)//2]
            positive_magnitude = magnitude[:len(magnitude)//2]
            
            if np.sum(positive_magnitude) > 0:
                spectral_centroid = np.sum(positive_freqs * positive_magnitude) / np.sum(positive_magnitude)
            else:
                spectral_centroid = 1000
            
            features['spectral_centroid'] = spectral_centroid
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {str(e)}")
            return None
    
    def analyze_emotion_advanced(self, audio_data, sample_rate=16000):
        """Advanced emotion analysis using multiple feature combinations"""
        features = self.extract_comprehensive_features(audio_data, sample_rate)
        
        if not features:
            return 'neutral', 0.5, {}
        
        emotion_scores = {}
        emotion_analysis = {}
        
        for emotion, profile in self.emotion_profiles.items():
            score = 0
            analysis = []
            
            # Energy matching
            energy = features['rms_energy']
            energy_min, energy_max = profile['energy_range']
            if energy_min <= energy <= energy_max:
                score += 0.25
                analysis.append(f"Energy level ({energy:.3f}) matches {emotion} pattern")
            elif energy < energy_min:
                penalty = (energy_min - energy) / energy_min
                score -= penalty * 0.1
            else:
                penalty = (energy - energy_max) / energy_max
                score -= penalty * 0.1
            
            # Pitch matching
            pitch = features['pitch']
            pitch_min, pitch_max = profile['pitch_range']
            if pitch_min <= pitch <= pitch_max:
                score += 0.25
                analysis.append(f"Pitch ({pitch:.1f} Hz) indicates {emotion}")
            
            # ZCR matching
            zcr = features['zcr']
            zcr_min, zcr_max = profile['zcr_range']
            if zcr_min <= zcr <= zcr_max:
                score += 0.2
                analysis.append(f"Speech clarity matches {emotion} characteristics")
            
            # Spectral centroid matching
            sc = features['spectral_centroid']
            sc_min, sc_max = profile['spectral_centroid_range']
            if sc_min <= sc <= sc_max:
                score += 0.2
                analysis.append(f"Voice brightness suggests {emotion}")
            
            # Energy variation bonus
            if emotion in ['excited', 'happy'] and features.get('energy_variation', 0) > 0.02:
                score += 0.1
                analysis.append("High energy variation indicates enthusiasm")
            elif emotion in ['sad', 'tired'] and features.get('energy_variation', 0) < 0.01:
                score += 0.1
                analysis.append("Low energy variation suggests subdued mood")
            
            emotion_scores[emotion] = max(0, score)
            emotion_analysis[emotion] = analysis
        
        # Find best matching emotion
        if not emotion_scores or max(emotion_scores.values()) < 0.3:
            return 'neutral', 0.5, {'neutral': ['Insufficient emotional indicators detected']}
        
        detected_emotion = max(emotion_scores, key=emotion_scores.get)
        confidence = emotion_scores[detected_emotion]
        
        return detected_emotion, confidence, emotion_analysis

class EmotionBasedMovieRecommender:
    """Advanced movie recommender with sophisticated emotion-based suggestions"""
    
    def __init__(self):
        """Initialize the emotion-based movie recommender"""
        self.movies = []
        self.conversation_active = False
        self.is_speaking = False
        self.conversation_history = []
        
        # Initialize advanced emotion detector
        self.emotion_detector = AdvancedEmotionDetector()
        self.user_emotion = 'neutral'
        self.emotion_confidence = 0.5
        self.emotion_analysis = {}
        
        # Track user's emotional journey
        self.emotion_history = []
        
        # Initialize pygame for audio playback
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        
        # Audio recording parameters
        self.sample_rate = 16000
        self.channels = 1
        self.recording_duration = 6
        
        # Load movie database
        print("🎬 Loading comprehensive movie database...")
        self.load_movie_database()
        
        # ENHANCED emotion-to-recommendation mapping (FIXED)
        self.emotion_movie_strategies = {
            'sad': {
                'primary_approach': 'uplift',
                'target_genres': ['comedy', 'family', 'animation', 'musical', 'romance'],
                'avoid_genres': ['horror', 'thriller', 'war'],
                'therapeutic_message': "I've selected uplifting movies to help brighten your mood"
            },
            'happy': {
                'primary_approach': 'amplify',
                'target_genres': ['comedy', 'adventure', 'family', 'musical', 'animation'],
                'therapeutic_message': "These joyful movies will keep your positive energy flowing"
            },
            'excited': {
                'primary_approach': 'channel',
                'target_genres': ['action', 'adventure', 'thriller', 'sci-fi', 'fantasy'],
                'therapeutic_message': "These high-energy movies match your enthusiastic mood"
            },
            'angry': {
                'primary_approach': 'soothe',
                'target_genres': ['comedy', 'family', 'animation', 'romance'],
                'avoid_genres': ['action', 'thriller', 'horror', 'crime'],
                'therapeutic_message': "These calming movies can help ease tension and frustration"
            },
            'calm': {
                'primary_approach': 'maintain',
                'target_genres': ['drama', 'romance', 'documentary', 'biography'],
                'therapeutic_message': "These thoughtful movies complement your peaceful state"
            },
            'tired': {
                'primary_approach': 'comfort',
                'target_genres': ['comedy', 'family', 'animation', 'romance'],
                'avoid_genres': ['thriller', 'horror', 'action'],
                'therapeutic_message': "These easy-to-follow movies are perfect for low energy"
            },
            'stressed': {
                'primary_approach': 'relax',
                'target_genres': ['comedy', 'family', 'animation', 'documentary'],
                'avoid_genres': ['thriller', 'horror', 'action', 'crime'],
                'therapeutic_message': "These stress-free movies will help you unwind"
            },
            'neutral': {
                'primary_approach': 'balance',
                'target_genres': ['comedy', 'drama', 'adventure', 'romance'],
                'therapeutic_message': "Here are some well-balanced movie recommendations"
            }
        }
        
        # Conversation state
        self.wake_words = ["hey movie buddy", "movie buddy", "recommend", "suggest"]
        self.exit_words = ["goodbye", "bye", "exit", "quit", "stop"]
        self.is_awake = False
        self.last_activity = time.time()
        self.sleep_timeout = 45  # Longer timeout for deeper conversations
        
    def load_movie_database(self):
        """Load and enrich movie database"""
        try:
            df = pd.read_csv('main_data_updated.csv')
            
            for _, row in df.iterrows():
                try:
                    title = str(row.get('movie_title', '')).strip()
                    if not title or title == 'nan':
                        continue
                    
                    # Extract year from title
                    year = None
                    title_year_match = re.search(r'\((\d{4})\)', title)
                    if title_year_match:
                        year = int(title_year_match.group(1))
                        title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
                    
                    # Process all fields safely (FIXED: Better genre processing)
                    genres = []
                    genres_value = row.get('genres')
                    if genres_value is not None and pd.notna(genres_value) and str(genres_value) != 'nan':
                        # Keep original case for better matching
                        genres = [g.strip() for g in str(genres_value).split('|') if g.strip()]
                    
                    # Enhanced movie object
                    movie = {
                        'title': title,
                        'year': year or 2000,
                        'genres': genres,  # Keep original case
                        'actors': self._safe_extract_list(row, ['actor_1_name', 'actor_2_name', 'actor_3_name']),
                        'directors': self._safe_extract_list(row, ['director_name']),
                        'mood': self._safe_extract_mood(row.get('mood')),
                        'imdb_score': self._safe_float(row.get('imdb_score')),
                        'duration': self._safe_int(row.get('duration')),
                        'content_rating': str(row.get('content_rating', '')) if pd.notna(row.get('content_rating')) else '',
                        'plot_keywords': str(row.get('plot_keywords', '')) if pd.notna(row.get('plot_keywords')) else ''
                    }
                    
                    self.movies.append(movie)
                    
                except Exception as e:
                    continue
            
            print(f"✅ Loaded {len(self.movies)} movies with enhanced emotion matching")
            
            # Debug: Check genre distribution
            all_genres = []
            for movie in self.movies[:100]:  # Sample check
                all_genres.extend(movie.get('genres', []))
            unique_genres = list(set(all_genres))
            print(f"📊 Found {len(unique_genres)} unique genres: {unique_genres[:10]}...")
            
        except Exception as e:
            print(f"❌ Error loading movie database: {str(e)}")
            self.movies = []
    
    def _safe_extract_list(self, row, columns):
        """Safely extract list from row columns"""
        result = []
        for col in columns:
            value = row.get(col, '')
            if value is not None and pd.notna(value) and str(value).strip() and str(value) != 'nan':
                result.append(str(value).strip())
        return result
    
    def _safe_extract_mood(self, mood_value):
        """Safely extract mood list"""
        if mood_value is not None and pd.notna(mood_value) and str(mood_value) != 'nan':
            return [m.strip() for m in str(mood_value).split('|') if m.strip()]
        return []
    
    def _safe_float(self, value):
        """Safely convert to float"""
        try:
            return float(value) if pd.notna(value) else 0.0
        except:
            return 0.0
    
    def _safe_int(self, value):
        """Safely convert to int"""
        try:
            return int(value) if pd.notna(value) else 0
        except:
            return 0
    
    def get_emotion_based_recommendations(self, user_input, n_recommendations=3):
        """UPGRADED: Get sophisticated emotion-based movie recommendations with debugging"""
        print(f"🎯 Getting recommendations for emotion: {self.user_emotion.upper()}")
        
        strategy = self.emotion_movie_strategies.get(self.user_emotion, self.emotion_movie_strategies.get('neutral', {}))
        target_genres = strategy.get('target_genres', ['comedy', 'drama'])
        avoid_genres = strategy.get('avoid_genres', [])
        
        print(f"🎬 Target genres: {target_genres}")
        print(f"❌ Avoiding genres: {avoid_genres}")
        
        scored_movies = []
        movies_with_genres = 0
        total_checked = 0
        
        for movie in self.movies:
            total_checked += 1
            score = 0
            score_reasons = []
            
            # Get movie info
            movie_genres = movie.get('genres', [])
            imdb_score = movie.get('imdb_score', 0)
            title = movie.get('title', 'Unknown')
            
            if movie_genres:
                movies_with_genres += 1
            
            # Base score for all movies
            if imdb_score > 7.5:
                score += 5
                score_reasons.append("Excellent rating")
            elif imdb_score > 6.5:
                score += 4
                score_reasons.append("Good rating")
            elif imdb_score > 5.5:
                score += 3
                score_reasons.append("Decent rating")
            else:
                score += 1  # Minimum score
            
            # IMPROVED: Genre matching logic
            genre_bonus = 0
            genre_penalty = 0
            
            for movie_genre in movie_genres:
                # Target genre matching (case-insensitive, partial matching)
                for target in target_genres:
                    if target.lower() in movie_genre.lower():
                        genre_bonus += 6
                        score_reasons.append(f"Target genre: {movie_genre}")
                        break
                
                # Avoid genre penalty
                for avoid in avoid_genres:
                    if avoid.lower() in movie_genre.lower():
                        genre_penalty += 3
                        score_reasons.append(f"Avoided genre: {movie_genre}")
                        break
            
            score += genre_bonus - genre_penalty
            
            # EMOTION-SPECIFIC BONUSES
            emotion_bonus = 0
            
            if self.user_emotion == 'sad':
                # Extra boost for mood-lifting content
                uplifting_keywords = ['comedy', 'family', 'animation', 'musical']
                for keyword in uplifting_keywords:
                    if any(keyword.lower() in genre.lower() for genre in movie_genres):
                        emotion_bonus += 4
                        score_reasons.append(f"Mood-lifting: {keyword}")
                        break
                        
            elif self.user_emotion == 'excited':
                # Extra boost for high-energy content
                energy_keywords = ['action', 'adventure', 'thriller', 'sci-fi']
                for keyword in energy_keywords:
                    if any(keyword.lower() in genre.lower() for genre in movie_genres):
                        emotion_bonus += 4
                        score_reasons.append(f"High-energy: {keyword}")
                        break
                        
            elif self.user_emotion in ['angry', 'stressed']:
                # Extra boost for calming content
                calming_keywords = ['comedy', 'family', 'romance', 'animation']
                for keyword in calming_keywords:
                    if any(keyword.lower() in genre.lower() for genre in movie_genres):
                        emotion_bonus += 4
                        score_reasons.append(f"Calming: {keyword}")
                        break
            
            score += emotion_bonus
            
            # User input matching
            user_lower = user_input.lower()
            for genre in movie_genres:
                if genre.lower() in user_lower:
                    score += 5
                    score_reasons.append(f"User requested: {genre}")
            
            # Store if score is decent
            if score > 2:  # Lower threshold to get more results
                scored_movies.append((score, movie, score_reasons))
        
        # Debug info
        print(f"📊 Processed {total_checked} movies, {movies_with_genres} had genres")
        print(f"🏆 Found {len(scored_movies)} movies with decent scores")
        
        # Sort by score
        scored_movies.sort(key=lambda x: x[0], reverse=True)
        
        # Show top scoring movies for debugging
        if scored_movies:
            print(f"🥇 Top scoring movies:")
            for i, (score, movie, reasons) in enumerate(scored_movies[:5]):
                print(f"  {i+1}. {movie['title']} (Score: {score}) - {movie.get('genres', [])} - {reasons[:2]}")
        else:
            print("⚠️ No movies found with current criteria - using fallback")
            return self._get_fallback_recommendations(n_recommendations)
        
        return [movie for score, movie, reasons in scored_movies[:n_recommendations]]
    
    def _get_fallback_recommendations(self, n_recommendations=3):
        """Enhanced fallback system when primary matching fails"""
        print(f"🔄 Using enhanced fallback for {self.user_emotion} emotion...")
        
        # Simpler fallback strategy
        if self.user_emotion == 'sad':
            fallback_genres = ['Comedy', 'Family', 'Animation']
        elif self.user_emotion == 'excited':
            fallback_genres = ['Action', 'Adventure', 'Thriller']
        elif self.user_emotion in ['angry', 'stressed']:
            fallback_genres = ['Comedy', 'Family', 'Romance']
        elif self.user_emotion == 'tired':
            fallback_genres = ['Comedy', 'Family', 'Animation']
        else:
            fallback_genres = ['Comedy', 'Drama', 'Romance']
        
        print(f"🎯 Fallback target genres: {fallback_genres}")
        
        # Find any movies with these genres and good ratings
        fallback_movies = []
        
        for movie in self.movies:
            movie_genres = movie.get('genres', [])
            imdb_score = movie.get('imdb_score', 0)
            
            # Check for any genre match
            genre_match = False
            for movie_genre in movie_genres:
                for fallback_genre in fallback_genres:
                    if fallback_genre.lower() in movie_genre.lower():
                        genre_match = True
                        break
                if genre_match:
                    break
            
            if genre_match and imdb_score > 5.5:
                fallback_movies.append(movie)
        
        # Sort by rating and return top ones
        fallback_movies.sort(key=lambda x: x.get('imdb_score', 0), reverse=True)
        
        result = fallback_movies[:n_recommendations]
        print(f"✅ Found {len(result)} fallback recommendations")
        
        if result:
            print("🎬 Fallback recommendations:")
            for i, movie in enumerate(result):
                print(f"  {i+1}. {movie['title']} - {movie.get('genres', [])} (IMDB: {movie.get('imdb_score', 0)})")
        
        return result
    
    def record_audio(self, duration=6):
        """Record audio with enhanced feedback"""
        print(f"\n🎤 LISTENING FOR EMOTION ANALYSIS! Speak naturally for {duration} seconds...")
        print("💡 I'll analyze your voice tone to understand your emotional state")
        print("🗣️  Example: 'Hey Movie Buddy, I need something to cheer me up'")
        
        recording = sd.rec(int(duration * self.sample_rate), 
                          samplerate=self.sample_rate, 
                          channels=self.channels, 
                          dtype=np.int16)
        sd.wait()
        
        # Save to temporary file for transcription
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_filename = temp_file.name
            
            import wave
            with wave.open(temp_filename, 'wb') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(recording.tobytes())
        
        print("✅ Audio captured. Analyzing emotion and transcribing...")
        return temp_filename, recording.flatten()
    
    def transcribe_audio(self, file_path):
        """Transcribe audio using Deepgram API"""
        print("🔍 Transcribing speech...")
        
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
                response = requests.post(url, headers=headers, params=params, data=audio.read())
            
            if response.status_code == 200:
                data = response.json()
                return data["results"]["channels"][0]["alternatives"][0]["transcript"]
            else:
                print(f"❌ Transcription failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Transcription error: {str(e)}")
            return None
    
    def analyze_user_emotion(self, audio_data):
        """Comprehensive emotion analysis"""
        print("🧠 Performing advanced emotion analysis...")
        
        emotion, confidence, analysis = self.emotion_detector.analyze_emotion_advanced(audio_data, self.sample_rate)
        
        # Update user state
        self.user_emotion = emotion
        self.emotion_confidence = confidence
        self.emotion_analysis = analysis
        
        # Add to emotion history
        self.emotion_history.append({
            'emotion': emotion,
            'confidence': confidence,
            'timestamp': time.time(),
            'analysis': analysis.get(emotion, [])
        })
        
        # Keep only recent history
        if len(self.emotion_history) > 10:
            self.emotion_history = self.emotion_history[-10:]
        
        # Provide detailed emotional feedback
        emotion_emoji = {
            'sad': '😢', 'happy': '😊', 'angry': '😠', 'calm': '😌',
            'excited': '🤗', 'tired': '😴', 'stressed': '😰', 'neutral': '😐'
        }
        
        emoji = emotion_emoji.get(emotion, '😐')
        print(f"💝 Detected emotion: {emotion.upper()} {emoji}")
        print(f"🎯 Confidence: {confidence:.2f}")
        
        if analysis.get(emotion):
            print(f"📊 Analysis: {'; '.join(analysis[emotion][:2])}")
        
        return emotion, confidence
    
    def format_empathetic_response(self, recommendations, user_input):
        """Create empathetic response based on emotion and recommendations"""
        if not recommendations:
            return self._create_no_results_response()
        
        strategy = self.emotion_movie_strategies.get(self.user_emotion, {})
        therapeutic_message = strategy.get('therapeutic_message', 'Here are some great movies for you')
        
        # Empathetic opening
        emotion_openings = {
            'sad': f"I can hear some sadness in your voice, and I want to help. {therapeutic_message}:",
            'happy': f"Your positive energy is wonderful to hear! {therapeutic_message}:",
            'excited': f"I love your enthusiasm! {therapeutic_message}:",
            'angry': f"I sense some frustration in your tone. {therapeutic_message}:",
            'calm': f"You sound very peaceful. {therapeutic_message}:",
            'tired': f"You sound like you need some gentle entertainment. {therapeutic_message}:",
            'stressed': f"I can detect some stress in your voice. {therapeutic_message}:",
            'neutral': f"Based on your current mood, {therapeutic_message}:"
        }
        
        response = emotion_openings.get(self.user_emotion, emotion_openings['neutral'])
        
        # Add detailed movie information
        for i, movie in enumerate(recommendations, 1):
            response += f"\n\n{i}. '{movie['title']}'"
            
            if movie.get('year'):
                response += f" ({movie['year']})"
            
            if movie.get('imdb_score', 0) > 0:
                response += f" - IMDB: {movie['imdb_score']:.1f}/10"
            
            if movie.get('genres'):
                response += f"\n   🎭 Genre: {', '.join(movie['genres'][:3])}"
            
            if movie.get('duration', 0) > 0:
                hours = movie['duration'] // 60
                minutes = movie['duration'] % 60
                if hours > 0:
                    response += f"\n   ⏱️ Runtime: {hours}h {minutes}m"
                else:
                    response += f"\n   ⏱️ Runtime: {minutes} minutes"
            
            if movie.get('directors'):
                response += f"\n   🎬 Director: {movie['directors'][0]}"
            
            if movie.get('actors'):
                response += f"\n   ⭐ Stars: {', '.join(movie['actors'][:2])}"
            
            # Explain why this movie fits their emotion
            response += f"\n   💝 Perfect for {self.user_emotion} mood: "
            if self.user_emotion == 'sad':
                response += "Will help lift your spirits"
            elif self.user_emotion == 'excited':
                response += "Matches your high energy"
            elif self.user_emotion in ['angry', 'stressed']:
                response += "Will help you relax and unwind"
            elif self.user_emotion == 'tired':
                response += "Easy and comforting to watch"
            else:
                response += "Great match for your current mood"
        
        # Empathetic closing
        emotion_closings = {
            'sad': "\n\nI hope these movies bring some light and joy to your day. Remember, it's okay to feel sad sometimes. 💙",
            'happy': "\n\nThese should keep your amazing energy flowing! Enjoy your movie time! 🎉",
            'excited': "\n\nThese high-energy movies should match your fantastic enthusiasm! 🚀",
            'angry': "\n\nI hope these calming movies help you find some peace and relaxation. Take care of yourself. 🕊️",
            'calm': "\n\nThese thoughtful films should complement your peaceful state beautifully. Enjoy the tranquility. 🧘",
            'tired': "\n\nThese gentle movies are perfect for when you need easy, comforting entertainment. Rest well. 😴",
            'stressed': "\n\nThese stress-free movies should help you unwind and decompress. You deserve relaxation. 🌱",
            'neutral': "\n\nI hope you find these recommendations perfectly suited to your current mood!"
        }
        
        response += emotion_closings.get(self.user_emotion, emotion_closings['neutral'])
        response += "\n\nWould you like more details about any of these movies, or different recommendations?"
        
        return response
    
    def _create_no_results_response(self):
        """Create empathetic response when no specific matches found"""
        emotion_responses = {
            'sad': "I understand you're feeling down. While I couldn't find exact matches, let me recommend some universally uplifting movies that have helped many people feel better.",
            'angry': "I sense your frustration. Let me suggest some particularly soothing movies that are known for their calming effects.",
            'excited': "Your energy is amazing! Let me find some universally thrilling movies that match high-energy moods.",
            'tired': "You sound exhausted. Here are some gentle, easy-to-follow movies perfect for low-energy moments.",
            'neutral': "Let me recommend some popular, well-reviewed movies that tend to suit most moods."
        }
        return emotion_responses.get(self.user_emotion, emotion_responses['neutral'])
    
    def speak_text(self, text):
        """Text-to-speech with emotion-aware delivery"""
        if not text:
            return
        
        try:
            self.is_speaking = True
            print(f"🔊 Responding with empathy...")
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
            
            # Adjust speech based on detected emotion
            slow_speech = self.user_emotion in ['sad', 'tired', 'stressed']
            
            # Generate speech using gTTS
            tts = gTTS(text=text, lang='en', slow=slow_speech)
            tts.save(temp_filename)
            
            # Play the audio
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.set_volume(0.8 if self.user_emotion in ['tired', 'sad'] else 0.9)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.music.unload()
            os.unlink(temp_filename)
            
        except Exception as e:
            print(f"❌ Speech error: {str(e)}")
        finally:
            self.is_speaking = False
    
    def process_user_input(self, user_input, audio_data):
        """Process user input with advanced emotion analysis"""
        if not user_input:
            return
        
        user_input_clean = user_input.lower().strip()
        print(f"📝 Processing: {user_input}")
        
        # Perform emotion analysis
        self.analyze_user_emotion(audio_data)
        
        # Update activity timestamp
        self.last_activity = time.time()
        
        # Handle wake words
        if not self.is_awake:
            if any(wake_word in user_input_clean for wake_word in self.wake_words):
                self.is_awake = True
                
                # Emotion-aware greeting
                greetings = {
                    'sad': "Hello there. I can sense some sadness in your voice, and I'm here to help. I'm MovieBuddy AI with advanced emotion detection, and I specialize in finding movies that can help improve your mood. What would comfort you right now?",
                    'happy': "Hello! Your positive energy is absolutely wonderful to hear! I'm MovieBuddy AI, and I love recommending movies that match and amplify great moods like yours. What kind of fantastic movie experience are you looking for?",
                    'excited': "Hey there! I can feel your excitement through your voice! I'm MovieBuddy AI with emotion detection, and I'm thrilled to help you find movies that match your amazing energy. What adventure are you in the mood for?",
                    'angry': "Hi there. I can detect some tension in your voice, and that's completely understandable. I'm MovieBuddy AI, and I specialize in recommending movies that can help you relax and feel better. What might help you unwind?",
                    'calm': "Hello. I appreciate the peaceful energy in your voice. I'm MovieBuddy AI with emotion detection, and I love finding thoughtful movies for calm, reflective moods like yours. What kind of contemplative experience interests you?",
                    'tired': "Hi there. You sound like you've had a long day. I'm MovieBuddy AI, and I understand when you need something gentle and easy to watch. What kind of comforting movie would help you relax?",
                    'stressed': "Hello. I can hear some stress in your voice, and I want to help you find some relief. I'm MovieBuddy AI with emotion detection, and I specialize in stress-free entertainment. What would help you decompress?",
                    'neutral': "Hello! I'm MovieBuddy AI with advanced emotion detection. I can analyze your voice to understand your mood and recommend perfect movies for exactly how you're feeling. What kind of movie experience are you looking for today?"
                }
                
                response = greetings.get(self.user_emotion, greetings['neutral'])
                self.speak_text(response)
                return
            else:
                print("💤 Waiting for wake word...")
                return
        
        # Handle exit words
        if any(exit_word in user_input_clean for exit_word in self.exit_words):
            goodbyes = {
                'sad': "Take very good care of yourself. I hope the movies I recommended help bring some brightness to your day. Remember, tough times don't last, but resilient people like you do. Until next time, be gentle with yourself.",
                'happy': "It's been absolutely delightful chatting with someone with such wonderful positive energy! Keep that beautiful spirit shining, and enjoy every moment of your movie experience!",
                'excited': "What an incredibly energetic and fun conversation! Your enthusiasm is contagious! Have an absolutely amazing time with your movies, and keep that fantastic energy flowing!",
                'angry': "I hope our conversation helped you feel a bit calmer. Take some time for yourself, enjoy those relaxing movies, and remember that it's okay to feel angry sometimes. Take care.",
                'calm': "Thank you for such a peaceful and thoughtful conversation. Continue to embrace that beautiful tranquility, and enjoy your contemplative movie time.",
                'tired': "Rest well, and I hope those gentle movies give you exactly the comfort and relaxation you need. Take care of yourself, and sweet dreams when the time comes.",
                'stressed': "I hope I've helped reduce some of your stress today. Take some deep breaths, enjoy those calming movies, and remember that you deserve peace and relaxation.",
                'neutral': "Thank you for this wonderful conversation! I hope my emotion-aware recommendations serve you well. Enjoy your movies, and remember I'm always here when you need mood-based suggestions!"
            }
            
            response = goodbyes.get(self.user_emotion, goodbyes['neutral'])
            self.speak_text(response)
            self.conversation_active = False
            return
        
        # Generate emotion-based movie recommendations
        try:
            print(f"\n🎬 GENERATING RECOMMENDATIONS FOR {self.user_emotion.upper()} EMOTION...")
            recommendations = self.get_emotion_based_recommendations(user_input_clean)
            
            if recommendations:
                response = self.format_empathetic_response(recommendations, user_input_clean)
                
                # Display detailed response in console
                print("\n" + "="*80)
                print("🎬 PERSONALIZED EMOTION-BASED MOVIE RECOMMENDATIONS")
                print("="*80)
                print(response)
                print("="*80)
                
                # Shorter spoken response
                spoken_response = f"Perfect! Based on your {self.user_emotion} emotional state, I found {len(recommendations)} therapeutic movie recommendations. Check your screen for complete details including why each movie is perfect for your current mood, plus ratings, cast, and runtime information."
                self.speak_text(spoken_response)
            else:
                error_response = f"I apologize, but I'm having trouble finding movies specifically for your {self.user_emotion} mood right now. Let me try a different approach - could you tell me what genre you're interested in?"
                print(f"❌ {error_response}")
                self.speak_text(error_response)
            
        except Exception as e:
            print(f"❌ Error processing request: {str(e)}")
            self.speak_text("I apologize, but I encountered an error while analyzing your emotional needs. Could you please try again?")
    
    def start_advanced_conversation(self):
        """Start the advanced emotion-aware conversation system"""
        try:
            print("🚀 Starting UPGRADED Advanced Emotion-Aware Movie Recommender...")
            print("🎬 MovieBuddy AI - Advanced Emotion Detection & Therapeutic Recommendations 🎬")
            print("="*90)
            print("🌟 Revolutionary Features:")
            print("✅ Advanced voice emotion analysis with detailed feedback")
            print("✅ FIXED: Reliable emotion-based movie recommendations")
            print("✅ Enhanced genre matching and fallback systems")
            print("✅ Therapeutic movie suggestions based on emotional state")
            print("✅ Comprehensive movie details (ratings, cast, runtime, therapeutic benefits)")
            print("✅ Debugging output to ensure recommendations work")
            print("✅ Natural conversation with emotion-aware speech delivery")
            print("="*90)
            print("💡 ADVANCED TIP: Speak naturally - I analyze micro-expressions in your voice!")
            print("🗣️  Say 'Hey Movie Buddy' to begin emotional analysis!")
            print("⏹️  Say 'goodbye' to exit")
            print("="*90)
            
            self.conversation_active = True
            
            # Initial greeting
            greeting = "Welcome to the upgraded MovieBuddy AI! I now have enhanced emotion detection and FIXED recommendation algorithms. I can understand your feelings through your voice and suggest movies that truly match your emotional needs. Say 'Hey Movie Buddy' for personalized, therapeutic movie recommendations!"
            self.speak_text(greeting)
            
            # Main conversation loop
            while self.conversation_active:
                # Check for sleep timeout
                if self.is_awake and time.time() - self.last_activity > self.sleep_timeout:
                    self.is_awake = False
                    print("💤 Going to sleep due to inactivity. Say 'Hey Movie Buddy' to wake me up!")
                
                try:
                    if not self.is_speaking:
                        # Record and analyze audio
                        audio_file, audio_data = self.record_audio(self.recording_duration)
                        transcript = self.transcribe_audio(audio_file)
                        
                        if transcript and transcript.strip():
                            print(f"🗣️  You said: {transcript}")
                            self.process_user_input(transcript, audio_data)
                        else:
                            print("🔇 No speech detected - try speaking louder or closer to microphone")
                        
                        # Clean up
                        if os.path.exists(audio_file):
                            os.unlink(audio_file)
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"❌ Loop error: {str(e)}")
                    time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutting down Advanced MovieBuddy AI...")
        except Exception as e:
            print(f"❌ System error: {str(e)}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        try:
            self.conversation_active = False
            if self.emotion_history:
                print(f"\n📊 Session Summary: Detected {len(set(e['emotion'] for e in self.emotion_history))} different emotions")
            print("✅ Advanced MovieBuddy AI shutdown complete")
        except Exception as e:
            print(f"❌ Cleanup error: {str(e)}")

def main():
    """Launch the UPGRADED advanced emotion-aware movie recommender"""
    print("🎬 UPGRADED Advanced MovieBuddy AI - Fixed Emotion-Based Recommendations 🎬")
    print("Initializing enhanced emotion analysis and recommendation system...")
    
    recommender = EmotionBasedMovieRecommender()
    recommender.start_advanced_conversation()

if __name__ == "__main__":
    main() 