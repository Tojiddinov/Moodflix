"""
Recommendation Service module for MoodFlix application.
Provides advanced recommendation algorithms for movie suggestions.
"""
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

from app.models.movie import Movie
from app.core.config import settings

class RecommendationService:
    """Service for advanced movie recommendations."""
    
    def __init__(self, movies: List[Movie] = None):
        """
        Initialize the recommendation service.
        
        Args:
            movies: List of Movie objects to use for recommendations
        """
        self.movies = movies or []
        self.similarity_matrix = None
        self.movie_indices = {}
        
        # Initialize similarity matrix if movies are provided
        if self.movies:
            self._build_similarity_matrix()
    
    def set_movies(self, movies: List[Movie]) -> None:
        """
        Set the movie database and rebuild similarity matrix.
        
        Args:
            movies: List of Movie objects
        """
        self.movies = movies
        self._build_similarity_matrix()
    
    def _build_similarity_matrix(self) -> None:
        """Build the movie similarity matrix for content-based recommendations."""
        if not self.movies:
            return
        
        # Create a DataFrame from movies
        movie_data = []
        for i, movie in enumerate(self.movies):
            # Create a combined features string for TF-IDF
            genres_str = ' '.join(movie.genres) if movie.genres else ''
            plot_str = movie.plot if movie.plot else ''
            actors_str = ' '.join(movie.actors) if hasattr(movie, 'actors') and movie.actors else ''
            directors_str = ' '.join(movie.directors) if hasattr(movie, 'directors') and movie.directors else ''
            
            # Add year as a feature
            year_str = f"year_{movie.year}" if movie.year else ''
            
            # Combine all features
            combined_features = f"{genres_str} {plot_str} {actors_str} {directors_str} {year_str}"
            
            # Clean the text
            combined_features = re.sub(r'[^\w\s]', '', combined_features.lower())
            
            movie_data.append({
                'title': movie.title,
                'features': combined_features
            })
            
            # Store the index for quick lookup
            self.movie_indices[movie.title] = i
        
        df = pd.DataFrame(movie_data)
        
        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words='english')
        
        # Check if we have valid features
        if df['features'].str.strip().str.len().sum() > 0:
            tfidf_matrix = tfidf.fit_transform(df['features'])
            
            # Calculate cosine similarity
            self.similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
        else:
            # Create an identity matrix if no valid features
            self.similarity_matrix = np.eye(len(df))
    
    def content_based_recommendations(self, movie_title: str, n_recommendations: int = 5) -> List[Movie]:
        """
        Get content-based recommendations similar to a given movie.
        
        Args:
            movie_title: Title of the movie to find recommendations for
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended Movie objects
        """
        if not self.movies or not self.similarity_matrix is not None:
            return []
        
        # Find the movie index
        movie_idx = None
        for i, movie in enumerate(self.movies):
            if movie.title.lower() == movie_title.lower():
                movie_idx = i
                break
        
        if movie_idx is None:
            return []
        
        # Get similarity scores
        sim_scores = list(enumerate(self.similarity_matrix[movie_idx]))
        
        # Sort movies by similarity score
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        
        # Get top N similar movies (excluding the input movie)
        sim_scores = [x for x in sim_scores if x[0] != movie_idx][:n_recommendations]
        
        # Get movie indices
        movie_indices = [i[0] for i in sim_scores]
        
        # Return recommended movies
        return [self.movies[i] for i in movie_indices]
    
    def hybrid_recommendations(self, preferences: Dict[str, Any], n_recommendations: int = 5) -> List[Movie]:
        """
        Get hybrid recommendations based on user preferences and content similarity.
        
        Args:
            preferences: Dictionary of user preferences
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended Movie objects
        """
        if not self.movies:
            return []
        
        # Extract preferences
        preferred_genres = preferences.get('genres', [])
        preferred_mood = preferences.get('mood', None)
        preferred_era = preferences.get('era', None)
        preferred_actor = preferences.get('actor', None)
        preferred_director = preferences.get('director', None)
        
        # Map mood to genres if mood is specified but genres are not
        if preferred_mood and not preferred_genres:
            mood_genres = settings.MOOD_MAPPINGS.get(preferred_mood.lower(), [])
            if mood_genres:
                preferred_genres = mood_genres
        
        # Calculate scores for each movie
        scored_movies = []
        for i, movie in enumerate(self.movies):
            score = 0
            
            # Score based on genres
            if preferred_genres:
                for genre in preferred_genres:
                    if genre.lower() in [g.lower() for g in movie.genres]:
                        score += 2
            
            # Score based on era/year
            if preferred_era and movie.year:
                era_match = False
                if preferred_era.lower() == '80s' and 1980 <= movie.year <= 1989:
                    era_match = True
                elif preferred_era.lower() == '90s' and 1990 <= movie.year <= 1999:
                    era_match = True
                elif preferred_era.lower() == '2000s' and 2000 <= movie.year <= 2009:
                    era_match = True
                elif preferred_era.lower() == '2010s' and 2010 <= movie.year <= 2019:
                    era_match = True
                elif preferred_era.lower() == '2020s' and movie.year >= 2020:
                    era_match = True
                
                if era_match:
                    score += 1
            
            # Score based on actor
            if preferred_actor and hasattr(movie, 'actors') and movie.actors:
                for actor in movie.actors:
                    if preferred_actor.lower() in actor.lower():
                        score += 1
                        break
            
            # Score based on director
            if preferred_director and hasattr(movie, 'directors') and movie.directors:
                for director in movie.directors:
                    if preferred_director.lower() in director.lower():
                        score += 1
                        break
            
            # Add to scored movies if it has a positive score
            if score > 0:
                scored_movies.append((movie, score, i))
        
        # If we have enough scored movies, enhance with content-based similarity
        if len(scored_movies) >= n_recommendations and self.similarity_matrix is not None:
            # Get top 3 highest scoring movies
            top_movies = sorted(scored_movies, key=lambda x: x[1], reverse=True)[:3]
            
            # For each top movie, get similar movies
            similar_movies = []
            for movie, _, idx in top_movies:
                # Get similarity scores
                sim_scores = list(enumerate(self.similarity_matrix[idx]))
                
                # Sort by similarity
                sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
                
                # Get top similar movies (excluding the input movie)
                sim_scores = [x for x in sim_scores if x[0] != idx][:5]
                
                # Add to similar movies
                for sim_idx, sim_score in sim_scores:
                    similar_movies.append((self.movies[sim_idx], sim_score * 0.5, sim_idx))
            
            # Combine scored movies and similar movies
            all_scored_movies = scored_movies + similar_movies
            
            # Remove duplicates (keep highest score)
            unique_movies = {}
            for movie, score, idx in all_scored_movies:
                if movie.title not in unique_movies or score > unique_movies[movie.title][1]:
                    unique_movies[movie.title] = (movie, score)
            
            # Sort by score and return top N
            final_movies = sorted(unique_movies.values(), key=lambda x: x[1], reverse=True)
            return [movie for movie, _ in final_movies[:n_recommendations]]
        
        # Fall back to simple scoring if not enough movies or no similarity matrix
        scored_movies = sorted(scored_movies, key=lambda x: x[1], reverse=True)
        return [movie for movie, _, _ in scored_movies[:n_recommendations]]
    
    def collaborative_recommendations(self, user_ratings: Dict[str, float], n_recommendations: int = 5) -> List[Movie]:
        """
        Get collaborative filtering recommendations based on user ratings.
        
        Args:
            user_ratings: Dictionary mapping movie titles to user ratings
            n_recommendations: Number of recommendations to return
            
        Returns:
            List of recommended Movie objects
        """
        # This is a simplified collaborative filtering implementation
        # In a real system, you would use a more sophisticated algorithm
        
        if not self.movies or not self.similarity_matrix is not None or not user_ratings:
            return []
        
        # Find indices of rated movies
        rated_indices = []
        for title, rating in user_ratings.items():
            for i, movie in enumerate(self.movies):
                if movie.title.lower() == title.lower():
                    rated_indices.append((i, rating))
                    break
        
        if not rated_indices:
            return []
        
        # Calculate weighted average of similarity scores
        scores = np.zeros(len(self.movies))
        total_weights = np.zeros(len(self.movies))
        
        for idx, rating in rated_indices:
            # Normalize rating to -1 to 1 scale (assuming 1-5 rating scale)
            normalized_rating = (rating - 3) / 2
            
            # Add weighted similarity scores
            scores += normalized_rating * self.similarity_matrix[idx]
            total_weights += np.abs(self.similarity_matrix[idx])
        
        # Avoid division by zero
        total_weights[total_weights == 0] = 1
        
        # Calculate final scores
        final_scores = scores / total_weights
        
        # Create a list of (movie, score) tuples
        movie_scores = [(self.movies[i], score) for i, score in enumerate(final_scores)]
        
        # Filter out already rated movies
        rated_titles = [title.lower() for title in user_ratings.keys()]
        movie_scores = [(movie, score) for movie, score in movie_scores 
                       if movie.title.lower() not in rated_titles]
        
        # Sort by score and return top N
        movie_scores = sorted(movie_scores, key=lambda x: x[1], reverse=True)
        return [movie for movie, _ in movie_scores[:n_recommendations]]
