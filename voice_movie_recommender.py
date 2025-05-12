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
import speech_recognition as sr
from pydub import AudioSegment
import io
import numpy as np
import warnings
import csv
import pyttsx3
from gtts import gTTS
import pygame
warnings.filterwarnings('ignore')

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
    def __init__(self, web_context=False):
        """Initialize the voice movie recommender
        
        Args:
            web_context (bool): Whether the recommender is being used in a web context
                If True, won't attempt to use audio output and will optimize for web responses
        """
        self.movies = []
        self.web_context = web_context
        self.user_sessions = {}
        self.active_conversations = {}
        
        # Define valid categories for detection
        self.genres = ["action", "comedy", "drama", "horror", "sci-fi", "romance", "thriller", 
                      "documentary", "animation", "fantasy", "adventure", "crime", "family", 
                      "mystery", "war", "history", "biography", "music", "sport"]
        
        self.moods = ["happy", "sad", "excited", "relaxed", "scared", "inspired", "tense", 
                     "romantic", "curious", "nostalgic", "emotional", "calm", "mysterious", 
                     "adventurous", "funny", "uplifting", "dark", "thoughtful", "hopeful"]
        
        self.eras = ["80s", "90s", "2000s", "2010s", "2020s", "classic", "modern", "1950s", 
                    "1960s", "1970s", "old", "new", "recent", "vintage", "retro"]
        
        self.genre_keywords = {
            'action': ['action', 'fight', 'explosion', 'chase', 'adventure'],
            'comedy': ['comedy', 'funny', 'humor', 'laugh', 'hilarious'],
            'drama': ['drama', 'emotional', 'intense', 'powerful', 'dramatic'],
            'horror': ['horror', 'scary', 'frightening', 'terror', 'spooky'],
            'sci-fi': ['sci-fi', 'science fiction', 'futuristic', 'space', 'technology'],
            'thriller': ['thriller', 'suspense', 'mystery', 'intense', 'psychological'],
            'romance': ['romance', 'love', 'romantic', 'relationship', 'passion'],
            'fantasy': ['fantasy', 'magical', 'mythical', 'supernatural', 'enchanted'],
            'adventure': ['adventure', 'journey', 'quest', 'exploration', 'discovery'],
            'documentary': ['documentary', 'real', 'true story', 'factual', 'historical']
        }
        
        self.mood_theme_associations = {
            'happy': ['comedy', 'romance', 'adventure', 'uplifting', 'friendship'],
            'sad': ['drama', 'emotional', 'tragedy', 'loss', 'melancholy'],
            'excited': ['action', 'adventure', 'thriller', 'suspense', 'discovery'],
            'relaxed': ['comedy', 'romance', 'slice of life', 'feel-good', 'nature'],
            'tense': ['thriller', 'horror', 'mystery', 'psychological', 'suspense'],
            'nostalgic': ['coming of age', 'childhood', 'retro', 'memory', 'history'],
            'inspired': ['biography', 'success', 'achievement', 'motivation', 'triumph'],
            'thoughtful': ['philosophy', 'psychology', 'meaning', 'identity', 'reality']
        }
        
        # Load movie database
        print("Loading movie database...")
        self.load_movie_database()
        
        # Initialize speech recognition if not in web context
        if not web_context:
            self.recognizer = sr.Recognizer()
            # Initialize text-to-speech
            self.engine = pyttsx3.init()
            # Set properties (optional)
            self.engine.setProperty('rate', 150)    # Speed of speech
            self.engine.setProperty('volume', 0.9)  # Volume (0-1)
            # Initialize pygame for audio playback
            pygame.mixer.init()
        
        # Default conversation state
        self.conversation_active = False
        self.is_listening = False
        self.is_processing = False
        self.is_speaking = False
        
        # Store conversation history
        self.conversation_history = []
        
        # For web integration
        self.last_response_time = 0
        self.response_timeout = 30  # seconds
        
        # For intelligent follow-up handling
        self.last_recommendations = None
        self.last_query_type = None
        self.last_preferences = None
        
    def load_movie_database(self):
        """Load movie data from CSV file"""
        try:
            # Initialize empty lists
            self.movies = []
            self.genres = set()
            self.actors = set()
            self.directors = set()
            
            # Print current working directory for debugging
            import os
            print(f"Current working directory: {os.getcwd()}")
            csv_path = 'main_data_updated.csv'
            print(f"Attempting to load: {os.path.abspath(csv_path)}")
            
            if not os.path.exists(csv_path):
                print(f"ERROR: File {csv_path} does not exist!")
                print("Falling back to sample database...")
                self.movies = self._create_sample_database()
                return
            
            # Load movie data from CSV
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        # Clean and process title
                        title = row.get('movie_title', '').strip()
                        if not title:
                            continue
                        
                        # Try to get year from title first (e.g., "Movie Name (2000)")
                        year = None
                        title_year_match = re.search(r'\((\d{4})\)', title)
                        if title_year_match:
                            year = int(title_year_match.group(1))
                            title = re.sub(r'\s*\(\d{4}\)', '', title).strip()
                        
                        # If still no year, try to extract it from the title
                        if not year:
                            year_match = re.search(r'(?:19|20)\d{2}', title)
                            if year_match:
                                year = int(year_match.group(0))
                                title = title.replace(year_match.group(0), '').strip()
                        
                        # Process genres
                        genres = [g.strip() for g in row.get('genres', '').split('|') if g.strip()]
                        self.genres.update(genres)
                        
                        # Process actors
                        actors = []
                        for i in range(1, 4):
                            actor = row.get(f'actor_{i}_name', '').strip()
                            if actor:
                                actors.append(actor)
                                self.actors.add(actor)
                        
                        # Process director
                        director = row.get('director_name', '').strip()
                        if director:
                            self.directors.add(director)
                            directors = [director]
                        else:
                            directors = []
                        
                        # Process mood
                        mood = [m.strip() for m in row.get('mood', '').split('|') if m.strip()]
                        
                        # Generate plot description
                        plot = f"A {', '.join(genres).lower()} movie"
                        if directors:
                            plot += f" directed by {directors[0]}"
                        if actors:
                            plot += f", starring {', '.join(actors[:-1])}{' and ' if len(actors) > 1 else ''}{actors[-1]}"
                        plot += "."
                        
                        # Create movie object
                        movie = {
                            'title': title,
                            'year': year or 2000,  # Default to 2000 if no year found
                            'genres': genres,
                            'actors': actors,
                            'directors': directors,
                            'mood': mood,
                            'themes': genres.copy(),  # Using genres as themes for now
                            'plot': plot
                        }
                        
                        self.movies.append(movie)
                        
                    except Exception as e:
                        print(f"Error processing movie: {str(e)}")
                        continue
            
            # Convert sets to sorted lists
            self.genres = sorted(list(self.genres))
            self.actors = sorted(list(self.actors))
            self.directors = sorted(list(self.directors))
            
            print(f"Loaded {len(self.movies)} movies from main_data_updated.csv")
            
        except Exception as e:
            print(f"Error loading movie database: {str(e)}")
            self.movies = []
    
    def _load_movie_database(self):
        """Load the movie database from main_data_updated.csv with enhanced data extraction"""
        try:
            # Load the dataset
            data = pd.read_csv('main_data_updated.csv')
            print(f"Loaded {len(data)} movies from main_data_updated.csv")
            
            # Convert to our internal format for processing
            movies = []
            for idx, row in data.iterrows():
                # Initialize movie data structure
                title = row.get('movie_title', '').strip()
                year = None
                genres = []
                mood = None
                plot = ''
                actors = []
                directors = []
                themes = []
                
                # 1. Extract actors
                for col in ['actor_1_name', 'actor_2_name', 'actor_3_name']:
                    if col in row and not pd.isna(row[col]) and row[col] != '':
                        actors.append(row[col])
                
                # 2. Extract director
                if 'director_name' in row and not pd.isna(row['director_name']) and row['director_name'] != '':
                    directors.append(row['director_name'])
                
                # 3. Extract and clean genres
                if 'genres' in row and not pd.isna(row['genres']) and row['genres'] != '':
                    # Split genres by '|' or comma and handle spaces
                    if '|' in row['genres']:
                        raw_genres = row['genres'].lower().split('|')
                    else:
                        raw_genres = row['genres'].lower().split(',')
                    
                    # Clean and normalize genres
                    for g in raw_genres:
                        g = g.strip()
                        if not g:
                            continue
                            
                        # Map genres to our standard set
                        if g in ['action', 'adventure', 'animation', 'comedy', 'crime', 'documentary', 
                                'drama', 'family', 'fantasy', 'history', 'horror', 'music', 'mystery',
                                'romance', 'sci-fi', 'science fiction', 'thriller', 'war', 'western']:
                            # Direct mapping
                            if g == 'science fiction':
                                genres.append('sci-fi')
                            else:
                                genres.append(g)
                        elif 'sci' in g or 'science' in g:
                            genres.append('sci-fi')
                        elif 'rom' in g or 'love' in g:
                            genres.append('romance')
                        elif 'horror' in g or 'scary' in g:
                            genres.append('horror')
                        elif 'thrill' in g or 'suspense' in g:
                            genres.append('thriller')
                        elif 'comed' in g or 'funny' in g:
                            genres.append('comedy')
                        elif 'action' in g:
                            genres.append('action')
                        elif 'drama' in g:
                            genres.append('drama')
                        elif 'document' in g:
                            genres.append('documentary')
                        elif 'family' in g or 'kids' in g or 'children' in g:
                            genres.append('family')
                        elif 'fantacy' in g or 'fantasy' in g:
                            genres.append('fantasy')
                
                # Use drama as fallback genre if none found
                if not genres:
                    genres = ['drama']  
                
                # 4. Extract plot
                if 'comb' in row and not pd.isna(row['comb']):
                    plot = row['comb']
                else:
                    plot = title
                
                # 5. Extract mood from plot if possible
                plot_lower = plot.lower()
                if 'mood' in row and not pd.isna(row['mood']):
                    mood = row['mood'].lower()
                elif any(word in plot_lower for word in ['happy', 'cheerful', 'uplifting', 'humor', 'comedy', 'laugh']):
                    mood = 'happy'
                elif any(word in plot_lower for word in ['sad', 'tragedy', 'emotional', 'sorrow', 'heart-breaking']):
                    mood = 'sad'
                elif any(word in plot_lower for word in ['exciting', 'thrilling', 'action', 'adventure', 'adrenaline']):
                    mood = 'excited'
                elif any(word in plot_lower for word in ['scared', 'scary', 'fear', 'horror', 'terror', 'frightening']):
                    mood = 'scared'
                elif any(word in plot_lower for word in ['romantic', 'love', 'romance', 'affection']):
                    mood = 'romantic'
                elif any(word in plot_lower for word in ['mystery', 'curious', 'investigation', 'puzzle']):
                    mood = 'curious'
                
                # 6. Extract year from movie title using regex
                year_patterns = [
                    r'\((\d{4})\)$',  # Year in parentheses at end
                    r'\((\d{4})\)',    # Year in parentheses anywhere
                    r'(\d{4})$',       # Year at end
                    r'(\b\d{4}\b)'     # Year as a whole word
                ]
                
                for pattern in year_patterns:
                    match = re.search(pattern, title)
                    if match:
                        try:
                            year = int(match.group(1))
                            # Validate the year is reasonable (between 1900 and current year)
                            import datetime
                            current_year = datetime.datetime.now().year
                            if 1900 <= year <= current_year:
                                # Remove year from title
                                title = re.sub(pattern, '', title).strip()
                                break
                        except (ValueError, TypeError):
                            pass
                
                # 7. If no year found, estimate based on other criteria
                if year is None:
                    # Use fallback estimation based on directors and genres
                    director_names = [d.lower() for d in directors]
                    if any(name in ['steven spielberg', 'george lucas', 'james cameron'] for name in director_names) and any(g in ['sci-fi', 'action'] for g in genres):
                        # Likely to be from 70s-90s
                        year = 1990
                    elif any(keyword in plot_lower for keyword in 
                              ['superhero', 'marvel', 'dc', 'comic']):
                        # Likely to be 2000s or later
                        year = 2010
                    else:
                        # Default to 2000 as an average estimate
                        year = 2000
                
                # 8. Extract themes from plot
                theme_keywords = {
                    "friendship": ["friend", "buddy", "companion", "brotherhood", "sisterhood", "camaraderie"],
                    "love": ["love", "romance", "relationship", "romantic", "passion", "affection"],
                    "family": ["family", "families", "parents", "siblings", "children"],
                    "revenge": ["revenge", "vengeance", "payback", "justice", "retaliation"],
                    "coming of age": ["coming of age", "grow up", "adolescence", "youth", "teen", "young adult"],
                    "survival": ["survival", "survive", "against odds", "struggle", "hardship"],
                    "war": ["war", "battle", "conflict", "military", "soldier", "combat", "fight"],
                    "sports": ["sports", "game", "competition", "athletic"]
                }
                
                for theme, keywords in theme_keywords.items():
                    if any(keyword in plot_lower for keyword in keywords):
                        themes.append(theme)
                
                # Create movie object
                movie = {
                    "title": title,
                    "year": year,
                    "genres": genres,
                    "mood": mood,
                    "movie_id": row.get('movie_id') if 'movie_id' in row else idx,
                    "plot": plot,
                    "actors": actors,
                    "directors": directors,
                    "themes": themes
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
    
    def extract_preferences(self, user_input):
        """Extract user preferences from input text with enhanced natural language understanding"""
        preferences = {
            'genres': [],
            'mood': None,
            'era': None,
            'actors': [],
            'directors': [],
            'themes': [],
            'title': None
        }
        
        try:
            # Convert input to lowercase for better matching
            text = user_input.lower()
            
            # Extract mood with expanded patterns and context
            mood_patterns = {
                'happy': ['happy', 'cheerful', 'joyful', 'upbeat', 'good mood', 'great mood', 'feeling good', 'excited'],
                'sad': ['sad', 'down', 'depressed', 'blue', 'bad mood', 'feeling low', 'unhappy', 'heartbroken'],
                'excited': ['excited', 'thrilled', 'pumped', 'energetic', 'cant wait', "can't wait", 'hyped'],
                'relaxed': ['relaxed', 'calm', 'peaceful', 'chill', 'mellow', 'easy-going', 'laid back'],
                'romantic': ['romantic', 'love', 'date night', 'romance', 'in love', 'feeling romantic'],
                'scared': ['scared', 'frightened', 'horror', 'spooky', 'creepy', 'terrified', 'fear'],
                'stressed': ['stressed', 'anxious', 'worried', 'tense', 'overwhelmed', 'pressure'],
                'bored': ['bored', 'nothing to do', 'uninterested', 'dull', 'monotonous'],
                'nostalgic': ['nostalgic', 'missing', 'remembering', 'memories', 'old times', 'childhood'],
                'inspired': ['inspired', 'motivated', 'determined', 'ambitious', 'ready to conquer'],
                'curious': ['curious', 'intrigued', 'interested', 'fascinated', 'want to learn'],
                'thoughtful': ['thoughtful', 'contemplative', 'philosophical', 'deep thinking']
            }
            
            # First try to find explicit mood statements
            mood_phrases = [
                (r"i(?:'m| am) (?:feeling |in a )?([\w-]+)", 1),  # "I'm feeling happy" or "I am sad"
                (r"i feel ([\w-]+)", 1),                          # "I feel excited"
                (r"(?:in|having) a ([\w-]+) mood", 1),           # "in a good mood"
                (r"(?:make me|feeling) ([\w-]+)", 1),            # "make me happy" or "feeling down"
                (r"had a ([\w-]+) day", 1),                      # "had a bad day"
                (r"need something ([\w-]+)", 1),                 # "need something uplifting"
                (r"want to feel ([\w-]+)", 1)                    # "want to feel better"
            ]
            
            for pattern, group in mood_phrases:
                match = re.search(pattern, text)
                if match:
                    mood_word = match.group(group)
                    # Find which mood category this word belongs to
                    for mood, patterns in mood_patterns.items():
                        if any(p in mood_word for p in patterns):
                            preferences['mood'] = mood
                            break
                    if preferences['mood']:
                        break
            
            # If no explicit mood found, look for mood indicators in the whole text
            if not preferences['mood']:
                for mood, patterns in mood_patterns.items():
                    if any(pattern in text for pattern in patterns):
                        preferences['mood'] = mood
                        break
            
            # Extract genres with context
            genre_patterns = {
                'action': ['action', 'adventure', 'exciting', 'thrilling', 'explosive', 'fast-paced'],
                'comedy': ['comedy', 'funny', 'humorous', 'laugh', 'hilarious', 'comedic', 'light-hearted'],
                'drama': ['drama', 'dramatic', 'serious', 'intense', 'emotional', 'powerful'],
                'horror': ['horror', 'scary', 'frightening', 'terror', 'creepy', 'spooky'],
                'romance': ['romance', 'romantic', 'love story', 'love', 'relationship', 'dating'],
                'thriller': ['thriller', 'suspense', 'mysterious', 'intense', 'gripping', 'psychological'],
                'documentary': ['documentary', 'real', 'true story', 'educational', 'informative'],
                'animation': ['animation', 'animated', 'cartoon', 'pixar', 'disney', 'anime'],
                'sci-fi': ['sci-fi', 'science fiction', 'space', 'future', 'technological', 'dystopian'],
                'fantasy': ['fantasy', 'magical', 'fairy tale', 'mythical', 'supernatural', 'enchanted']
            }
            
            # Look for genre preferences in various formats
            genre_phrases = [
                r"(?:like|love|enjoy|want|prefer) (?:to watch |watching )?([\w\s-]+) (?:movies|films)",
                r"(?:show|give|recommend) me (?:some |a )?([\w\s-]+) (?:movies|films)",
                r"(?:in the mood for|looking for) (?:some |a )?([\w\s-]+) (?:movies|films)",
                r"(?:something|anything) ([\w\s-]+)",
                r"(?:fan of|into) ([\w\s-]+)"
            ]
            
            for pattern in genre_phrases:
                matches = re.finditer(pattern, text)
                for match in matches:
                    genre_text = match.group(1)
                    for genre, patterns in genre_patterns.items():
                        if any(p in genre_text for p in patterns):
                            if genre not in preferences['genres']:
                                preferences['genres'].append(genre)
            
            # Extract era with expanded patterns
            era_patterns = {
                '2020s': ['2020s', 'very recent', 'latest', 'new', 'current', 'modern day', 'contemporary'],
                '2010s': ['2010s', 'recent', 'modern', 'last decade'],
                '2000s': ['2000s', '00s', 'early 2000s', 'turn of the century'],
                '1990s': ['90s', '1990s', 'nineties', 'late 20th century'],
                '1980s': ['80s', '1980s', 'eighties', 'retro'],
                '1970s': ['70s', '1970s', 'seventies', 'disco era'],
                '1960s': ['60s', '1960s', 'sixties', 'classic'],
                'classic': ['classic', 'old', 'vintage', 'retro', 'golden age', 'timeless']
            }
            
            # Look for era preferences in various formats
            era_phrases = [
                r"(?:from|in) the ([\w\s]+)",
                r"([\w\s]+) (?:era|period|time)",
                r"(?:old|classic|modern|recent) ([\w\s]+)",
                r"(?:made|released) (?:in|during) the ([\w\s]+)"
            ]
            
            for pattern in era_phrases:
                matches = re.finditer(pattern, text)
                for match in matches:
                    era_text = match.group(1)
                    for era, patterns in era_patterns.items():
                        if any(p in era_text for p in patterns):
                            preferences['era'] = era
                            break
                    if preferences['era']:
                        break
            
            # Extract specific title if mentioned
            title_patterns = [
                r'like ["\'](.*?)["\']',
                r'similar to ["\'](.*?)["\']',
                r'(?:like|similar to) (.*?)(?:\s|$)',
                r'(?:watch|seen) ["\'](.*?)["\']',
                r'(?:recommend|suggest) (?:something like |movies like )(.*?)(?:\s|$)'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, text)
                if match:
                    title = match.group(1).strip()
                    # Clean up common words that might be captured
                    cleanup_words = ['movie', 'film', 'something', 'anything', 'please', 'thanks']
                    for word in cleanup_words:
                        title = re.sub(r'\b' + word + r'\b', '', title, flags=re.IGNORECASE).strip()
                    if title:
                        preferences['title'] = title
                        break
            
            # Extract actors and directors from the database with context
            for person in self.actors + self.directors:
                person_lower = person.lower()
                # Look for various ways to mention actors/directors
                if any(pattern.format(person_lower) in text for pattern in [
                    'with {}',
                    'starring {}',
                    'featuring {}',
                    'by {}',
                    'directed by {}',
                    '{} movie',
                    '{} film'
                ]):
                    if person in self.actors:
                        preferences['actors'].append(person)
                    if person in self.directors:
                        preferences['directors'].append(person)
            
            # Extract themes with context
            theme_patterns = {
                'friendship': ['friendship', 'friends', 'buddy', 'companionship'],
                'family': ['family', 'families', 'parents', 'siblings', 'children'],
                'love': ['love', 'romance', 'relationship', 'romantic', 'passion', 'affection'],
                'adventure': ['adventure', 'journey', 'quest', 'exploration'],
                'mystery': ['mystery', 'puzzle', 'detective', 'investigation'],
                'survival': ['survival', 'survive', 'against odds', 'struggle', 'hardship'],
                'revenge': ['revenge', 'vengeance', 'payback', 'justice', 'retaliation'],
                'coming of age': ['coming of age', 'grow up', 'adolescence', 'youth', 'teen', 'young adult'],
                'war': ['war', 'battle', 'conflict', 'military', 'soldier', 'combat', 'fight'],
                'sports': ['sports', 'game', 'competition', 'athletic']
            }
            
            for theme, patterns in theme_patterns.items():
                if any(pattern in text for pattern in patterns):
                    preferences['themes'].append(theme)
            
            return preferences
            
        except Exception as e:
            print(f"Error extracting preferences: {str(e)}")
            return preferences
    
    def recommend_movies(self, user_preferences, n_recommendations=5):
        """Recommend movies based on user preferences with enhanced scoring"""
        try:
            # Initialize scores for all movies
            movie_scores = []
            
            # Get the search query if any
            search_query = user_preferences.get('title', '').lower() if user_preferences.get('title') else ''
            
            # Define mood opposites for recommendation with expanded options
            mood_opposites = {
                'sad': ['happy', 'uplifting', 'inspiring', 'joyful', 'cheerful', 'heartwarming', 'hopeful'],
                'scared': ['funny', 'light-hearted', 'happy', 'joyful', 'inspiring', 'uplifting'],
                'stressed': ['relaxing', 'calm', 'peaceful', 'soothing', 'meditative', 'gentle'],
                'angry': ['calm', 'funny', 'uplifting', 'peaceful', 'soothing', 'inspiring'],
                'tired': ['exciting', 'energetic', 'funny', 'thrilling', 'adventurous', 'dynamic'],
                'bored': ['exciting', 'thrilling', 'adventurous', 'action-packed', 'surprising', 'mind-bending'],
                'anxious': ['calming', 'peaceful', 'gentle', 'uplifting', 'heartwarming', 'inspiring'],
                'lonely': ['heartwarming', 'uplifting', 'inspiring', 'social', 'friendship', 'family'],
                'nostalgic': ['classic', 'timeless', 'retro', 'feel-good', 'memorable', 'iconic']
            }
            
            # Enhanced genre recommendations for moods
            mood_genres = {
                'sad': ['comedy', 'animation', 'family', 'adventure', 'feel-good', 'musical'],
                'scared': ['comedy', 'animation', 'family', 'adventure', 'fantasy', 'romance'],
                'stressed': ['comedy', 'animation', 'family', 'documentary', 'nature', 'music'],
                'angry': ['comedy', 'animation', 'family', 'romance', 'fantasy', 'adventure'],
                'tired': ['action', 'adventure', 'comedy', 'sci-fi', 'superhero', 'fantasy'],
                'bored': ['action', 'thriller', 'adventure', 'sci-fi', 'mystery', 'crime'],
                'anxious': ['comedy', 'animation', 'family', 'documentary', 'nature', 'music'],
                'lonely': ['comedy', 'romance', 'drama', 'family', 'friendship', 'feel-good'],
                'nostalgic': ['classic', 'drama', 'romance', 'musical', 'family', 'adventure']
            }
            
            # Define theme weights for better scoring
            theme_weights = {
                'friendship': 1.2,
                'love': 1.1,
                'family': 1.15,
                'hope': 1.25,
                'triumph': 1.2,
                'redemption': 1.15,
                'justice': 1.1,
                'courage': 1.2,
                'discovery': 1.15,
                'growth': 1.2
            }
            
            # Convert mood to target moods
            target_moods = []
            if user_preferences.get('mood'):
                user_mood = user_preferences['mood'][0] if isinstance(user_preferences['mood'], list) else user_preferences['mood']
                if user_mood in mood_opposites:
                    target_moods = mood_opposites[user_mood]
                else:
                    target_moods = [user_mood]
            
            # Add genre preferences based on mood
            if user_preferences.get('mood') and not user_preferences.get('genres'):
                user_mood = user_preferences['mood'][0] if isinstance(user_preferences['mood'], list) else user_preferences['mood']
                if user_mood in mood_genres:
                    user_preferences['genres'] = mood_genres[user_mood]
            
            for movie in self.movies:
                score = 0
                
                # Title match with high priority
                if search_query:
                    if search_query == movie['title'].lower():
                        score += 100  # Exact match
                    elif search_query in movie['title'].lower():
                        score += 50   # Partial match
                    elif any(word in movie['title'].lower() for word in search_query.split()):
                        score += 25   # Word match
                
                # Genre matching with weighted scoring
                if user_preferences.get('genres'):
                    genre_matches = sum(1 for genre in user_preferences['genres'] if genre.lower() in [g.lower() for g in movie['genres']])
                    score += genre_matches * 15
                    
                    # Bonus for matching multiple genres
                    if genre_matches > 1:
                        score += (genre_matches - 1) * 5
                
                # Actor matching with role importance
                if user_preferences.get('actors'):
                    for actor in user_preferences['actors']:
                        if actor in movie['actors']:
                            # Higher score for leading actors
                            actor_index = movie['actors'].index(actor)
                            score += max(20 - actor_index * 5, 5)  # Decreasing score based on billing order
                
                # Director matching with bonus for acclaimed directors
                if user_preferences.get('directors'):
                    director_matches = sum(1 for director in user_preferences['directors'] if director in movie['directors'])
                    score += director_matches * 20
                    
                    # Bonus for acclaimed directors
                    acclaimed_directors = ['Steven Spielberg', 'Martin Scorsese', 'Christopher Nolan', 'Quentin Tarantino']
                    if any(director in acclaimed_directors for director in movie['directors']):
                        score += 10
                
                # Mood matching with sophisticated handling
                if target_moods:
                    movie_mood = movie['mood'] if isinstance(movie['mood'], list) else [movie['mood']]
                    mood_matches = sum(1 for mood in target_moods if any(m and mood.lower() in m.lower() for m in movie_mood))
                    score += mood_matches * 25
                
                # Theme matching with weights
                if movie.get('themes'):
                    for theme in movie['themes']:
                        if theme.lower() in theme_weights:
                            score *= theme_weights[theme.lower()]
                
                # Era matching with year proximity
                if user_preferences.get('era'):
                    year = movie['year']
                    era_score = 0
                    for era in (user_preferences['era'] if isinstance(user_preferences['era'], list) else [user_preferences['era']]):
                        if (era == '2020s' and year >= 2020) or \
                           (era == '2010s' and 2010 <= year < 2020) or \
                           (era == '2000s' and 2000 <= year < 2010) or \
                           (era == '1990s' and 1990 <= year < 2000) or \
                           (era == '1980s' and 1980 <= year < 1990) or \
                           (era == '1970s' and 1970 <= year < 1980) or \
                           (era == '1960s' and 1960 <= year < 1970) or \
                           (era == 'classic' and year < 1960):
                            era_score = 15
                            # Bonus for being in the middle of the era
                            if era != 'classic':
                                decade_start = int(era[:4])
                                if decade_start <= year < decade_start + 5:
                                    era_score += 5
                    score += era_score
                
                # Special bonuses based on user mood and preferences
                if target_moods:
                    # Award-winning movies bonus for certain moods
                    if any(mood in ['sad', 'stressed', 'lonely'] for mood in target_moods):
                        if any(keyword in str(movie['plot']).lower() for keyword in 
                              ['award', 'oscar', 'golden globe', 'acclaimed', 'masterpiece']):
                            score += 15
                    
                    # Feel-good movie bonus for sad moods
                    if 'sad' in target_moods:
                        if any(keyword in str(movie['plot']).lower() for keyword in 
                              ['heartwarming', 'inspiring', 'uplifting', 'feel-good', 'hope']):
                            score += 20
                    
                    # Exciting movie bonus for bored moods
                    if 'bored' in target_moods:
                        if any(keyword in str(movie['plot']).lower() for keyword in 
                              ['thrilling', 'exciting', 'action-packed', 'adventure', 'suspense']):
                            score += 20
                
                # Add the movie and its score if it has any points
                if score > 0:
                    movie_scores.append((movie, score))
            
            # Sort movies by score and return top N
            movie_scores.sort(key=lambda x: x[1], reverse=True)
            recommended_movies = [movie for movie, _ in movie_scores[:n_recommendations]]
            
            # Store recommendations for follow-up questions
            self.last_recommendations = recommended_movies
            
            return recommended_movies if recommended_movies else None
            
        except Exception as e:
            print(f"Error recommending movies: {str(e)}")
            return None
    
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
        recommendations = self.recommend_movies(user_preferences=self.user_preferences)
        
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

    def speak(self, text):
        """Convert text to speech with minimal terminal output"""
        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_filename = fp.name
                
            # Clean up the text
            text = text.replace('\n', ' ').strip()
            text = re.sub(r'\s+', ' ', text)
            
            # Remove emojis and special characters
            text = re.sub(r'[^\x00-\x7F]+', '', text)
            
            # Generate and play speech
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.set_volume(0.9)
            pygame.mixer.music.play()
            
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            
            # Clean up
            pygame.mixer.music.unload()
            os.unlink(temp_filename)
            
        except Exception:
            # Fallback to pyttsx3 without output
            try:
                self.engine.setProperty('rate', 150)
                self.engine.setProperty('volume', 0.9)
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass
    
    def listen(self):
        """Enhanced listening function with minimal output"""
        with sr.Microphone() as source:
            try:
                # Adjust for ambient noise silently
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Listen for audio input
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=15)
                
                # Convert speech to text
                text = self.recognizer.recognize_google(audio)
                return text.lower()
                
            except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError):
                return None
            except Exception:
                return None

    def introduce(self):
        """Simplified introduction without terminal output"""
        introduction = "Hey, I'm MovieBuddy AI! Your personal movie recommendation assistant. How can I help you today?"
        self.speak(introduction.strip())
        return introduction

    def voice_interaction(self, user_input=None):
        """Handle voice-based movie recommendations with enhanced real-time interaction"""
        try:
            # Initialize conversation state if not already set
            if not hasattr(self, 'conversation_active'):
                self.conversation_active = True
                self.is_listening = False
                self.is_processing = False
                self.is_speaking = False
                self.session_id = str(random.randint(10000, 99999))
                self.conversation_history = []
            
            # Get user input either from parameter or by listening
            if user_input is None:
                # Process user input
                self.is_listening = True
                user_input = self.listen()
                self.is_listening = False
            
            if not user_input:
                return {"success": False, "error": "I couldn't hear anything. Please try again."}
            
            # Add user input to conversation history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Check for initial greeting
            greeting_phrases = ['hey', 'hello', 'hi', 'hey there', 'hello there', 'hi there', 'greetings', 'howdy']
            if any(user_input.lower().strip() == phrase for phrase in greeting_phrases):
                self.is_speaking = True
                response = self.introduce()
                self.is_speaking = False
                
                # Add response to conversation history
                self.conversation_history.append({"role": "assistant", "content": response})
                
                return {
                    "success": True, 
                    "transcript": user_input,
                    "response": response,
                    "recommendations": [],
                    "session_id": self.session_id,
                    "waiting_for_follow_up": True,
                    "conversation_history": self.conversation_history
                }
            
            # Check for help requests
            help_phrases = ['help', 'what can you do', 'how does this work', 'instructions', 'guide me']
            if any(phrase in user_input.lower() for phrase in help_phrases):
                help_response = "I'm MovieBuddy AI, your personal movie recommendation assistant. You can ask me to recommend movies based on genre, mood, actors, or directors. For example, try saying 'I want to watch an action movie' or 'I'm feeling sad, what should I watch?' or 'Show me movies with Tom Hanks'."
                
                # Add response to conversation history
                self.conversation_history.append({"role": "assistant", "content": help_response})
                
                return {
                    "success": True,
                    "transcript": user_input,
                    "response": help_response,
                    "session_id": self.session_id,
                    "conversation_history": self.conversation_history
                }
            
            # Check for emotional state queries
            mood_phrases = [
                'i feel sad', 'feeling sad', 'i am sad', 'i\'m sad',
                'i feel happy', 'feeling happy', 'i am happy', 'i\'m happy',
                'i feel bad', 'feeling bad', 'i am feeling bad', 'i\'m feeling bad',
                'i feel good', 'feeling good', 'i am feeling good', 'i\'m feeling good',
                'i feel bored', 'feeling bored', 'i am bored', 'i\'m bored',
                'i feel excited', 'feeling excited', 'i am excited', 'i\'m excited',
                'i feel anxious', 'feeling anxious', 'i am anxious', 'i\'m anxious',
                'i feel tired', 'feeling tired', 'i am tired', 'i\'m tired',
                'i feel lonely', 'feeling lonely', 'i am lonely', 'i\'m lonely'
            ]
            
            matched_mood = None
            for phrase in mood_phrases:
                if phrase in user_input.lower():
                    matched_mood = phrase.split()[-1]  # Extract the mood word
                    break
            
            if matched_mood:
                # Process mood-based request
                self.is_processing = True
                
                # Create preferences with emphasis on mood
                preferences = {
                    'mood': matched_mood,
                    'genres': []
                }
                
                # Map common moods to suitable movie types
                mood_mapping = {
                    'sad': ['drama', 'emotional', 'romance'],
                    'happy': ['comedy', 'family', 'adventure'],
                    'bad': ['comedy', 'feel-good', 'uplifting'],
                    'good': ['action', 'adventure', 'comedy'],
                    'bored': ['thriller', 'action', 'adventure'],
                    'excited': ['action', 'thriller', 'sci-fi'],
                    'anxious': ['comedy', 'animation', 'family'],
                    'tired': ['comedy', 'romance', 'relaxing'],
                    'lonely': ['drama', 'romance', 'comedy']
                }
                
                if matched_mood in mood_mapping:
                    preferences['genres'] = mood_mapping[matched_mood]
                
                # Generate recommendations
                recommendations = self.recommend_movies(preferences, n_recommendations=3)
                self.is_processing = False
                
                # Generate response
                self.is_speaking = True
                if recommendations:
                    if matched_mood == 'bad':
                        response = f"I'm sorry to hear you're feeling {matched_mood}. Let me recommend some movies to cheer you up. "
                    elif matched_mood == 'sad':
                        response = f"I understand you're feeling {matched_mood}. Here are some movies that might help lift your spirits. "
                    elif matched_mood == 'bored':
                        response = f"Feeling {matched_mood}? I've got some exciting movies that will definitely entertain you. "
                    else:
                        response = f"I see you're feeling {matched_mood}. Here are some movies that match your mood. "
                    
                    # Add recommendations
                    for i, movie in enumerate(recommendations, 1):
                        response += f"Movie {i}: {movie['title']} from {movie['year']}. "
                        if movie.get('genres'):
                            response += f"It's a {', '.join(movie['genres'][:2])} movie. "
                    
                    # Only speak in non-web contexts
                    if not hasattr(self, 'web_context') or not self.web_context:
                        self.speak(response)
                else:
                    response = f"I understand you're feeling {matched_mood}, but I couldn't find suitable recommendations. Would you like to try a different type of movie?"
                    if not hasattr(self, 'web_context') or not self.web_context:
                        self.speak(response)
                self.is_speaking = False
                
                # Add response to conversation history
                self.conversation_history.append({"role": "assistant", "content": response})
                
                return {
                    "success": True,
                    "transcript": user_input,
                    "response": response,
                    "recommendations": self._serialize_recommendations(recommendations) if recommendations else [],
                    "preferences": preferences,
                    "session_id": self.session_id,
                    "state": self.get_conversation_state(),
                    "conversation_history": self.conversation_history
                }
            
            # Process normal movie request
            self.is_processing = True
            preferences = self.extract_preferences(user_input)
            recommendations = self.recommend_movies(preferences)
            self.is_processing = False
            
            # Generate response
            self.is_speaking = True
            if recommendations:
                response = self._format_movie_recommendations(recommendations, preferences)
                # Only speak in non-web contexts
                if not hasattr(self, 'web_context') or not self.web_context:
                    self.speak(response)
            else:
                response = self._get_no_recommendations_response(preferences)
                if not hasattr(self, 'web_context') or not self.web_context:
                    self.speak(response)
            self.is_speaking = False
            
            # Add response to conversation history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            return {
                "success": True,
                "transcript": user_input,
                "response": response,
                "recommendations": self._serialize_recommendations(recommendations) if recommendations else [],
                "preferences": preferences,
                "session_id": self.session_id,
                "state": self.get_conversation_state(),
                "conversation_history": self.conversation_history
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_conversation_state(self, session_id=None):
        """Get the current state of the conversation
        
        Args:
            session_id (str, optional): The session ID to get state for. If None, returns global state.
            
        Returns:
            dict: The current conversation state
        """
        if session_id and session_id in self.active_conversations:
            # Return session-specific state
            return self.active_conversations[session_id].copy()
        else:
            # Return global state
            return {
                "active": getattr(self, 'conversation_active', False),
                "listening": getattr(self, 'is_listening', False),
                "processing": getattr(self, 'is_processing', False),
                "speaking": getattr(self, 'is_speaking', False)
            }

    def _format_movie_recommendations(self, recommendations, preferences):
        """Format movie recommendations without visual formatting"""
        # Start with a simple opener
        if preferences.get('mood'):
            response = f"Based on your {preferences['mood']} mood, here are some movies you might enjoy. "
        elif preferences.get('genres'):
            response = f"Here are some {', '.join(preferences['genres'])} movies you might like. "
        else:
            response = "Here are some movies I think you'll enjoy. "

        # Add recommendations
        for i, movie in enumerate(recommendations, 1):
            response += f"Movie {i}: {movie['title']} from {movie['year']}. "
            if movie.get('genres'):
                response += f"It's a {', '.join(movie['genres'][:2])} movie. "
            if movie.get('directors'):
                response += f"Directed by {', '.join(movie['directors'][:2])}. "
            if movie.get('actors'):
                response += f"Starring {', '.join(movie['actors'][:2])}. "
            if movie.get('plot'):
                response += f"{movie['plot'][:150]}. "

        # Add a follow-up prompt to encourage conversation
        followup_prompts = [
            "\n\nWould you like more details about any of these movies?",
            "\n\nIs there a specific one you'd like to know more about?",
            "\n\nDo any of these interest you? I can tell you more about them.",
            "\n\nAsk me for more similar movies if these don't quite match what you're looking for."
        ]
        import random
        response += random.choice(followup_prompts)
        
        return response
        
    def _format_voice_recommendations(self, recommendations, preferences):
        """Format movie recommendations for voice response (more concise)"""
        # Start with a simple opener
        if preferences.get('mood'):
            response = f"For your {preferences['mood']} mood, I recommend: "
        elif preferences.get('genres'):
            response = f"Here are some {', '.join(preferences['genres'][:1])} recommendations: "
        else:
            response = "I recommend these movies: "

        # Add recommendations (more concise for voice)
        for i, movie in enumerate(recommendations[:3], 1):  # Limit to top 3 for voice
            response += f"{movie['title']} ({movie['year']})"
            if i < len(recommendations[:3]):
                response += ", "
            
        # Add simple follow-up prompt
        response += ". Would you like more details about any of these?"
        return response
        
    def _serialize_recommendations(self, recommendations):
        """Convert movie recommendations to a serializable format for JSON"""
        if not recommendations:
            return []
            
        serialized = []
        for movie in recommendations:
            # Create a simplified version of the movie object
            serialized_movie = {
                'title': movie.get('title', ''),
                'year': movie.get('year', ''),
                'genres': movie.get('genres', []),
                'directors': movie.get('directors', []),
                'actors': movie.get('actors', []),
                'plot': movie.get('plot', '')[:200]  # Limit plot length
            }
            serialized.append(serialized_movie)
            
        return serialized

    def _get_acknowledgment(self, preferences):
        """Generate simple acknowledgment"""
        if preferences.get('mood'):
            return f"I understand you're feeling {preferences['mood']}. Let me find something suitable."
        elif preferences.get('genres'):
            return f"Looking for {', '.join(preferences['genres'])} movies. One moment."
        elif preferences.get('actors'):
            return f"I'll find movies with {', '.join(preferences['actors'])}."
        elif preferences.get('title'):
            return f"Looking for movies similar to {preferences['title']}."
        else:
            return "Let me find some movies for you."

    def _get_no_recommendations_response(self, preferences):
        """Simple response for no recommendations"""
        return "I couldn't find exact matches. Could you tell me more about what you're looking for?"

    def process_audio_file(self, file_path):
        """Process an audio file and return the transcription"""
        try:
            # Transcribe the audio file
            transcript = self.transcribe_audio(file_path)
            if not transcript:
                return None
            return transcript.strip()
        except Exception as e:
            print(f"Error processing audio file: {str(e)}")
            return None

    def handle_web_request(self, action, data=None):
        """Handle web interface requests separately from voice interaction
        
        Args:
            action (str): The action to perform ('start', 'stop', 'process_input', etc.)
            data (dict): Data associated with the request
            
        Returns:
            dict: Response with relevant data based on the action
        """
        try:
            # Set web context for this session
            self.web_context = True
            
            # Initialize data structure if needed
            if data is None:
                data = {}
                
            # Get or generate session ID
            session_id = data.get('session_id', str(random.randint(10000, 99999)))
            
            # Initialize user session if it doesn't exist
            if session_id not in self.user_sessions:
                self.user_sessions[session_id] = {
                    'conversation_history': [],
                    'last_recommendations': None,
                    'last_query_type': None,
                    'last_preferences': None,
                    'created_at': time.time(),
                    'last_activity': time.time()
                }
            
            # Update last activity time
            self.user_sessions[session_id]['last_activity'] = time.time()
                
            if action == 'start':
                # Initialize new conversation
                if session_id not in self.active_conversations:
                    self.active_conversations[session_id] = {
                        'active': True,
                        'listening': False,
                        'processing': False,
                        'speaking': False
                    }
                
                # Generate welcome message
                welcome_message = "Hi there! I'm MovieBuddy AI. How can I help you find the perfect movie today?"
                
                # Add to conversation history
                self.user_sessions[session_id]['conversation_history'].append({
                    "role": "assistant",
                    "content": welcome_message,
                    "timestamp": time.time()
                })
                
                return {
                    "success": True,
                    "message": welcome_message,
                    "session_id": session_id,
                    "state": self.get_conversation_state(session_id)
                }
                
            elif action == 'stop':
                # End conversation for this session
                if session_id in self.active_conversations:
                    self.active_conversations[session_id]['active'] = False
                    
                return {
                    "success": True,
                    "message": "Conversation ended",
                    "session_id": session_id,
                    "state": self.get_conversation_state(session_id)
                }
                
            elif action == 'get_state':
                # Return current conversation state for this session
                return {
                    "success": True,
                    "session_id": session_id,
                    "state": self.get_conversation_state(session_id)
                }
                
            elif action == 'get_history':
                # Return conversation history for this session
                if session_id in self.user_sessions:
                    return {
                        "success": True,
                        "session_id": session_id,
                        "conversation_history": self.user_sessions[session_id]['conversation_history']
                    }
                else:
                    return {
                        "success": False,
                        "error": "Session not found"
                    }
                
            elif action == 'process_input':
                # Set processing state for this session
                if session_id in self.active_conversations:
                    self.active_conversations[session_id]['processing'] = True
                
                # Process text input
                if data and 'text' in data:
                    user_input = data['text']
                    input_type = 'text'
                # Process audio file input
                elif data and 'file_path' in data:
                    user_input = self.process_audio_file(data['file_path'])
                    input_type = 'voice'
                    if not user_input:
                        if session_id in self.active_conversations:
                            self.active_conversations[session_id]['processing'] = False
                        return {"success": False, "error": "Could not transcribe audio", "session_id": session_id}
                else:
                    if session_id in self.active_conversations:
                        self.active_conversations[session_id]['processing'] = False
                    return {"success": False, "error": "No input provided", "session_id": session_id}
                
                # Store the source of the request
                source = data.get('source', 'unknown')
                
                # Add user input to conversation history
                self.user_sessions[session_id]['conversation_history'].append({
                    "role": "user",
                    "content": user_input,
                    "timestamp": time.time(),
                    "source": source,
                    "input_type": input_type
                })
                
                # Check for follow-up queries
                is_follow_up = self._is_follow_up_query(user_input, session_id)
                
                # Handle follow-up queries differently
                if is_follow_up and self.user_sessions[session_id]['last_recommendations']:
                    # This is a follow-up question about previous recommendations
                    response, recommendations = self._handle_follow_up_query(
                        user_input, 
                        self.user_sessions[session_id]['last_recommendations'],
                        self.user_sessions[session_id]['last_preferences']
                    )
                else:
                    # Normal query flow
                    # Extract preferences from user input
                    preferences = self.extract_preferences(user_input)
                    
                    # Check for special requests like help, greetings
                    special_response = self._check_special_requests(user_input, session_id)
                    if special_response:
                        # Add response to conversation history
                        self.user_sessions[session_id]['conversation_history'].append({
                            "role": "assistant", 
                            "content": special_response,
                            "timestamp": time.time()
                        })
                        
                        # Reset processing state
                        if session_id in self.active_conversations:
                            self.active_conversations[session_id]['processing'] = False
                            
                        # Return the special response
                        return {
                            "success": True,
                            "transcript": user_input,
                            "response": special_response,
                            "session_id": session_id,
                            "state": self.get_conversation_state(session_id),
                            "conversation_history": self.user_sessions[session_id]['conversation_history']
                        }
                    
                    # Generate movie recommendations
                    recommendations = self.recommend_movies(preferences)
                    
                    # Save for potential follow-up questions
                    self.user_sessions[session_id]['last_recommendations'] = recommendations
                    self.user_sessions[session_id]['last_preferences'] = preferences
                    self.user_sessions[session_id]['last_query_type'] = 'recommendation'
                    
                    # Generate response based on input and recommendations
                    if recommendations:
                        if input_type == 'text':
                            response = self._format_movie_recommendations(recommendations, preferences)
                        else:  # voice input gets a more concise response
                            response = self._format_voice_recommendations(recommendations, preferences)
                    else:
                        response = self._get_no_recommendations_response(preferences)
                
                # Add response to conversation history
                self.user_sessions[session_id]['conversation_history'].append({
                    "role": "assistant", 
                    "content": response,
                    "timestamp": time.time()
                })
                
                # Reset processing state
                if session_id in self.active_conversations:
                    self.active_conversations[session_id]['processing'] = False
                
                # Return comprehensive result
                result = {
                    "success": True,
                    "transcript": user_input,
                    "response": response,
                    "recommendations": self._serialize_recommendations(recommendations) if recommendations else [],
                    "preferences": preferences if 'preferences' in locals() else {},
                    "session_id": session_id,
                    "source": source,
                    "input_type": input_type,
                    "is_follow_up": is_follow_up,
                    "state": self.get_conversation_state(session_id),
                    "conversation_history": self.user_sessions[session_id]['conversation_history']
                }
                
                return result
                
            elif action == 'speak':
                if not data or 'text' not in data:
                    return {"success": False, "error": "No text to speak", "session_id": session_id}
                
                # Set speaking state
                if session_id in self.active_conversations:
                    self.active_conversations[session_id]['speaking'] = True
                
                # Only actually speak if not in web context
                if not self.web_context:
                    self.speak(data['text'])
                
                # Reset speaking state
                if session_id in self.active_conversations:
                    self.active_conversations[session_id]['speaking'] = False
                
                return {
                    "success": True,
                    "message": "Speech completed",
                    "session_id": session_id,
                    "state": self.get_conversation_state(session_id)
                }
                
            elif action == 'clear_history':
                # Clear conversation history for this session
                if session_id in self.user_sessions:
                    self.user_sessions[session_id]['conversation_history'] = []
                    self.user_sessions[session_id]['last_recommendations'] = None
                    self.user_sessions[session_id]['last_query_type'] = None
                    self.user_sessions[session_id]['last_preferences'] = None
                
                return {
                    "success": True,
                    "message": "Conversation history cleared",
                    "session_id": session_id
                }
            
            else:
                return {"success": False, "error": "Unknown action"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def main_web(self):
        """Initialize the recommender for web use"""
        try:
            print("MovieBuddyAI initialized for web interface")
            return {"success": True, "message": "MovieBuddyAI ready"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _is_follow_up_query(self, user_input, session_id=None):
        """Determine if the user query is a follow-up to a previous recommendation
        
        Args:
            user_input (str): The user's input text
            session_id (str, optional): The session ID to check history for
            
        Returns:
            bool: True if the query is a follow-up, False otherwise
        """
        # Simple follow-up indicators
        follow_up_phrases = [
            'tell me more', 'more about', 'more details', 'details about', 
            'first one', 'second one', 'third one', 'fourth one', 'fifth one',
            'the first', 'the second', 'the third', 'the fourth', 'the fifth',
            'which one', 'who stars in', 'who directed', 'plot of', 'synopsis',
            'what is it about', 'what year', 'similar to these', 'more like these',
            'watch it', 'stream it', 'where can i watch'
        ]
        
        # Check if input contains any follow-up phrases
        if any(phrase in user_input.lower() for phrase in follow_up_phrases):
            # Check if there are previous recommendations to follow up on
            if session_id and session_id in self.user_sessions:
                return self.user_sessions[session_id]['last_recommendations'] is not None
            else:
                return self.last_recommendations is not None
        
        return False
    
    def _handle_follow_up_query(self, user_input, last_recommendations, last_preferences):
        """Handle follow-up queries about previous recommendations
        
        Args:
            user_input (str): The user's input text
            last_recommendations (list): The previous movie recommendations
            last_preferences (dict): The previous user preferences
            
        Returns:
            tuple: (response, filtered_recommendations)
        """
        # Initialize response
        response = ""
        filtered_recommendations = last_recommendations
        
        # Check for requests about specific movies
        movie_indices = {
            'first': 0, 'second': 1, 'third': 2, 'fourth': 3, 'fifth': 4,
            'one': 0, 'two': 1, 'three': 2, 'four': 3, 'five': 4,
            '1': 0, '2': 1, '3': 2, '4': 3, '5': 4
        }
        
        # Check for references to specific movies by index
        selected_index = None
        for key, index in movie_indices.items():
            if f"the {key}" in user_input.lower() or f"{key} one" in user_input.lower():
                if 0 <= index < len(last_recommendations):
                    selected_index = index
                    break
        
        # If a specific movie is referenced
        if selected_index is not None:
            movie = last_recommendations[selected_index]
            
            # Check what aspect they're asking about
            if any(phrase in user_input.lower() for phrase in ['plot', 'about', 'synopsis', 'what is']):
                response = f"Here's more about {movie['title']}: {movie.get('plot', 'No plot available.')} "
            elif any(phrase in user_input.lower() for phrase in ['who stars', 'actor', 'cast']):
                actors = movie.get('actors', [])
                if actors:
                    response = f"{movie['title']} stars {', '.join(actors)}. "
                else:
                    response = f"I don't have cast information for {movie['title']}. "
            elif any(phrase in user_input.lower() for phrase in ['director', 'directed', 'who made']):
                directors = movie.get('directors', [])
                if directors:
                    response = f"{movie['title']} was directed by {', '.join(directors)}. "
                else:
                    response = f"I don't have director information for {movie['title']}. "
            elif any(phrase in user_input.lower() for phrase in ['where can i watch', 'stream', 'watch']):
                response = f"You might be able to stream {movie['title']} on popular platforms like Netflix, Amazon Prime, or Disney+. I recommend checking JustWatch.com for current streaming options."
            else:
                # General request for more information
                response = f"Here's more about {movie['title']} ({movie.get('year', 'unknown year')}): "
                if movie.get('genres'):
                    response += f"It's a {', '.join(movie['genres'][:3])} movie. "
                if movie.get('directors'):
                    response += f"Directed by {', '.join(movie['directors'][:2])}. "
                if movie.get('actors'):
                    response += f"Starring {', '.join(movie['actors'][:3])}. "
                if movie.get('plot'):
                    response += f"{movie['plot']} "
            
            return response, [movie]
        
        # Check for requests for similar movies
        if any(phrase in user_input.lower() for phrase in ['similar', 'more like', 'like these']):
            # Get more recommendations using the same preferences
            more_recommendations = self.recommend_movies(last_preferences, n_recommendations=5)
            
            # Filter out movies already recommended
            new_recommendations = [movie for movie in more_recommendations 
                                if movie['title'] not in [rec['title'] for rec in last_recommendations]]
            
            if new_recommendations:
                response = "Here are more movies similar to my previous recommendations: "
                for i, movie in enumerate(new_recommendations[:3], 1):
                    response += f"{i}. {movie['title']} ({movie.get('year', '')}). "
                    if movie.get('genres'):
                        response += f"It's a {', '.join(movie['genres'][:2])} movie. "
                
                return response, new_recommendations
        
        # Default response if no specific follow-up was detected
        response = "Was there something specific you wanted to know about these recommendations?"
        return response, last_recommendations
    
    def _check_special_requests(self, user_input, session_id=None):
        """Check for special requests like help, greetings, etc.
        
        Args:
            user_input (str): The user's input text
            session_id (str, optional): The session ID
            
        Returns:
            str or None: Special response if applicable, None otherwise
        """
        user_input_lower = user_input.lower()
        
        # Check for greetings
        greeting_phrases = ['hello', 'hi', 'hey', 'greetings', 'howdy', 'good morning', 'good afternoon', 'good evening']
        if any(user_input_lower.strip() == phrase for phrase in greeting_phrases):
            return "Hello! I'm MovieBuddy AI. How can I help you find the perfect movie today?"
        
        # Check for help requests
        help_phrases = ['help', 'how do you work', 'what can you do', 'instructions', 'guide me', 'how to use']
        if any(phrase in user_input_lower for phrase in help_phrases):
            return "I'm MovieBuddy AI, your movie recommendation assistant. You can ask me questions like: 'Recommend action movies from the 90s', 'I'm feeling sad, what should I watch?', or 'Show me movies with Tom Hanks'. I can also answer follow-up questions about my recommendations."
        
        # Check for thank you messages
        thanks_phrases = ['thank you', 'thanks', 'appreciated', 'that helps', 'helpful']
        if any(phrase in user_input_lower for phrase in thanks_phrases) and len(user_input_lower.split()) < 5:
            return "You're welcome! Is there anything else you'd like to know about movies?"
        
        # Check for goodbye messages
        bye_phrases = ['bye', 'goodbye', 'see you', 'farewell', 'that\'s all', 'exit']
        if any(phrase in user_input_lower for phrase in bye_phrases) and len(user_input_lower.split()) < 5:
            return "Goodbye! Feel free to come back when you need more movie recommendations!"
        
        # No special request detected
        return None
        
    def main_voice(self):
        """Initialize the recommender for voice use"""
        try:
            print("MovieBuddyAI initialized for voice interface")
            return self.voice_interaction()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_pending_response(self, session_id):
        """Retrieve any pending asynchronous responses for a session"""
        if session_id in self.pending_responses and self.pending_responses[session_id]:
            return self.pending_responses[session_id].pop(0)
        return None
    
    def get_conversation_history(self, session_id):
        """Get the conversation history for a specific session"""
        if session_id in self.user_sessions:
            return self.user_sessions[session_id]['conversation_history']
        return []
    
    def add_pending_response(self, session_id, response):
        """Add an asynchronous response to be delivered later"""
        if session_id not in self.pending_responses:
            self.pending_responses[session_id] = []
        self.pending_responses[session_id].append(response)

def main():
    """Main function to run the voice movie recommender"""
    # Initialize recommender
    recommender = VoiceMovieRecommender()
    
    # Print welcome message
    print("Welcome to the Voice Movie Recommender!")
    print("I can help you find movies based on your preferences.")
    print("Just speak naturally about what kind of movie you're looking for.")
    print("For example, you can say things like:")
    print("  - 'I'm looking for action movies from the 90s'")
    print("  - 'Recommend me movies with Tom Hanks'")
    print("  - 'I'm feeling sad and need a good comedy'")
    print("\nPress Ctrl+C to exit.")
    
    # Start conversation loop
    try:
        recommender.voice_interaction()
    except KeyboardInterrupt:
        print("\nExiting Voice Movie Recommender. Thank you for using our service!")
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Exiting Voice Movie Recommender.")

if __name__ == "__main__":
    main() 