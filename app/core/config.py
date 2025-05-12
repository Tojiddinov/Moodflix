"""
Configuration module for MoodFlix application.
Loads environment variables and provides configuration settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Settings:
    """Application settings loaded from environment variables."""
    
    # Application settings
    PROJECT_NAME: str = "MoodFlix"
    VERSION: str = "2.0.0"
    DESCRIPTION: str = "Emotion-Driven Movie Recommendation System"
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default_secret_key_change_in_production")
    
    # API Keys
    DEEPGRAM_API_KEY: Optional[str] = os.getenv("DEEPGRAM_API_KEY")
    TMDB_API_KEY: Optional[str] = os.getenv("TMDB_API_KEY")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///moodflix.db")
    
    # Speech Recognition settings
    SPEECH_RECOGNITION_TIMEOUT: int = int(os.getenv("SPEECH_RECOGNITION_TIMEOUT", "5"))
    SPEECH_RECOGNITION_ENERGY_THRESHOLD: int = int(os.getenv("SPEECH_RECOGNITION_ENERGY_THRESHOLD", "4000"))
    
    # Voice settings
    TTS_RATE: int = int(os.getenv("TTS_RATE", "150"))
    TTS_VOLUME: float = float(os.getenv("TTS_VOLUME", "0.9"))
    
    # Movie data settings
    MOVIE_DATA_PATH: str = os.getenv("MOVIE_DATA_PATH", "main_data_updated.csv")
    
    # Mood mappings
    MOOD_MAPPINGS: Dict[str, list] = {
        "sad": ["Drama", "Romance"],
        "happy": ["Comedy", "Animation", "Adventure"],
        "bad": ["Comedy", "Adventure", "Animation"],
        "excited": ["Action", "Adventure", "Sci-Fi"],
        "bored": ["Thriller", "Mystery", "Action"],
        "angry": ["Action", "Crime", "Thriller"],
        "scared": ["Horror", "Thriller", "Mystery"],
        "nostalgic": ["Drama", "Family", "Music"],
        "curious": ["Documentary", "Mystery", "Sci-Fi"],
        "tired": ["Comedy", "Animation", "Family"],
        "confused": ["Mystery", "Thriller", "Sci-Fi"],
        "relaxed": ["Comedy", "Romance", "Animation"],
        "peaceful": ["Animation", "Romance", "Drama"],
        "mysterious": ["Mystery", "Thriller", "Sci-Fi"],
        "inspired": ["Drama", "Adventure", "Biography"],
        "playful": ["Animation", "Comedy", "Family"]
    }

    def validate(self) -> None:
        """Validate that critical configuration values are set."""
        missing_keys = []
        
        if not self.SECRET_KEY or self.SECRET_KEY == "default_secret_key_change_in_production":
            missing_keys.append("SECRET_KEY")
        
        if not self.DEEPGRAM_API_KEY:
            missing_keys.append("DEEPGRAM_API_KEY")
            
        if not self.TMDB_API_KEY:
            missing_keys.append("TMDB_API_KEY")
        
        if missing_keys:
            warning = (
                f"Missing required environment variables: {', '.join(missing_keys)}. "
                f"Please check your .env file or environment settings."
            )
            print(f"\033[93mWARNING: {warning}\033[0m")  # Yellow warning text

# Create a settings object for importing in other modules
settings = Settings()
