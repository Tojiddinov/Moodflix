import unittest
from voice_movie_recommender import VoiceMovieRecommender

def test_complex_query(query):
    """Test the voice movie recommender with a complex query"""
    print(f"\nTesting query: '{query}'")
    
    # Initialize the recommender
    print("Initializing voice movie recommender...")
    recommender = VoiceMovieRecommender()
    print("Recommender initialized successfully!")
    
    # Extract preferences from the query
    print("Extracting preferences...")
    preferences = recommender.extract_preferences(query)
    
    # Print extracted preferences
    print("\nExtracted Preferences:")
    for key, value in preferences.items():
        if value:  # Only print non-empty preferences
            print(f"{key.capitalize()}: {value}")
    
    # Get recommendations
    print("\nGenerating recommendations...")
    recommendations = recommender.recommend_movies(preferences, n_recommendations=5)
    
    # Print recommendations in detail
    print("\nRecommended Movies:")
    for i, movie in enumerate(recommendations, 1):
        print(f"\n{i}. {movie.get('title', 'Unknown Title')} ({movie.get('year', 'Unknown Year')})")
        print(f"   Genres: {', '.join(movie.get('genres', []))}")
        print(f"   Director: {', '.join(movie.get('directors', []))}")
        print(f"   Actors: {', '.join(movie.get('actors', [])[:3])}")
        print(f"   Themes: {', '.join(movie.get('themes', []))}")
        print(f"   Mood: {movie.get('mood', 'Unknown')}")
        print(f"   Plot: {movie.get('plot', 'No plot available')[:200]}...")
    
    print("\n===========================\n")

if __name__ == "__main__":
    # Test multiple complex queries
    test_queries = [
        "I want a psychological thriller from the 90s with Leonardo DiCaprio, directed by Christopher Nolan, that explores themes of identity and reality",
        "I want to watch an exciting sci-fi movie from the 90s, but not horror, with Tom Hanks or Leonardo DiCaprio, directed by Spielberg about survival",
        "I'm feeling nostalgic, show me something from the 80s that's funny but not too childish, maybe with some adventure elements"
    ]
    
    for query in test_queries:
        test_complex_query(query) 