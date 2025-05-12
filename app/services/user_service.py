"""
User Service module for MoodFlix application.
Handles user management and personalized recommendations.
"""
import os
import json
import datetime
from typing import List, Dict, Any, Optional
import hashlib
import random

from app.models.user import User
from app.models.movie import Movie
from app.core.config import settings
from app.services.recommendation_service import RecommendationService

class UserService:
    """Service for handling user management and personalized recommendations."""
    
    def __init__(self, recommendation_service: Optional[RecommendationService] = None):
        """
        Initialize the user service.
        
        Args:
            recommendation_service: Optional recommendation service to use
        """
        self.users = {}  # In-memory user storage (will be replaced with database)
        self.users_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'users.json')
        self.recommendation_service = recommendation_service or RecommendationService()
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        
        # Load users from file
        self._load_users()
    
    def _load_users(self) -> None:
        """Load users from file."""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    users_data = json.load(f)
                
                for username, user_data in users_data.items():
                    self.users[username] = User.from_dict(user_data)
                
                print(f"Loaded {len(self.users)} users from {self.users_file}")
            except Exception as e:
                print(f"Error loading users: {str(e)}")
    
    def _save_users(self) -> None:
        """Save users to file."""
        try:
            users_data = {username: user.to_dict() for username, user in self.users.items()}
            
            with open(self.users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
            
            print(f"Saved {len(self.users)} users to {self.users_file}")
        except Exception as e:
            print(f"Error saving users: {str(e)}")
    
    def get_user(self, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            username: Username to look up
            
        Returns:
            User object if found, None otherwise
        """
        return self.users.get(username)
    
    def create_user(self, username: str, email: str, password: str) -> User:
        """
        Create a new user.
        
        Args:
            username: Username for the new user
            email: Email address for the new user
            password: Password for the new user
            
        Returns:
            Newly created User object
            
        Raises:
            ValueError: If username already exists
        """
        if username in self.users:
            raise ValueError(f"Username '{username}' already exists")
        
        # Create new user
        user = User(
            username=username,
            email=email
        )
        
        # Store password hash (in a real system, use a proper password hashing library)
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user.preferences['password_hash'] = password_hash
        
        # Add to users dictionary
        self.users[username] = user
        
        # Save users to file
        self._save_users()
        
        return user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate a user.
        
        Args:
            username: Username to authenticate
            password: Password to check
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Check password hash
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        stored_hash = user.preferences.get('password_hash', '')
        
        if password_hash != stored_hash:
            return None
        
        # Update last login time
        user.last_login = datetime.datetime.now()
        self._save_users()
        
        return user
    
    def update_user(self, username: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update user information.
        
        Args:
            username: Username of the user to update
            updates: Dictionary of updates to apply
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Apply updates
        if 'email' in updates:
            user.email = updates['email']
        
        if 'preferences' in updates:
            user.preferences.update(updates['preferences'])
        
        if 'profile_picture' in updates:
            user.profile_picture = updates['profile_picture']
        
        # Save changes
        self._save_users()
        
        return user
    
    def add_to_watch_history(self, username: str, movie: Movie) -> Optional[User]:
        """
        Add a movie to a user's watch history.
        
        Args:
            username: Username of the user
            movie: Movie to add to history
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Add to watch history
        user.watch_history.append({
            'movie_title': movie.title,
            'watched_at': datetime.datetime.now().isoformat(),
            'genres': movie.genres
        })
        
        # Update genre preferences based on watched movie
        for genre in movie.genres:
            if genre in user.genre_preferences:
                user.genre_preferences[genre] += 0.1
            else:
                user.genre_preferences[genre] = 0.1
        
        # Save changes
        self._save_users()
        
        return user
    
    def add_rating(self, username: str, movie_title: str, rating: float) -> Optional[User]:
        """
        Add a movie rating for a user.
        
        Args:
            username: Username of the user
            movie_title: Title of the movie to rate
            rating: Rating value (1-5)
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Validate rating
        rating = max(1.0, min(5.0, float(rating)))
        
        # Add rating
        user.ratings[movie_title] = rating
        
        # Save changes
        self._save_users()
        
        return user
    
    def add_to_favorites(self, username: str, movie_title: str) -> Optional[User]:
        """
        Add a movie to a user's favorites.
        
        Args:
            username: Username of the user
            movie_title: Title of the movie to add
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Add to favorites if not already there
        if movie_title not in user.favorites:
            user.favorites.append(movie_title)
            
            # Save changes
            self._save_users()
        
        return user
    
    def remove_from_favorites(self, username: str, movie_title: str) -> Optional[User]:
        """
        Remove a movie from a user's favorites.
        
        Args:
            username: Username of the user
            movie_title: Title of the movie to remove
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Remove from favorites if present
        if movie_title in user.favorites:
            user.favorites.remove(movie_title)
            
            # Save changes
            self._save_users()
        
        return user
    
    def log_mood(self, username: str, mood: str) -> Optional[User]:
        """
        Log a user's mood.
        
        Args:
            username: Username of the user
            mood: Mood to log
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Add to mood history
        user.mood_history.append({
            'mood': mood,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Save changes
        self._save_users()
        
        return user
    
    def get_personalized_recommendations(self, username: str, n_recommendations: int = 5) -> List[Movie]:
        """
        Get personalized movie recommendations for a user.
        
        Args:
            username: Username of the user
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended Movie objects
        """
        user = self.get_user(username)
        
        if not user:
            return []
        
        # Get user's genre preferences
        genre_preferences = user.genre_preferences
        
        # If user has no genre preferences, use their most recent mood
        if not genre_preferences and user.mood_history:
            latest_mood = user.mood_history[-1]['mood']
            preferences = {'mood': latest_mood}
        else:
            # Convert genre preferences to a format the recommendation service can use
            preferences = {
                'genres': [genre for genre, weight in sorted(
                    genre_preferences.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:3]]  # Use top 3 genres
            }
        
        # Add user's ratings for collaborative filtering
        if user.ratings:
            preferences['ratings'] = user.ratings
        
        # Get recommendations
        recommendations = self.recommendation_service.hybrid_recommendations(preferences, n_recommendations)
        
        # Filter out movies the user has already watched
        watched_movies = [item['movie_title'] for item in user.watch_history]
        recommendations = [movie for movie in recommendations if movie.title not in watched_movies]
        
        # If we don't have enough recommendations, add some based on the user's favorites
        if len(recommendations) < n_recommendations and user.favorites:
            # Get a random favorite movie
            favorite = random.choice(user.favorites)
            
            # Get similar movies
            similar_movies = self.recommendation_service.content_based_recommendations(favorite, n_recommendations)
            
            # Add to recommendations if not already watched
            for movie in similar_movies:
                if movie.title not in watched_movies and movie not in recommendations:
                    recommendations.append(movie)
                    if len(recommendations) >= n_recommendations:
                        break
        
        return recommendations[:n_recommendations]
    
    def log_recommendation_feedback(self, username: str, movie_title: str, feedback: str) -> Optional[User]:
        """
        Log feedback on a recommendation.
        
        Args:
            username: Username of the user
            movie_title: Title of the recommended movie
            feedback: Feedback on the recommendation (e.g., 'liked', 'disliked', 'neutral')
            
        Returns:
            Updated User object if successful, None otherwise
        """
        user = self.get_user(username)
        
        if not user:
            return None
        
        # Add feedback to recommendations_feedback
        user.recommendations_feedback.append({
            'movie_title': movie_title,
            'feedback': feedback,
            'timestamp': datetime.datetime.now().isoformat()
        })
        
        # Update genre preferences based on feedback
        # This would require looking up the movie's genres
        
        # Save changes
        self._save_users()
        
        return user
