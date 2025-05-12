"""
User model for MoodFlix application.
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import datetime

@dataclass
class User:
    """User data model with enhanced personalization features."""
    
    username: str
    email: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)
    preferences: Dict[str, Any] = field(default_factory=dict)
    watch_history: List[Dict[str, Any]] = field(default_factory=list)
    favorites: List[str] = field(default_factory=list)
    ratings: Dict[str, float] = field(default_factory=dict)  # Movie title -> rating (1-5)
    genre_preferences: Dict[str, float] = field(default_factory=dict)  # Genre -> weight
    mood_history: List[Dict[str, Any]] = field(default_factory=list)  # Track mood over time
    recommendations_feedback: List[Dict[str, Any]] = field(default_factory=list)  # Track feedback on recommendations
    last_login: Optional[datetime.datetime] = None
    profile_picture: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert User object to dictionary.
        
        Returns:
            Dictionary representation of the User
        """
        result = {
            'username': self.username,
            'email': self.email,
            'created_at': self.created_at.isoformat(),
            'preferences': self.preferences,
            'watch_history': self.watch_history,
            'favorites': self.favorites,
            'ratings': self.ratings,
            'genre_preferences': self.genre_preferences,
            'mood_history': self.mood_history,
            'recommendations_feedback': self.recommendations_feedback
        }
        
        # Add optional fields if they exist
        if self.last_login:
            result['last_login'] = self.last_login.isoformat()
        if self.profile_picture:
            result['profile_picture'] = self.profile_picture
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        """
        Create User object from dictionary.
        
        Args:
            data: Dictionary containing user data
            
        Returns:
            User object
        """
        # Handle datetime fields
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            created_at = datetime.datetime.fromisoformat(created_at)
        else:
            created_at = datetime.datetime.now()
        
        last_login = data.get('last_login')
        if isinstance(last_login, str):
            last_login = datetime.datetime.fromisoformat(last_login)
        
        # Create the user object with all fields
        return cls(
            username=data.get('username', ''),
            email=data.get('email', ''),
            created_at=created_at,
            preferences=data.get('preferences', {}),
            watch_history=data.get('watch_history', []),
            favorites=data.get('favorites', []),
            ratings=data.get('ratings', {}),
            genre_preferences=data.get('genre_preferences', {}),
            mood_history=data.get('mood_history', []),
            recommendations_feedback=data.get('recommendations_feedback', []),
            last_login=last_login,
            profile_picture=data.get('profile_picture')
        )
    
    def add_to_watch_history(self, movie_title: str) -> None:
        """
        Add a movie to the user's watch history.
        
        Args:
            movie_title: Title of the movie to add
        """
        self.watch_history.append({
            'movie': movie_title,
            'watched_at': datetime.datetime.now().isoformat()
        })
    
    def add_to_favorites(self, movie_title: str) -> None:
        """
        Add a movie to the user's favorites.
        
        Args:
            movie_title: Title of the movie to add
        """
        if movie_title not in self.favorites:
            self.favorites.append(movie_title)
    
    def remove_from_favorites(self, movie_title: str) -> None:
        """
        Remove a movie from the user's favorites.
        
        Args:
            movie_title: Title of the movie to remove
        """
        if movie_title in self.favorites:
            self.favorites.remove(movie_title)
    
    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """
        Update user preferences.
        
        Args:
            new_preferences: New preferences to update
        """
        self.preferences.update(new_preferences)
