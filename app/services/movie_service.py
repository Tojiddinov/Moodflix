"""
Movie Service module for MoodFlix application.
Handles movie recommendations and database interactions.
"""
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import json
from pathlib import Path

from app.core.config import settings
from app.models.movie import Movie
from app.services.recommendation_service import RecommendationService
from app.services.compatibility_fixed import create_similarity, get_recommendations

class MovieService:
    """Service for handling movie recommendations and database interactions."""
    
    def __init__(self):
        """Initialize the movie service and load the movie database."""
        self.movies: List[Movie] = []
        self.recommendation_service = RecommendationService()
        self.data = None
        self.similarity = None
        self.load_movie_database()
    
    def load_movie_database(self) -> None:
        """Load movie data from CSV file or create sample database if file doesn't exist."""
        try:
            # Try to load from CSV file
            movie_data_path = settings.MOVIE_DATA_PATH
            if os.path.exists(movie_data_path):
                self._load_from_csv(movie_data_path)
                print(f"Loaded {len(self.movies)} movies from {movie_data_path}")
                
                # Initialize the recommendation service with the loaded movies
                self.recommendation_service.set_movies(self.movies)
                
                # Also initialize the compatibility layer for old code
                self.data, self.similarity = create_similarity()
            else:
                # Fall back to sample database
                self._create_sample_database()
                print(f"Created sample database with {len(self.movies)} movies")
                
                # Initialize the recommendation service with the sample movies
                self.recommendation_service.set_movies(self.movies)
                
                # Also initialize the compatibility layer for old code
                self.data, self.similarity = create_similarity()
        except Exception as e:
            print(f"Error loading movie database: {str(e)}")
            # Fall back to sample database
            self._create_sample_database()
            print(f"Created sample database with {len(self.movies)} movies")
            
            # Initialize the recommendation service with the sample movies
            self.recommendation_service.set_movies(self.movies)
            
            # Also initialize the compatibility layer for old code
            self.data, self.similarity = create_similarity()
    
    def _load_from_csv(self, file_path: str) -> None:
        """
        Load movie data from CSV file with enhanced data extraction.
        
        Args:
            file_path: Path to the CSV file
        """
        try:
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Process each row
            for _, row in df.iterrows():
                try:
                    # Extract genres
                    genres = []
                    if 'genres' in row and pd.notna(row['genres']):
                        # Handle different formats of genres data
                        if isinstance(row['genres'], str):
                            if row['genres'].startswith('[') and row['genres'].endswith(']'):
                                # JSON format
                                try:
                                    genres = json.loads(row['genres'].replace("'", "\""))
                                except:
                                    # Comma-separated format
                                    genres = [g.strip() for g in row['genres'].strip('[]').split(',')]
                            else:
                                # Pipe-separated format
                                genres = [g.strip() for g in row['genres'].split('|')]
                    
                    # Extract year
                    year = None
                    if 'year' in row and pd.notna(row['year']):
                        year = int(row['year'])
                    elif 'release_date' in row and pd.notna(row['release_date']):
                        # Try to extract year from release_date
                        try:
                            year = int(row['release_date'].split('-')[0])
                        except:
                            pass
                    
                    # Create movie object
                    movie = Movie(
                        title=row.get('title', 'Unknown Title') if pd.notna(row.get('title')) else 'Unknown Title',
                        year=year,
                        genres=genres,
                        plot=row.get('overview', '') if pd.notna(row.get('overview')) else '',
                        poster=row.get('poster_path', '') if pd.notna(row.get('poster_path')) else ''
                    )
                    
                    # Add additional fields if they exist
                    if 'actors' in row and pd.notna(row['actors']):
                        if isinstance(row['actors'], str):
                            movie.actors = [a.strip() for a in row['actors'].strip('[]').split(',')]
                    
                    if 'directors' in row and pd.notna(row['directors']):
                        if isinstance(row['directors'], str):
                            movie.directors = [d.strip() for d in row['directors'].strip('[]').split(',')]
                    
                    # Add movie to list
                    self.movies.append(movie)
                except Exception as e:
                    print(f"Error processing movie row: {str(e)}")
                    continue
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            raise
    
    def _create_sample_database(self) -> None:
        """Create a sample movie database for fallback."""
        sample_movies = [
            Movie(
                title="The Shawshank Redemption",
                year=1994,
                genres=["Drama"],
                plot="Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
                poster="https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZmRlYWMwMWFmXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg"
            ),
            Movie(
                title="The Godfather",
                year=1972,
                genres=["Crime", "Drama"],
                plot="The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
                poster="https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg"
            ),
            Movie(
                title="Inception",
                year=2010,
                genres=["Action", "Adventure", "Sci-Fi"],
                plot="A thief who steals corporate secrets through the use of dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.",
                poster="https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_.jpg"
            ),
            Movie(
                title="Forrest Gump",
                year=1994,
                genres=["Drama", "Romance"],
                plot="The presidencies of Kennedy and Johnson, the events of Vietnam, Watergate, and other historical events unfold through the perspective of an Alabama man with an IQ of 75.",
                poster="https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg"
            ),
            Movie(
                title="Toy Story",
                year=1995,
                genres=["Animation", "Adventure", "Comedy"],
                plot="A cowboy doll is profoundly threatened and jealous when a new spaceman figure supplants him as top toy in a boy's room.",
                poster="https://m.media-amazon.com/images/M/MV5BMDU2ZWJlMjktMTRhMy00ZTA5LWEzNDgtYmNmZTEwZTViZWJkXkEyXkFqcGdeQXVyNDQ2OTk4MzI@._V1_.jpg"
            ),
            Movie(
                title="The Lion King",
                year=1994,
                genres=["Animation", "Adventure", "Drama"],
                plot="Lion prince Simba and his father are targeted by his bitter uncle, who wants to ascend the throne himself.",
                poster="https://m.media-amazon.com/images/M/MV5BYTYxNGMyZTYtMjE3MS00MzNjLWFjNmYtMDk3N2FmM2JiM2M1XkEyXkFqcGdeQXVyNjY5NDU4NzI@._V1_.jpg"
            ),
            Movie(
                title="Titanic",
                year=1997,
                genres=["Drama", "Romance"],
                plot="A seventeen-year-old aristocrat falls in love with a kind but poor artist aboard the luxurious, ill-fated R.M.S. Titanic.",
                poster="https://m.media-amazon.com/images/M/MV5BMDdmZGU3NDQtY2E5My00ZTliLWIzOTUtMTY4ZGI1YjdiNjk3XkEyXkFqcGdeQXVyNTA4NzY1MzY@._V1_.jpg"
            ),
            Movie(
                title="Fight Club",
                year=1999,
                genres=["Drama", "Thriller"],
                plot="An insomniac office worker and a devil-may-care soapmaker form an underground fight club that evolves into something much, much more.",
                poster="https://m.media-amazon.com/images/M/MV5BMmEzNTkxYjQtZTc0MC00YTVjLTg5ZTEtZWMwOWVlYzY0NWIwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_.jpg"
            ),
            Movie(
                title="Memento",
                year=2000,
                genres=["Mystery", "Thriller"],
                plot="A man with short-term memory loss attempts to track down his wife's murderer.",
                poster="https://m.media-amazon.com/images/M/MV5BZTcyNjk1MjgtOWI3Mi00YzQwLWI5MTktMzY4ZmI2NDAyNzYzXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_.jpg"
            ),
            Movie(
                title="Back to the Future",
                year=1985,
                genres=["Adventure", "Comedy", "Sci-Fi"],
                plot="Marty McFly, a 17-year-old high school student, is accidentally sent thirty years into the past in a time-traveling DeLorean invented by his close friend, the eccentric scientist Doc Brown.",
                poster="https://m.media-amazon.com/images/M/MV5BZmU0M2Y1OGUtZjIxNi00ZjBkLTg1MjgtOWIyNThiZWIwYjRiXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_.jpg"
            )
        ]
        
        self.movies = sample_movies
    
    def recommend_movies(self, preferences: Dict[str, Any], n_recommendations: int = 5) -> List[Movie]:
        """
        Recommend movies based on user preferences with enhanced scoring.
        
        Args:
            preferences: Dictionary of user preferences
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended Movie objects
        """
        if not self.movies:
            return []
        
        # Use the recommendation service for better recommendations
        return self.recommendation_service.hybrid_recommendations(preferences, n_recommendations)
    
    def find_movie_by_title(self, title: str) -> Optional[Movie]:
        """
        Find a movie by its title.
        
        Args:
            title: Movie title to search for
            
        Returns:
            Movie object if found, None otherwise
        """
        print(f"Checking if movie '{title}' exists in database")
        
        # First try exact match
        for movie in self.movies:
            if movie.title.lower() == title.lower():
                return movie
        
        # Try partial match if exact match not found
        for movie in self.movies:
            if title.lower() in movie.title.lower():
                return movie
        
        # If still not found, try using the compatibility layer
        if self.data is not None:
            # Check if movie exists in the old data format
            if title.lower() in self.data['movie_title'].values:
                # Get the movie data from the old format
                movie_data = self.data[self.data['movie_title'] == title.lower()].iloc[0]
                
                # Convert to Movie object
                genres = movie_data.get('genres', '').split(',') if 'genres' in movie_data else []
                movie = Movie(
                    title=movie_data.get('movie_title', 'Unknown Title'),
                    year=movie_data.get('year') if 'year' in movie_data else None,
                    genres=[g.strip() for g in genres],
                    plot=movie_data.get('plot', '') if 'plot' in movie_data else '',
                    poster=''
                )
                return movie
        
        print(f"Movie '{title}' not found in database")
        return None
    
    def get_timestamp(self) -> str:
        """Get current timestamp in readable format."""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def get_similar_movies(self, movie_title: str, n_recommendations: int = 5) -> List[Movie]:
        """
        Get movies similar to the given movie.
        
        Args:
            movie_title: Title of the movie to find similar movies for
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of similar Movie objects
        """
        # First try using the new recommendation service
        movie = self.find_movie_by_title(movie_title)
        if movie:
            return self.recommendation_service.content_based_recommendations(movie.title, n_recommendations)
        
        # Fall back to the compatibility layer
        similar_titles = get_recommendations(movie_title, self.data, self.similarity)
        
        # Convert titles to Movie objects
        similar_movies = []
        for title in similar_titles:
            similar_movie = self.find_movie_by_title(title)
            if similar_movie:
                similar_movies.append(similar_movie)
        
        return similar_movies
