import os
import sys
import time
import tempfile
import random
import pygame
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
import pyttsx3  # Add text-to-speech engine
import numpy as np
from collections import deque
import audioop
import wave
import json
from vosk import Model, KaldiRecognizer
import shutil

# Initialize Flask app
app = Flask(__name__)

# Initialize Vosk model
try:
    # Check if model exists, if not download it
    model_path = "vosk-model-small-en-us-0.15"
    if not os.path.exists(model_path):
        print("Downloading Vosk model...")
        import urllib.request
        import zipfile
        import io
        import shutil
        
        url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
        print(f"Downloading model from {url}")
        
        # Create a temporary directory for download
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "model.zip")
        
        # Download the model
        urllib.request.urlretrieve(url, zip_path)
        
        # Extract the model
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Clean up
        shutil.rmtree(temp_dir)
        print("Model downloaded and extracted successfully")
    
    # Verify model files exist
    if not os.path.exists(os.path.join(model_path, "am", "final.mdl")):
        raise Exception("Model files are incomplete. Please try downloading again.")
    
    vosk_model = Model(model_path)
    print("Vosk model initialized successfully")
    VOSK_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize Vosk model: {e}")
    print("Please ensure you have:")
    print("1. vosk installed (pip install vosk)")
    print("2. Internet connection for model download")
    print("3. Sufficient disk space for the model")
    VOSK_AVAILABLE = False

# Initialize text-to-speech engine
try:
    tts_engine = pyttsx3.init()
    # Set properties for the voice
    tts_engine.setProperty('rate', 150)  # Speed of speech
    tts_engine.setProperty('volume', 0.9)  # Volume (0-1)
    voices = tts_engine.getProperty('voices')
    
    # Try to find and set a good quality voice
    selected_voice = None
    for voice in voices:
        # Prefer Microsoft voices if available
        if "microsoft" in voice.name.lower():
            selected_voice = voice
            break
        # Otherwise prefer female voices
        elif "female" in voice.name.lower() and not selected_voice:
            selected_voice = voice
    
    # If we found a preferred voice, use it
    if selected_voice:
        tts_engine.setProperty('voice', selected_voice.id)
        print(f"Using voice: {selected_voice.name}")
    
    # Test the TTS engine
    tts_engine.say("Test")
    tts_engine.runAndWait()
    
    print("Text-to-speech initialized successfully")
    TTS_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize text-to-speech: {e}")
    print("Please ensure you have the following:")
    print("1. pyttsx3 is installed (pip install pyttsx3)")
    print("2. pywin32 is installed on Windows (pip install pywin32)")
    print("3. espeak is installed on Linux (sudo apt-get install espeak)")
    print("4. nsss is available on MacOS")
    TTS_AVAILABLE = False

# Initialize speech recognition
try:
    recognizer = sr.Recognizer()
    
    # Improved configuration for better recognition
    recognizer.energy_threshold = 4000  # Higher threshold for better voice detection
    recognizer.dynamic_energy_threshold = True  # Automatically adjust for ambient noise
    recognizer.dynamic_energy_adjustment_damping = 0.15  # More responsive to changes
    recognizer.dynamic_energy_ratio = 1.5  # More lenient ratio
    recognizer.pause_threshold = 0.8  # Longer pause between phrases
    recognizer.operation_timeout = None  # No timeout for operations
    recognizer.phrase_threshold = 0.3  # More sensitive to phrase detection
    recognizer.non_speaking_duration = 0.5  # Longer duration for non-speaking detection
    
    print("Speech recognition initialized successfully")
    SPEECH_RECOGNITION_AVAILABLE = True
except Exception as e:
    print(f"Warning: Could not initialize speech recognition: {e}")
    SPEECH_RECOGNITION_AVAILABLE = False

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
    "confused": ["Sci-Fi", "Thriller", "Mystery"],
    "romantic": ["Romance", "Drama", "Comedy"],
    "adventurous": ["Adventure", "Action", "Sci-Fi"],
    "thoughtful": ["Drama", "Sci-Fi", "Mystery"],
    "energetic": ["Action", "Adventure", "Comedy"],
    "peaceful": ["Animation", "Romance", "Drama"],
    "mysterious": ["Mystery", "Thriller", "Sci-Fi"],
    "inspired": ["Drama", "Adventure", "Biography"],
    "playful": ["Animation", "Comedy", "Family"]
}

# Complex query patterns
COMPLEX_PATTERNS = {
    "time_period": {
        "80s": ["1980", "1981", "1982", "1983", "1984", "1985", "1986", "1987", "1988", "1989"],
        "90s": ["1990", "1991", "1992", "1993", "1994", "1995", "1996", "1997", "1998", "1999"],
        "2000s": ["2000", "2001", "2002", "2003", "2004", "2005", "2006", "2007", "2008", "2009"],
        "2010s": ["2010", "2011", "2012", "2013", "2014", "2015", "2016", "2017", "2018", "2019"]
    },
    "directors": {
        "nolan": ["Christopher Nolan"],
        "spielberg": ["Steven Spielberg"],
        "tarantino": ["Quentin Tarantino"],
        "scorsese": ["Martin Scorsese"],
        "kubrick": ["Stanley Kubrick"]
    },
    "actors": {
        "hanks": ["Tom Hanks"],
        "dicaprio": ["Leonardo DiCaprio"],
        "pitt": ["Brad Pitt"],
        "depp": ["Johnny Depp"],
        "cruise": ["Tom Cruise"]
    },
    "themes": {
        "time_travel": ["time travel", "time machine", "time loop"],
        "space": ["space", "astronaut", "planet", "galaxy"],
        "crime": ["crime", "heist", "robbery", "detective"],
        "love": ["love", "romance", "relationship", "dating"],
        "family": ["family", "parent", "child", "sibling"]
    }
}

class AudioProcessor:
    """Advanced audio processing for better voice recognition"""
    
    def __init__(self):
        self.sample_rate = 16000
        self.chunk_size = 1024
        self.buffer_size = 10  # Number of chunks to buffer
        self.audio_buffer = []
        self.vad_threshold = 0.5
        self.speaking_threshold = 0.6
        self.silence_threshold = 0.3
        self.min_speaking_frames = 15
        
        # Speech enhancement settings
        self.noise_reduction_level = 0.7
        self.gain = 1.5
        self.spectral_subtraction = True
        
    def process_audio(self, audio_data):
        """Apply advanced audio processing to improve recognition"""
        try:
            # Convert audio data to numpy array
            raw_data = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply preemphasis filter to boost high frequencies
            preemphasized = self._preemphasis(raw_data)
            
            # Apply noise reduction
            enhanced = self._noise_reduction(preemphasized)
            
            # Apply normalization
            normalized = self._normalize_audio(enhanced)
            
            return normalized
        except Exception as e:
            print(f"Error processing audio: {e}")
            return audio_data  # Return original data on error
    
    def _preemphasis(self, signal, coeff=0.97):
        """Apply preemphasis filter to boost high frequencies"""
        return np.append(signal[0], signal[1:] - coeff * signal[:-1])
    
    def _noise_reduction(self, signal):
        """Apply noise reduction to audio"""
        if not self.spectral_subtraction:
            return signal
            
        # Simple spectral subtraction-based noise reduction
        try:
            # Calculate FFT
            fft = np.fft.rfft(signal)
            # Get magnitude
            magnitude = np.abs(fft)
            # Get phase
            phase = np.angle(fft)
            
            # Estimate noise from first 500ms
            noise_estimate = np.mean(magnitude[:int(0.5 * self.sample_rate / 2)])
            
            # Apply spectral subtraction
            magnitude = np.maximum(magnitude - noise_estimate * self.noise_reduction_level, 0)
            
            # Reconstruct signal
            enhanced_fft = magnitude * np.exp(1j * phase)
            enhanced_signal = np.fft.irfft(enhanced_fft)
            
            # Apply gain
            enhanced_signal = enhanced_signal * self.gain
            
            return enhanced_signal.astype(np.int16)
        except Exception as e:
            print(f"Error in noise reduction: {e}")
            return signal
    
    def _normalize_audio(self, signal):
        """Normalize audio signal to have consistent volume"""
        try:
            # Check if signal needs normalization
            max_val = np.max(np.abs(signal))
            if max_val > 0:
                # Calculate normalization factor (70% of max possible amplitude)
                target_level = 0.7 * 32767  # 70% of max 16-bit value
                normalize_factor = min(target_level / max_val, 3.0)  # Cap at 3x gain
                
                # Apply normalization
                normalized = signal * normalize_factor
                
                # Clip to valid 16-bit range
                normalized = np.clip(normalized, -32768, 32767)
                return normalized.astype(np.int16)
            return signal
        except Exception as e:
            print(f"Error in audio normalization: {e}")
            return signal
    
    def detect_voice(self, audio_data):
        """Enhanced voice activity detection with buffering"""
        try:
            # Convert audio to numpy array
            raw_data = np.frombuffer(audio_data, dtype=np.int16)
            
            # Add to buffer
            self.audio_buffer.append(raw_data)
            if len(self.audio_buffer) > self.buffer_size:
                self.audio_buffer.pop(0)
            
            # Use entire buffer for more stable detection
            combined_audio = np.concatenate(self.audio_buffer)
            
            # Calculate energy
            energy = np.sum(combined_audio.astype(np.float32)**2) / len(combined_audio)
            
            # Calculate zero-crossing rate
            zero_crossings = np.sum(np.abs(np.diff(np.signbit(combined_audio)))) / len(combined_audio)
            
            # Spectral centroid
            fft = np.abs(np.fft.rfft(combined_audio))
            freqs = np.fft.rfftfreq(len(combined_audio), 1.0/self.sample_rate)
            if np.sum(fft) > 0:
                centroid = np.sum(freqs * fft) / np.sum(fft)
            else:
                centroid = 0
                
            # Human voice typically has centroid between 500Hz and 2000Hz
            centroid_factor = 1.0
            if 500 <= centroid <= 2000:
                centroid_factor = 1.5
            
            # Calculate spectral flux
            if len(self.audio_buffer) > 1:
                prev_fft = np.abs(np.fft.rfft(self.audio_buffer[-2]))
                if len(prev_fft) == len(fft):
                    spectral_flux = np.sum(np.abs(fft - prev_fft)) / len(fft)
                else:
                    spectral_flux = 0
            else:
                spectral_flux = 0
            
            # Combine factors for voice detection
            energy_factor = np.log1p(energy) / 10  # Logarithmic scaling
            zcr_factor = zero_crossings * 10
            flux_factor = spectral_flux * 20
            
            # Calculate voice probability
            voice_probability = (energy_factor * 0.6 + zcr_factor * 0.2 + flux_factor * 0.2) * centroid_factor
            
            # Decision with hysteresis
            is_speaking = voice_probability > self.speaking_threshold
            is_silent = voice_probability < self.silence_threshold
            
            # If neither speaking nor silent, maintain previous state
            if not is_speaking and not is_silent:
                # Return previous state or default false
                return self.vad_threshold > 0.5
            
            # Update threshold with hysteresis
            if is_speaking:
                self.vad_threshold = min(0.9, self.vad_threshold + 0.1)
            elif is_silent:
                self.vad_threshold = max(0.1, self.vad_threshold - 0.1)
            
            return voice_probability > self.vad_threshold
            
        except Exception as e:
            print(f"Error in voice detection: {e}")
            return False

# Enhance the SpeechProcessor class
class SpeechProcessor:
    def __init__(self):
        """Initialize speech processing with enhanced features"""
        self.recognizer = sr.Recognizer()
        self.history = deque(maxlen=5)  # Store recent recognition results
        self.noise_levels = deque(maxlen=50)  # Track ambient noise levels
        self.voice_activity_log = deque(maxlen=100)  # Store voice activity data
        self.conversation_history = deque(maxlen=10)  # Store conversation history
        self.energy_history = deque(maxlen=50)  # Store energy history for better detection
        
        # Initialize audio processor for advanced audio handling
        self.audio_processor = AudioProcessor()
        
        # Initialize Vosk recognizer
        if VOSK_AVAILABLE:
            self.vosk_recognizer = KaldiRecognizer(vosk_model, 16000)
            print("Vosk recognizer initialized")
        
        # Initialize google recognizer object
        self.google_recognizer = sr.Recognizer()
        self.google_recognizer.energy_threshold = 1000
        self.google_recognizer.dynamic_energy_threshold = True
        self.google_recognizer.dynamic_energy_adjustment_damping = 0.15
        self.google_recognizer.pause_threshold = 0.8
        self.google_recognizer.phrase_threshold = 0.3
        self.google_recognizer.non_speaking_duration = 0.5
        self.google_recognizer.operation_timeout = None
        
        # Enhanced recognition settings with better sensitivity
        self.recognizer.energy_threshold = 800  # Lower threshold for better sensitivity
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.dynamic_energy_adjustment_damping = 0.15  # More responsive to changes
        self.recognizer.pause_threshold = 0.8  # Longer pause for better phrase detection
        self.recognizer.phrase_threshold = 0.3  # More sensitive to phrases
        self.recognizer.non_speaking_duration = 0.5  # Longer non-speaking duration
        self.recognizer.operation_timeout = None  # No timeout for operations
        
        # Advanced sensitivity settings
        self.min_rms = 40  # Lower minimum RMS for better sensitivity
        self.noise_factor = 1.1  # More sensitive noise multiplier
        self.sensitivity_mode = "very_high"  # Start with highest sensitivity
        self.sensitivity_levels = {
            "very_high": {"factor": 1.1, "min_rms": 40, "energy_threshold": 800},
            "high": {"factor": 1.2, "min_rms": 60, "energy_threshold": 1000},
            "normal": {"factor": 1.3, "min_rms": 80, "energy_threshold": 1500},
            "low": {"factor": 1.5, "min_rms": 100, "energy_threshold": 2000},
            "adaptive": {"factor": None, "min_rms": None, "energy_threshold": None}
        }
        
        # Environment adaptation settings
        self.environment_noise_samples = deque(maxlen=200)  # Larger sample size for better adaptation
        self.last_adaptation_time = time.time()
        self.adaptation_interval = 30  # Adapt every 30 seconds
        
        # Voice detection enhancement
        self.min_voice_duration = 0.1  # Minimum duration for voice detection
        self.max_silence_duration = 0.5  # Maximum silence duration within speech
        self.energy_deviation_threshold = 0.2  # Threshold for energy variation
        
        # Voice activity logging settings
        self.log_enabled = True
        self.debug_mode = False  # Set to True for even more detailed logging
        self.detailed_logging = True  # Enable detailed metrics
        self.log_categories = {
            'voice_detection': True,
            'noise_levels': True,
            'sensitivity': True,
            'recognition': True,
            'errors': True
        }
        
        # Advanced logging metrics
        self.voice_metrics = {
            'detection_count': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'average_speech_duration': 0,
            'total_speech_time': 0,
            'recognition_success_rate': 0,
            'noise_floor_history': deque(maxlen=1000),
            'signal_peaks': deque(maxlen=100)
        }
        
        # Performance tracking
        self.performance_metrics = {
            'start_time': time.time(),
            'total_sessions': 0,
            'successful_recognitions': 0,
            'failed_recognitions': 0,
            'average_response_time': 0,
            'total_processing_time': 0
        }

    def listen(self):
        """Enhanced listening function with advanced audio processing"""
        try:
            # First, check available microphones
            mics = sr.Microphone.list_microphone_names()
            if not mics:
                print("No microphones found! Please check your audio settings.")
                return None
                
            print(f"Available microphones: {mics}")
            
            # Try to use the default microphone
            with sr.Microphone(sample_rate=16000) as source:
                print("Adjusting for ambient noise...")
                # Longer calibration for better noise adjustment
                self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
                print(f"Current energy threshold: {self.recognizer.energy_threshold}")
                
                # Ensure minimum threshold
                if self.recognizer.energy_threshold < 800:
                    print("Energy threshold too low, adjusting to minimum value")
                    self.recognizer.energy_threshold = 800
                
                print("Listening...")
                
                # Increase timeout and phrase time limit
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                # Check audio duration
                if len(audio.frame_data) < 16000:  # Less than 1 second
                    print("Audio too short, please speak longer")
                    return None
                
                # Apply audio processing to enhance recognition
                enhanced_audio = self._enhance_audio(audio)
                
                # Try Vosk first (offline)
                vosk_result = self._try_vosk_recognition(enhanced_audio)
                if vosk_result:
                    return vosk_result
                
                # Then try Google recognition
                google_result = self._try_google_recognition(enhanced_audio)
                if google_result:
                    return google_result
                
                # If both fail, try again with the original audio
                print("Enhanced audio recognition failed, trying with original audio...")
                
                # Try Vosk with original audio
                vosk_result = self._try_vosk_recognition(audio)
                if vosk_result:
                    return vosk_result
                
                # Try Google with original audio
                google_result = self._try_google_recognition(audio)
                if google_result:
                    return google_result
                
                print("Could not understand audio. Please speak clearly and try again.")
                return None
                
        except sr.WaitTimeoutError:
            print("Listening timed out. Please try speaking again.")
            return None
        except Exception as e:
            print(f"Error in listen: {e}")
            print("Please check your microphone settings and permissions.")
            return None
    
    def _enhance_audio(self, audio):
        """Apply audio enhancement techniques"""
        try:
            # Get raw audio data
            raw_data = audio.get_raw_data()
            
            # Process through audio processor
            enhanced_data = self.audio_processor.process_audio(raw_data)
            
            # Create new audio data
            enhanced_audio = sr.AudioData(
                enhanced_data.tobytes(),
                audio.sample_rate,
                audio.sample_width
            )
            
            return enhanced_audio
        except Exception as e:
            print(f"Error enhancing audio: {e}")
            return audio  # Return original on error
    
    def _try_vosk_recognition(self, audio):
        """Try recognition with Vosk"""
        if not VOSK_AVAILABLE:
            return None
            
        try:
            # Convert audio to WAV format for Vosk
            wav_data = audio.get_wav_data()
            if self.vosk_recognizer.AcceptWaveform(wav_data):
                result = json.loads(self.vosk_recognizer.Result())
                if result.get("text"):
                    print(f"Vosk recognized: {result['text']}")
                    self.add_to_history(result["text"])
                    
                    # Update performance metrics
                    self.performance_metrics['successful_recognitions'] += 1
                    self.performance_metrics['total_sessions'] += 1
                    
                    return result["text"]
            return None
        except Exception as e:
            print(f"Vosk recognition failed: {e}")
            return None
    
    def _try_google_recognition(self, audio):
        """Try recognition with Google"""
        try:
            text = self.recognizer.recognize_google(audio)
            print(f"Google recognized: {text}")
            self.add_to_history(text)
            
            # Update performance metrics
            self.performance_metrics['successful_recognitions'] += 1
            self.performance_metrics['total_sessions'] += 1
            
            return text
        except sr.UnknownValueError:
            print("Google could not understand audio")
            
            # Update performance metrics
            self.performance_metrics['failed_recognitions'] += 1
            self.performance_metrics['total_sessions'] += 1
            
            return None
        except sr.RequestError as e:
            print(f"Could not request results from Google; {e}")
            return None
            
    def log_voice_activity(self, rms, threshold, is_active, source="main"):
        """Log voice activity data with enhanced metrics"""
        if self.log_enabled:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            
            # Calculate advanced metrics
            current_noise_floor = sum(self.noise_levels) / len(self.noise_levels) if self.noise_levels else 0
            signal_to_noise = rms / (current_noise_floor + 1e-6)  # Avoid division by zero
            energy_variance = np.var(self.energy_history) if len(self.energy_history) > 0 else 0
            detection_confidence = min(1.0, (rms - threshold) / (threshold + 1e-6))
            
            log_entry = {
                "timestamp": timestamp,
                "rms": rms,
                "threshold": threshold,
                "is_active": is_active,
                "noise_level_avg": current_noise_floor,
                "sensitivity_mode": self.sensitivity_mode,
                "source": source,
                "signal_to_noise_ratio": signal_to_noise,
                "energy_variance": energy_variance,
                "current_noise_floor": current_noise_floor,
                "peak_energy": max(self.energy_history) if self.energy_history else rms,
                "energy_range": max(self.energy_history) - min(self.energy_history) if self.energy_history else 0,
                "detection_confidence": detection_confidence
            }
            
            self.voice_activity_log.append(log_entry)
            
            # Update metrics
            if is_active:
                self.voice_metrics['detection_count'] += 1
                
            # Debug output with enhanced information
            if self.debug_mode:
                self._print_debug_info(log_entry)
            elif self.detailed_logging:
                print(f"Voice Activity: RMS={rms:.2f}, SNR={signal_to_noise:.2f}, Confidence={detection_confidence:.2f}, Active={is_active}")
            else:
                print(f"Voice Activity: RMS={rms:.2f}, Threshold={threshold:.2f}, Active={is_active}")
    
    def _print_debug_info(self, log_entry):
        """Print detailed debug information"""
        print(f"\nVoice Activity Log [{log_entry['timestamp']}]:")
        print(f"  Basic Metrics:")
        print(f"    RMS: {log_entry['rms']:.2f}")
        print(f"    Threshold: {log_entry['threshold']:.2f}")
        print(f"    Is Active: {log_entry['is_active']}")
        print(f"  Advanced Metrics:")
        print(f"    Signal-to-Noise Ratio: {log_entry['signal_to_noise_ratio']:.2f}")
        print(f"    Detection Confidence: {log_entry['detection_confidence']:.2f}")
        print(f"    Energy Variance: {log_entry['energy_variance']:.2f}")
        print(f"    Peak Energy: {log_entry['peak_energy']:.2f}")
        print(f"  Environment:")
        print(f"    Current Noise Floor: {log_entry['current_noise_floor']:.2f}")
        print(f"    Sensitivity Mode: {log_entry['sensitivity_mode']}")
        print(f"    Detection Source: {log_entry['source']}")
        print("  Performance Stats:")
        print(f"    Total Detections: {self.voice_metrics['detection_count']}")
        print(f"    Recognition Rate: {(self.performance_metrics['successful_recognitions'] / max(1, self.performance_metrics['total_sessions']) * 100):.1f}%")
    
    def get_voice_activity_stats(self):
        """Get enhanced statistics about voice activity detection"""
        if not self.voice_activity_log:
            return "No voice activity data available"
            
        recent_logs = list(self.voice_activity_log)[-50:]  # Last 50 entries
        if recent_logs:
            total_checks = len(recent_logs)
            active_count = sum(1 for log in recent_logs if log["is_active"])
            avg_rms = sum(log["rms"] for log in recent_logs) / total_checks
            avg_threshold = sum(log["threshold"] for log in recent_logs) / total_checks
            
            # Calculate additional statistics
            avg_snr = sum(log.get("signal_to_noise_ratio", 0) for log in recent_logs) / total_checks
            avg_confidence = sum(log.get("detection_confidence", 0) for log in recent_logs) / total_checks
            max_peak = max(log.get("peak_energy", 0) for log in recent_logs)
            min_noise = min(log.get("current_noise_floor", float('inf')) for log in recent_logs)
            
            stats = f"""Voice Activity Statistics (last 50 checks):
            Basic Metrics:
            - Detection Rate: {(active_count/total_checks)*100:.1f}%
            - Average RMS: {avg_rms:.2f}
            - Average Threshold: {avg_threshold:.2f}
            
            Advanced Metrics:
            - Average Signal-to-Noise Ratio: {avg_snr:.2f}
            - Average Detection Confidence: {avg_confidence:.2f}
            - Peak Energy Level: {max_peak:.2f}
            - Lowest Noise Floor: {min_noise:.2f}
            
            Current Settings:
            - Sensitivity Mode: {self.sensitivity_mode}
            - Noise Factor: {self.noise_factor}
            - Min RMS: {self.min_rms}
            
            Performance Metrics:
            - Total Detections: {self.voice_metrics['detection_count']}
            - Recognition Success Rate: {(self.performance_metrics['successful_recognitions'] / max(1, self.performance_metrics['total_sessions']) * 100):.1f}%
            - Average Response Time: {self.performance_metrics['average_response_time']:.2f}ms
            """
            return stats
        return "Insufficient data for statistics"
        
    def get_performance_report(self):
        """Generate a detailed performance report"""
        total_time = time.time() - self.performance_metrics['start_time']
        total_sessions = self.performance_metrics['total_sessions']
        
        if total_sessions == 0:
            return "No performance data available yet"
        
        report = f"""Performance Report:
        Time Period: {total_time:.1f} seconds
        Total Sessions: {total_sessions}
        Success Rate: {(self.performance_metrics['successful_recognitions'] / total_sessions * 100):.1f}%
        Average Response Time: {self.performance_metrics['average_response_time']:.2f}ms
        
        Voice Detection Metrics:
        - Total Detections: {self.voice_metrics['detection_count']}
        - False Positives: {self.voice_metrics['false_positives']}
        - False Negatives: {self.voice_metrics['false_negatives']}
        - Average Speech Duration: {self.voice_metrics['average_speech_duration']:.2f}s
        
        Signal Quality:
        - Average SNR: {np.mean([log.get('signal_to_noise_ratio', 0) for log in self.voice_activity_log]):.2f}
        - Average Confidence: {np.mean([log.get('detection_confidence', 0) for log in self.voice_activity_log]):.2f}
        """
        return report
        
    def set_sensitivity(self, mode):
        """Set voice detection sensitivity mode with enhanced controls"""
        if mode in self.sensitivity_levels:
            self.sensitivity_mode = mode
            if mode != "adaptive":
                settings = self.sensitivity_levels[mode]
                self.noise_factor = settings["factor"]
                self.min_rms = settings["min_rms"]
                self.recognizer.energy_threshold = settings["energy_threshold"]
                print(f"Sensitivity mode set to: {mode}")
                print(f"Settings - Factor: {self.noise_factor}, Min RMS: {self.min_rms}, "
                      f"Energy Threshold: {self.recognizer.energy_threshold}")
            return True
        return False
        
    def get_context(self):
        """Get the recent conversation history"""
        return list(self.conversation_history)
    
    def add_to_history(self, text):
        """Add text to conversation history"""
        if text:
            self.conversation_history.append(text)
            
    def calibrate_noise(self, duration=2):
        """Calibrate noise levels with enhanced feedback"""
        try:
            with sr.Microphone(sample_rate=16000) as source:
                print(f"Calibrating for {duration} seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                
                # Get the calibrated energy threshold
                threshold = self.recognizer.energy_threshold
                print(f"Calibrated energy threshold: {threshold}")
                
                # Store initial noise levels
                self.noise_levels.append(threshold)
                
                # If using Vosk, also calibrate its model
                if VOSK_AVAILABLE:
                    print("Calibrating Vosk model...")
                    # Record a short sample for Vosk
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=1)
                    wav_data = audio.get_wav_data()
                    self.vosk_recognizer.AcceptWaveform(wav_data)
                
                return True
        except Exception as e:
            print(f"Error during calibration: {e}")
            return False
            
    def calibrate_microphone(self):
        """Calibrate microphone settings for optimal voice recognition"""
        try:
            with sr.Microphone(sample_rate=16000) as source:
                print("\n=== Microphone Calibration ===")
                print("Please stay quiet for 2 seconds...")
                self.recognizer.adjust_for_ambient_noise(source, duration=2.0)
                initial_threshold = self.recognizer.energy_threshold
                print(f"Initial noise level: {initial_threshold}")
                
                print("\nNow, please say 'Hello' at a normal volume...")
                try:
                    audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    rms = audioop.rms(audio.get_raw_data(), 2)
                    print(f"Your voice level: {rms}")
                    
                    # Apply audio enhancement for testing
                    enhanced_audio = self._enhance_audio(audio)
                    enhanced_rms = audioop.rms(enhanced_audio.get_raw_data(), 2)
                    print(f"Enhanced voice level: {enhanced_rms}")
                    
                    # Calculate optimal threshold based on enhanced audio
                    optimal_threshold = max(800, min(3000, enhanced_rms * 0.5))
                    self.recognizer.energy_threshold = optimal_threshold
                    
                    print(f"\nCalibration complete!")
                    print(f"Optimal energy threshold set to: {optimal_threshold}")
                    print("Tips for better recognition:")
                    print("1. Speak at a normal volume")
                    print("2. Keep a consistent distance from the microphone")
                    print("3. Minimize background noise")
                    print("4. Speak clearly and at a normal pace")
                    
                    return True
                except sr.WaitTimeoutError:
                    print("No voice detected. Please try again.")
                    return False
                except Exception as e:
                    print(f"Error during calibration: {e}")
                    return False
        except Exception as e:
            print(f"Error accessing microphone: {e}")
            return False

# Create speech processor instance
speech_processor = SpeechProcessor()

def initialize_speech_recognition():
    """Initialize speech recognition with enhanced settings"""
    try:
        print("\n=== Initializing Enhanced Speech Recognition System ===")
        
        # Check available microphones
        print(f"Available microphones: {sr.Microphone.list_microphone_names()}")
        
        # Initial calibration
        if speech_processor.calibrate_microphone():
            print("\nSpeech recognition system initialized and calibrated successfully")
            
            # Test voice enhancement on a sample if possible
            try:
                print("\nTesting audio enhancement...")
                
                with sr.Microphone(sample_rate=16000) as source:
                    print("Please say something for audio enhancement test...")
                    audio = speech_processor.recognizer.listen(source, timeout=5, phrase_time_limit=3)
                    
                    # Get original audio metrics
                    orig_rms = audioop.rms(audio.get_raw_data(), 2)
                    
                    # Apply enhancement
                    enhanced = speech_processor._enhance_audio(audio)
                    enhanced_rms = audioop.rms(enhanced.get_raw_data(), 2)
                    
                    print(f"Original audio level: {orig_rms}")
                    print(f"Enhanced audio level: {enhanced_rms}")
                    print(f"Enhancement gain: {enhanced_rms/max(1, orig_rms):.2f}x")
                    
                    # Try recognition with enhanced audio
                    result = speech_processor._try_google_recognition(enhanced)
                    if result:
                        print(f"Enhancement test successful! Recognized: '{result}'")
                    else:
                        print("Enhancement test: No speech recognized, but audio processing is active")
            except Exception as e:
                print(f"Audio enhancement test error: {e}")
                print("This is non-critical - the system will still work")
            
            # Set sensitivity mode
            speech_processor.set_sensitivity("very_high")
            
            return True
        else:
            print("Failed to calibrate speech recognition system")
            print("Continuing with default settings")
            
            # Set fallback defaults
            speech_processor.recognizer.energy_threshold = 800
            speech_processor.set_sensitivity("very_high")
            
            return True
    except Exception as e:
        print(f"Error initializing speech recognition: {e}")
        print("Continuing with default settings")
        return True  # Return True anyway to allow application to run

class RealVoiceMovieBuddy:
    """MovieBuddy AI with enhanced voice recognition"""
    
    def __init__(self):
        """Initialize the movie buddy AI"""
        print("Initializing RealVoiceMovieBuddy with enhanced speech recognition...")
        self.movies = SAMPLE_MOVIES
        self.recommendation_history = []
        
        # Initialize enhanced speech processor
        self.speech_processor = SpeechProcessor()
        
        # Initialize text-to-speech
        if TTS_AVAILABLE:
            print("Text-to-speech is available")
        else:
            print("Warning: Text-to-speech is not available")
        
        # Initialize pygame for audio playback (optional)
        try:
            pygame.mixer.init()
            print("Audio playback initialized")
        except:
            print("Warning: Pygame mixer initialization failed. Audio playback may not work.")
    
    def listen(self):
        """Enhanced listening function with better noise handling and feedback"""
        return self.speech_processor.listen()
    
    def demo_listen(self, demo_phrase):
        """Simulate listening by returning a demo phrase"""
        print(f"DEMO MODE: Simulating voice input: '{demo_phrase}'")
        return demo_phrase
    
    def speak(self, text):
        """Speak the given text using text-to-speech"""
        global tts_engine
        
        print(f"Speaking: {text}")
        if TTS_AVAILABLE:
            try:
                # Stop any ongoing speech
                tts_engine.stop()
                
                # Split text into smaller chunks for more reliable playback
                chunks = text.split('.')
                for chunk in chunks:
                    if chunk.strip():
                        # Clean the chunk and add proper punctuation
                        clean_chunk = chunk.strip() + '.'
                        tts_engine.say(clean_chunk)
                        tts_engine.runAndWait()
                        # Small pause between chunks
                        time.sleep(0.3)
                return True
            except Exception as e:
                print(f"Error in text-to-speech: {e}")
                # Try reinitializing the engine
                try:
                    tts_engine = pyttsx3.init()
                    tts_engine.say(text)
                    tts_engine.runAndWait()
                    return True
                except Exception as e2:
                    print(f"Failed to reinitialize TTS engine: {e2}")
                    return False
        return False
    
    def process_input(self, user_input):
        """Process user input with enhanced context awareness"""
        if not user_input:
            return {
                "success": False,
                "error": "Sorry, I couldn't hear that. Could you please try again?"
            }
        
        user_input = user_input.lower().strip()
        
        # Get context from recent interactions
        context = self.speech_processor.get_context()
        
        # Check for greetings with context awareness
        greeting_keywords = ['hey', 'hello', 'hi']
        is_greeting = False
        
        # Check if this is a follow-up to a previous greeting
        was_greeted = any('moviebuddy' in prev.lower() for prev in context[-2:] if prev)
        
        for keyword in greeting_keywords:
            if keyword in user_input:
                is_greeting = True
                break
        
        movie_buddy_variations = ['moviebuddyai', 'movie buddy ai', 'movie buddy', 'moviebuddy']
        for variation in movie_buddy_variations:
            if variation in user_input:
                is_greeting = True
                break
        
        if is_greeting and not was_greeted:
            response = self.introduce()
            return {
                "success": True,
                "transcript": user_input,
                "response": response,
                "recommendations": [],
                "waiting_for_follow_up": True
            }
        
        # Process complex queries with context
        recommendations = []
        response = ""
        
        # Check for time period
        for period, years in COMPLEX_PATTERNS["time_period"].items():
            if period in user_input:
                recommendations = [movie for movie in self.movies if str(movie["year"]) in years]
                response = f"I'll recommend some great movies from the {period}. "
                break
        
        # Check for directors
        for director, names in COMPLEX_PATTERNS["directors"].items():
            if director in user_input:
                recommendations = [movie for movie in self.movies if any(name in movie.get("director", "") for name in names)]
                response = f"Here are some amazing movies directed by {names[0]}. "
                break
        
        # Check for actors
        for actor, names in COMPLEX_PATTERNS["actors"].items():
            if actor in user_input:
                recommendations = [movie for movie in self.movies if any(name in movie.get("actors", "") for name in names)]
                response = f"Here are some great movies starring {names[0]}. "
                break
        
        # Check for themes
        for theme, keywords in COMPLEX_PATTERNS["themes"].items():
            if any(keyword in user_input for keyword in keywords):
                recommendations = [movie for movie in self.movies if any(keyword in movie.get("plot", "").lower() for keyword in keywords)]
                response = f"Here are some movies about {theme}. "
                break
        
        # If no complex query matched, check for mood
        if not recommendations:
            mood_phrases = {
                'sad': ['i feel sad', 'feeling sad', 'i am sad', 'i\'m sad'],
                'happy': ['i feel happy', 'feeling happy', 'i am happy', 'i\'m happy'],
                'bad': ['i feel bad', 'feeling bad', 'i am feeling bad', 'i\'m feeling bad'],
                'bored': ['i feel bored', 'feeling bored', 'i am bored', 'i\'m bored'],
                'excited': ['i feel excited', 'feeling excited', 'i am excited', 'i\'m excited'],
                'relaxed': ['i feel relaxed', 'feeling relaxed', 'i am relaxed', 'i\'m relaxed'],
                'angry': ['i feel angry', 'feeling angry', 'i am angry', 'i\'m angry', 'i\'m mad', 'i am mad'],
                'scared': ['i feel scared', 'feeling scared', 'i am scared', 'i\'m scared', 'i\'m afraid', 'i am afraid'],
                'nostalgic': ['i feel nostalgic', 'feeling nostalgic', 'i am nostalgic', 'i\'m nostalgic', 'i miss the old days'],
                'curious': ['i feel curious', 'feeling curious', 'i am curious', 'i\'m curious', 'i want to learn'],
                'tired': ['i feel tired', 'feeling tired', 'i am tired', 'i\'m tired', 'i\'m exhausted'],
                'confused': ['i feel confused', 'feeling confused', 'i am confused', 'i\'m confused', 'i don\'t understand'],
                'romantic': ['i feel romantic', 'feeling romantic', 'i am romantic', 'i\'m romantic', 'i want romance'],
                'adventurous': ['i feel adventurous', 'feeling adventurous', 'i am adventurous', 'i\'m adventurous'],
                'thoughtful': ['i feel thoughtful', 'feeling thoughtful', 'i am thoughtful', 'i\'m thoughtful'],
                'energetic': ['i feel energetic', 'feeling energetic', 'i am energetic', 'i\'m energetic'],
                'peaceful': ['i feel peaceful', 'feeling peaceful', 'i am peaceful', 'i\'m peaceful'],
                'mysterious': ['i feel mysterious', 'feeling mysterious', 'i am mysterious', 'i\'m mysterious'],
                'inspired': ['i feel inspired', 'feeling inspired', 'i am inspired', 'i\'m inspired'],
                'playful': ['i feel playful', 'feeling playful', 'i am playful', 'i\'m playful']
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
                recommendations = self.recommend_movies(matched_mood)
                response = self.get_mood_response(matched_mood)
        
        # If still no recommendations, provide random ones
        if not recommendations:
            recommendations = random.sample(self.movies, 3)
            response = "I'm not sure what you're looking for. Here are some great movies you might enjoy. "
        
        # Add recommendations to response
        for i, movie in enumerate(recommendations[:3], 1):
            response += f"Movie {i}: {movie['title']} from {movie['year']}. "
            if movie.get('genres'):
                response += f"It's a {', '.join(movie['genres'][:2])} movie. "
        
        print(f"MovieBuddy says: {response}")
        self.speak(response)
        
        return {
            "success": True,
            "transcript": user_input,
            "response": response,
            "recommendations": recommendations[:3]
        }
    
    def introduce(self):
        """Enhanced introduction with context awareness"""
        context = self.speech_processor.get_context()
        
        # Check if we've already introduced ourselves recently
        if any('moviebuddy' in prev.lower() for prev in context[-3:] if prev):
            intro = "Yes, I'm here! How can I help you find the perfect movie?"
        else:
            intro = "Hey, I'm MovieBuddy AI! Your personal movie recommendation assistant. How can I help you today?"
        
        print(f"MovieBuddy says: {intro}")
        self.speak(intro)
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
    
    def get_mood_response(self, mood):
        """Get appropriate response for different moods"""
        responses = {
            'bad': "I'm sorry to hear you're feeling bad. Let me recommend some movies to cheer you up. ",
            'sad': "I understand you're feeling sad. Here are some movies that might help lift your spirits. ",
            'bored': "Feeling bored? I've got some exciting movies that will definitely entertain you. ",
            'angry': "I understand you're feeling angry. These intense movies might help channel that energy. ",
            'scared': "If you're feeling scared, these thrilling films might help you process those emotions. ",
            'nostalgic': "Feeling nostalgic? These classic films should satisfy your yearning for the good old days. ",
            'curious': "For someone feeling curious, these thought-provoking movies will feed your inquisitive mind. ",
            'tired': "When you're feeling tired, these light-hearted movies are perfect for relaxation. ",
            'confused': "If you're feeling confused, these mind-bending films might actually make sense to you right now. ",
            'romantic': "Feeling romantic? These love stories will warm your heart. ",
            'adventurous': "Ready for adventure? These exciting films will take you on a journey. ",
            'thoughtful': "In a thoughtful mood? These deep and meaningful movies will resonate with you. ",
            'energetic': "Feeling energetic? These action-packed movies will match your energy. ",
            'peaceful': "Want to feel peaceful? These calming movies will help you relax. ",
            'mysterious': "In the mood for mystery? These intriguing films will keep you guessing. ",
            'inspired': "Feeling inspired? These motivational movies will uplift your spirit. ",
            'playful': "Feeling playful? These fun and entertaining movies will keep you smiling. "
        }
        return responses.get(mood, f"I see you're feeling {mood}. Here are some movies that match your mood. ")

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
                <button class="demo-btn" id="demoFeelRomantic">Demo: "I feel romantic"</button>
                <button class="demo-btn" id="demoFeelAdventurous">Demo: "I feel adventurous"</button>
                <button class="demo-btn" id="demoFeelThoughtful">Demo: "I feel thoughtful"</button>
                <button class="demo-btn" id="demoFeelEnergetic">Demo: "I feel energetic"</button>
                <button class="demo-btn" id="demoFeelPeaceful">Demo: "I feel peaceful"</button>
                <button class="demo-btn" id="demoFeelMysterious">Demo: "I feel mysterious"</button>
                <button class="demo-btn" id="demoFeelInspired">Demo: "I feel inspired"</button>
                <button class="demo-btn" id="demoFeelPlayful">Demo: "I feel playful"</button>
                <button class="demo-btn" id="demo80s">Demo: "Show me movies from the 80s"</button>
                <button class="demo-btn" id="demo90s">Demo: "Show me movies from the 90s"</button>
                <button class="demo-btn" id="demoNolan">Demo: "Show me movies by Christopher Nolan"</button>
                <button class="demo-btn" id="demoHanks">Demo: "Show me movies with Tom Hanks"</button>
                <button class="demo-btn" id="demoTimeTravel">Demo: "Show me time travel movies"</button>
                <button class="demo-btn" id="demoSpace">Demo: "Show me space movies"</button>
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
            const demoFeelRomantic = document.getElementById('demoFeelRomantic');
            const demoFeelAdventurous = document.getElementById('demoFeelAdventurous');
            const demoFeelThoughtful = document.getElementById('demoFeelThoughtful');
            const demoFeelEnergetic = document.getElementById('demoFeelEnergetic');
            const demoFeelPeaceful = document.getElementById('demoFeelPeaceful');
            const demoFeelMysterious = document.getElementById('demoFeelMysterious');
            const demoFeelInspired = document.getElementById('demoFeelInspired');
            const demoFeelPlayful = document.getElementById('demoFeelPlayful');
            const demo80s = document.getElementById('demo80s');
            const demo90s = document.getElementById('demo90s');
            const demoNolan = document.getElementById('demoNolan');
            const demoHanks = document.getElementById('demoHanks');
            const demoTimeTravel = document.getElementById('demoTimeTravel');
            const demoSpace = document.getElementById('demoSpace');
            
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
            
            demoFeelRomantic.addEventListener('click', function() {
                handleDemoButton("I feel romantic");
            });
            
            demoFeelAdventurous.addEventListener('click', function() {
                handleDemoButton("I feel adventurous");
            });
            
            demoFeelThoughtful.addEventListener('click', function() {
                handleDemoButton("I feel thoughtful");
            });
            
            demoFeelEnergetic.addEventListener('click', function() {
                handleDemoButton("I feel energetic");
            });
            
            demoFeelPeaceful.addEventListener('click', function() {
                handleDemoButton("I feel peaceful");
            });
            
            demoFeelMysterious.addEventListener('click', function() {
                handleDemoButton("I feel mysterious");
            });
            
            demoFeelInspired.addEventListener('click', function() {
                handleDemoButton("I feel inspired");
            });
            
            demoFeelPlayful.addEventListener('click', function() {
                handleDemoButton("I feel playful");
            });
            
            demo80s.addEventListener('click', function() {
                handleDemoButton("Show me movies from the 80s");
            });
            
            demo90s.addEventListener('click', function() {
                handleDemoButton("Show me movies from the 90s");
            });
            
            demoNolan.addEventListener('click', function() {
                handleDemoButton("Show me movies by Christopher Nolan");
            });
            
            demoHanks.addEventListener('click', function() {
                handleDemoButton("Show me movies with Tom Hanks");
            });
            
            demoTimeTravel.addEventListener('click', function() {
                handleDemoButton("Show me time travel movies");
            });
            
            demoSpace.addEventListener('click', function() {
                handleDemoButton("Show me space movies");
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