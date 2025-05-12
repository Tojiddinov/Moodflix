"""
Mood Service module for MoodFlix application.
Handles mood detection and preference extraction from user input.
"""
import re
from typing import Dict, Any, List
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from app.core.config import settings

# Download required NLTK resources if not already downloaded
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class MoodService:
    """Service for handling mood detection and preference extraction."""
    
    def __init__(self):
        """Initialize mood detection service."""
        # Define valid categories for detection
        self.genres = [
            "action", "comedy", "drama", "horror", "sci-fi", "romance", "thriller", 
            "documentary", "animation", "fantasy", "adventure", "crime", "family", 
            "mystery", "war", "history", "biography", "music", "sport"
        ]
        
        self.moods = [
            "happy", "sad", "excited", "relaxed", "scared", "inspired", "tense", 
            "romantic", "curious", "nostalgic", "emotional", "calm", "mysterious", 
            "adventurous", "funny", "uplifting", "dark", "thoughtful", "hopeful",
            "bored", "angry", "confused", "tired", "peaceful", "playful"
        ]
        
        self.eras = [
            "80s", "90s", "2000s", "2010s", "2020s", "classic", "modern", "1950s", 
            "1960s", "1970s", "old", "new", "recent", "vintage", "retro"
        ]
        
        # Define keyword mappings for better detection
        self.genre_keywords = {
            'action': ['action', 'fight', 'explosion', 'chase', 'adventure', 'exciting', 'fast-paced'],
            'comedy': ['comedy', 'funny', 'humor', 'laugh', 'hilarious', 'amusing', 'comical'],
            'drama': ['drama', 'emotional', 'intense', 'powerful', 'dramatic', 'serious', 'moving'],
            'horror': ['horror', 'scary', 'frightening', 'terror', 'spooky', 'creepy', 'disturbing'],
            'sci-fi': ['sci-fi', 'science fiction', 'futuristic', 'space', 'technology', 'alien', 'robot'],
            'thriller': ['thriller', 'suspense', 'mystery', 'intense', 'psychological', 'gripping', 'tense'],
            'romance': ['romance', 'love', 'romantic', 'relationship', 'passion', 'heartfelt', 'emotional'],
            'fantasy': ['fantasy', 'magical', 'mythical', 'supernatural', 'enchanted', 'fairy tale', 'wizards'],
            'adventure': ['adventure', 'journey', 'quest', 'exploration', 'discovery', 'exciting', 'expedition'],
            'documentary': ['documentary', 'real', 'true story', 'factual', 'historical', 'educational', 'informative'],
            'animation': ['animation', 'animated', 'cartoon', 'pixar', 'disney', 'drawings', 'cgi'],
            'crime': ['crime', 'detective', 'police', 'investigation', 'murder', 'heist', 'gangster'],
            'family': ['family', 'kids', 'children', 'all ages', 'wholesome', 'clean', 'parental'],
            'mystery': ['mystery', 'detective', 'puzzle', 'clue', 'enigma', 'whodunit', 'suspense']
        }
        
        # Define mood to genre mappings
        self.mood_genre_associations = settings.MOOD_MAPPINGS
        
        # Define common phrases for mood detection
        self.mood_phrases = {
            'happy': ['feel happy', 'feeling happy', 'in a good mood', 'feeling good', 'feel cheerful', 'feeling joyful'],
            'sad': ['feel sad', 'feeling sad', 'feeling down', 'feel depressed', 'feeling blue', 'feel gloomy'],
            'excited': ['feel excited', 'feeling excited', 'feel thrilled', 'feeling pumped', 'feel energetic'],
            'bored': ['feel bored', 'feeling bored', 'nothing to do', 'need something interesting'],
            'angry': ['feel angry', 'feeling angry', 'feel mad', 'feeling upset', 'feel furious'],
            'scared': ['feel scared', 'feeling scared', 'feel afraid', 'feeling frightened', 'feel terrified'],
            'nostalgic': ['feel nostalgic', 'feeling nostalgic', 'reminiscing', 'good old days', 'childhood memories'],
            'curious': ['feel curious', 'feeling curious', 'want to learn', 'interested in', 'want to discover'],
            'tired': ['feel tired', 'feeling tired', 'feel exhausted', 'feeling sleepy', 'need to relax'],
            'confused': ['feel confused', 'feeling confused', 'feel lost', 'not sure what to watch']
        }
        
        # Load stopwords
        self.stop_words = set(stopwords.words('english'))
    
    def extract_preferences(self, user_input: str) -> Dict[str, Any]:
        """
        Extract user preferences from input text with enhanced natural language understanding.
        
        Args:
            user_input: User input text
            
        Returns:
            Dictionary of user preferences
        """
        # Convert to lowercase for easier matching
        text = user_input.lower()
        
        # Initialize preferences dictionary
        preferences = {
            'genres': [],
            'mood': None,
            'era': None,
            'actor': None,
            'director': None
        }
        
        # Extract mood using phrase detection
        for mood, phrases in self.mood_phrases.items():
            for phrase in phrases:
                if phrase in text:
                    preferences['mood'] = mood
                    break
            if preferences['mood']:
                break
        
        # If no mood phrases found, try single word detection
        if not preferences['mood']:
            words = word_tokenize(text)
            for word in words:
                if word in self.moods:
                    preferences['mood'] = word
                    break
        
        # Extract genres
        for genre in self.genres:
            if genre in text:
                if genre not in preferences['genres']:
                    preferences['genres'].append(genre)
        
        # Use genre keywords for better detection
        for genre, keywords in self.genre_keywords.items():
            for keyword in keywords:
                if keyword in text and genre not in preferences['genres']:
                    preferences['genres'].append(genre)
                    break
        
        # Extract era
        for era in self.eras:
            if era in text:
                preferences['era'] = era
                break
        
        # Extract actor (simple pattern matching)
        actor_match = re.search(r'(?:with|starring|actor|actress|featuring)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', user_input)
        if actor_match:
            preferences['actor'] = actor_match.group(1)
        
        # Extract director (simple pattern matching)
        director_match = re.search(r'(?:directed by|director)\s+([A-Z][a-z]+\s+[A-Z][a-z]+)', user_input)
        if director_match:
            preferences['director'] = director_match.group(1)
        
        # If mood is detected but no genres, map mood to genres
        if preferences['mood'] and not preferences['genres']:
            mood_genres = self.mood_genre_associations.get(preferences['mood'], [])
            preferences['genres'] = [genre.lower() for genre in mood_genres]
        
        # Clean up preferences (remove empty values)
        return {k: v for k, v in preferences.items() if v}
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Simple sentiment analysis to determine the overall mood of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Detected mood
        """
        # This is a very simple implementation
        # In a production system, you would use a proper NLP model
        
        # Define positive and negative word lists
        positive_words = [
            'happy', 'good', 'great', 'excellent', 'wonderful', 'amazing', 'fantastic',
            'love', 'enjoy', 'like', 'positive', 'fun', 'exciting', 'awesome'
        ]
        
        negative_words = [
            'sad', 'bad', 'terrible', 'awful', 'horrible', 'depressing', 'depressed',
            'hate', 'dislike', 'negative', 'boring', 'tired', 'angry', 'upset'
        ]
        
        # Tokenize text
        words = word_tokenize(text.lower())
        
        # Count positive and negative words
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        # Determine sentiment
        if positive_count > negative_count:
            return 'happy'
        elif negative_count > positive_count:
            return 'sad'
        else:
            return 'neutral'
    
    def extract_complex_query(self, text: str) -> Dict[str, Any]:
        """
        Extract complex query parameters from text.
        
        Args:
            text: User input text
            
        Returns:
            Dictionary of extracted parameters
        """
        # Define patterns for complex queries
        time_period_patterns = {
            '80s': r'(?:80s|1980s|eighties)',
            '90s': r'(?:90s|1990s|nineties)',
            '2000s': r'(?:2000s|two thousands)',
            'classic': r'(?:classic|old|vintage|retro)',
            'modern': r'(?:modern|recent|new|latest)'
        }
        
        theme_patterns = {
            'space': r'(?:space|sci-fi|science fiction|alien|future)',
            'crime': r'(?:crime|detective|mystery|thriller|murder)',
            'love': r'(?:love|romance|romantic|relationship)',
            'family': r'(?:family|kids|children|parental)'
        }
        
        result = {}
        
        # Check for time periods
        for period, pattern in time_period_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                result['era'] = period
                break
        
        # Check for themes
        for theme, pattern in theme_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                if 'themes' not in result:
                    result['themes'] = []
                result['themes'].append(theme)
        
        return result
