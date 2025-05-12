"""
TMDB Service module for MoodFlix application.
Handles integration with The Movie Database (TMDB) API.
"""
import requests
import os
from typing import List, Dict, Any, Optional
import time
from functools import lru_cache

from app.core.config import settings
from app.models.movie import Movie

class TMDBService:
    """Service for handling TMDB API integration."""
    
    def __init__(self):
        """Initialize the TMDB service."""
        self.api_key = settings.TMDB_API_KEY
        self.base_url = "https://api.themoviedb.org/3"
        self.image_base_url = "https://image.tmdb.org/t/p/w500"
        self.request_count = 0
        self.last_request_time = 0
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Make a request to the TMDB API with rate limiting.
        
        Args:
            endpoint: API endpoint to request
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        # Basic rate limiting (TMDB allows 40 requests per 10 seconds)
        current_time = time.time()
        if current_time - self.last_request_time < 10 and self.request_count >= 40:
            # Wait until 10 seconds have passed
            time.sleep(10 - (current_time - self.last_request_time))
            self.request_count = 0
            self.last_request_time = time.time()
        elif current_time - self.last_request_time >= 10:
            # Reset counter if 10 seconds have passed
            self.request_count = 0
            self.last_request_time = current_time
        
        # Increment request counter
        self.request_count += 1
        
        # Prepare request
        url = f"{self.base_url}{endpoint}"
        request_params = params or {}
        request_params["api_key"] = self.api_key
        
        # Make request
        response = requests.get(url, params=request_params)
        
        # Check for errors
        if response.status_code != 200:
            print(f"Error making TMDB request: {response.status_code} - {response.text}")
            return {}
        
        return response.json()
    
    @lru_cache(maxsize=100)
    def search_movie(self, query: str) -> List[Movie]:
        """
        Search for movies by title.
        
        Args:
            query: Movie title to search for
            
        Returns:
            List of Movie objects
        """
        endpoint = "/search/movie"
        params = {
            "query": query,
            "include_adult": "false",
            "language": "en-US",
            "page": 1
        }
        
        response = self._make_request(endpoint, params)
        
        if not response or "results" not in response:
            return []
        
        movies = []
        for result in response["results"][:10]:  # Limit to top 10 results
            movie = self._convert_tmdb_to_movie(result)
            if movie:
                movies.append(movie)
        
        return movies
    
    @lru_cache(maxsize=100)
    def get_movie_details(self, tmdb_id: int) -> Optional[Movie]:
        """
        Get detailed information for a movie.
        
        Args:
            tmdb_id: TMDB ID of the movie
            
        Returns:
            Movie object if found, None otherwise
        """
        endpoint = f"/movie/{tmdb_id}"
        params = {
            "append_to_response": "credits,keywords",
            "language": "en-US"
        }
        
        response = self._make_request(endpoint, params)
        
        if not response or "id" not in response:
            return None
        
        return self._convert_tmdb_to_movie(response, include_credits=True)
    
    @lru_cache(maxsize=100)
    def discover_movies(self, params: Dict[str, Any]) -> List[Movie]:
        """
        Discover movies based on various parameters.
        
        Args:
            params: Dictionary of parameters for discovery
            
        Returns:
            List of Movie objects
        """
        endpoint = "/discover/movie"
        
        response = self._make_request(endpoint, params)
        
        if not response or "results" not in response:
            return []
        
        movies = []
        for result in response["results"][:20]:  # Limit to top 20 results
            movie = self._convert_tmdb_to_movie(result)
            if movie:
                movies.append(movie)
        
        return movies
    
    def get_recommendations_by_mood(self, mood: str, limit: int = 10) -> List[Movie]:
        """
        Get movie recommendations based on mood.
        
        Args:
            mood: User's mood
            limit: Maximum number of recommendations
            
        Returns:
            List of Movie objects
        """
        # Map mood to genres
        genre_ids = self._map_mood_to_genre_ids(mood)
        
        if not genre_ids:
            return []
        
        # Discover movies with these genres
        params = {
            "with_genres": ",".join(str(id) for id in genre_ids),
            "sort_by": "popularity.desc",
            "page": 1
        }
        
        movies = self.discover_movies(params)
        return movies[:limit]
    
    def _convert_tmdb_to_movie(self, tmdb_data: Dict[str, Any], include_credits: bool = False) -> Optional[Movie]:
        """
        Convert TMDB movie data to Movie object.
        
        Args:
            tmdb_data: TMDB movie data
            include_credits: Whether to include credits (actors, directors)
            
        Returns:
            Movie object
        """
        if not tmdb_data:
            return None
        
        # Extract basic information
        title = tmdb_data.get("title", "Unknown Title")
        year = None
        if "release_date" in tmdb_data and tmdb_data["release_date"]:
            try:
                year = int(tmdb_data["release_date"].split("-")[0])
            except:
                pass
        
        # Extract genres
        genres = []
        if "genres" in tmdb_data:
            genres = [genre["name"] for genre in tmdb_data["genres"]]
        elif "genre_ids" in tmdb_data:
            genres = self._genre_ids_to_names(tmdb_data["genre_ids"])
        
        # Create poster URL
        poster = ""
        if "poster_path" in tmdb_data and tmdb_data["poster_path"]:
            poster = f"{self.image_base_url}{tmdb_data['poster_path']}"
        
        # Create movie object
        movie = Movie(
            title=title,
            year=year,
            genres=genres,
            plot=tmdb_data.get("overview", ""),
            poster=poster
        )
        
        # Add TMDB ID
        movie.tmdb_id = tmdb_data.get("id")
        
        # Add credits if available and requested
        if include_credits and "credits" in tmdb_data:
            # Add actors
            if "cast" in tmdb_data["credits"]:
                movie.actors = [actor["name"] for actor in tmdb_data["credits"]["cast"][:5]]
            
            # Add directors
            if "crew" in tmdb_data["credits"]:
                movie.directors = [
                    crew["name"] for crew in tmdb_data["credits"]["crew"]
                    if crew["job"] == "Director"
                ]
        
        return movie
    
    def _genre_ids_to_names(self, genre_ids: List[int]) -> List[str]:
        """
        Convert TMDB genre IDs to genre names.
        
        Args:
            genre_ids: List of TMDB genre IDs
            
        Returns:
            List of genre names
        """
        # TMDB genre ID to name mapping
        genre_map = {
            28: "Action",
            12: "Adventure",
            16: "Animation",
            35: "Comedy",
            80: "Crime",
            99: "Documentary",
            18: "Drama",
            10751: "Family",
            14: "Fantasy",
            36: "History",
            27: "Horror",
            10402: "Music",
            9648: "Mystery",
            10749: "Romance",
            878: "Science Fiction",
            10770: "TV Movie",
            53: "Thriller",
            10752: "War",
            37: "Western"
        }
        
        return [genre_map.get(id, "Unknown") for id in genre_ids if id in genre_map]
    
    def _map_mood_to_genre_ids(self, mood: str) -> List[int]:
        """
        Map mood to TMDB genre IDs.
        
        Args:
            mood: User's mood
            
        Returns:
            List of TMDB genre IDs
        """
        # Mood to genre ID mapping
        mood_map = {
            "happy": [35, 16, 10751],  # Comedy, Animation, Family
            "sad": [18, 10749],  # Drama, Romance
            "excited": [28, 12, 878],  # Action, Adventure, Sci-Fi
            "relaxed": [35, 10749, 18],  # Comedy, Romance, Drama
            "scared": [27, 53, 9648],  # Horror, Thriller, Mystery
            "nostalgic": [18, 10751, 36],  # Drama, Family, History
            "curious": [99, 9648, 878],  # Documentary, Mystery, Sci-Fi
            "tired": [35, 16, 10751],  # Comedy, Animation, Family
            "confused": [9648, 53, 878],  # Mystery, Thriller, Sci-Fi
            "angry": [28, 80, 53],  # Action, Crime, Thriller
            "bored": [53, 9648, 28],  # Thriller, Mystery, Action
            "romantic": [10749, 18, 35],  # Romance, Drama, Comedy
            "peaceful": [16, 10749, 18],  # Animation, Romance, Drama
            "mysterious": [9648, 53, 878],  # Mystery, Thriller, Sci-Fi
            "inspired": [18, 12, 36],  # Drama, Adventure, History
            "playful": [16, 35, 10751]  # Animation, Comedy, Family
        }
        
        return mood_map.get(mood.lower(), [35, 28, 18])  # Default to Comedy, Action, Drama
