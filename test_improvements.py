import unittest
from voice_movie_recommender import VoiceMovieRecommender

class TestVoiceMovieRecommenderImprovements(unittest.TestCase):
    def setUp(self):
        self.recommender = VoiceMovieRecommender()
        
    def test_complex_genre_combinations(self):
        """Test handling of complex genre combinations and negations"""
        # Test 1: Action but not horror
        query = "I want an action movie but not horror"
        preferences = self.recommender.extract_preferences(query)
        self.assertIn("action", preferences["genres"])
        self.assertNotIn("horror", preferences["genres"])
        
        # Test 2: Sci-fi thriller combination
        query = "Show me a sci-fi thriller"
        preferences = self.recommender.extract_preferences(query)
        self.assertIn("sci-fi", preferences["genres"])
        self.assertIn("thriller", preferences["genres"])
        
        # Test 3: Comedy but not family
        query = "I want something funny but not family-friendly"
        preferences = self.recommender.extract_preferences(query)
        self.assertIn("comedy", preferences["genres"])
        self.assertNotIn("family", preferences["genres"])
    
    def test_era_and_actor_combinations(self):
        """Test handling of era preferences with actor combinations"""
        # Test 1: 90s movie with specific actor
        query = "Show me a 90s movie with Tom Hanks"
        preferences = self.recommender.extract_preferences(query)
        self.assertEqual(preferences["era"], "90s")
        self.assertIn("Tom Hanks", preferences["actors"])
        
        # Test 2: Classic movie with multiple actors
        query = "I want a classic movie starring Leonardo DiCaprio and Brad Pitt"
        preferences = self.recommender.extract_preferences(query)
        self.assertEqual(preferences["era"], "classic")
        self.assertIn("Leonardo DiCaprio", preferences["actors"])
        self.assertIn("Brad Pitt", preferences["actors"])
    
    def test_mood_and_theme_combinations(self):
        """Test handling of mood preferences with themes"""
        # Test 1: Sad movie about love
        query = "I'm feeling sad, show me something about love"
        preferences = self.recommender.extract_preferences(query)
        self.assertEqual(preferences["mood"], "sad")
        self.assertIn("love", preferences["themes"])
        
        # Test 2: Exciting movie about adventure
        query = "I want something exciting about adventure"
        preferences = self.recommender.extract_preferences(query)
        self.assertEqual(preferences["mood"], "excited")
        self.assertIn("adventure", preferences["themes"])
    
    def test_complex_recommendations(self):
        """Test complex recommendation queries"""
        # Test 1: Complex query with multiple preferences
        query = "I want to watch an exciting sci-fi movie from the 90s, but not horror, with Tom Hanks or Leonardo DiCaprio, directed by Spielberg about survival"
        preferences = self.recommender.extract_preferences(query)
        self.assertIn("sci-fi", preferences["genres"])
        self.assertNotIn("horror", preferences["genres"])
        self.assertEqual(preferences["era"], "90s")
        self.assertIn("Tom Hanks", preferences["actors"])
        self.assertIn("Leonardo DiCaprio", preferences["actors"])
        self.assertIn("Spielberg", preferences["directors"])
        self.assertIn("survival", preferences["themes"])
        
        # Test 2: Another complex query
        query = "Show me a funny but not family-friendly movie from the 80s with Will Smith, directed by Martin Scorsese about crime"
        preferences = self.recommender.extract_preferences(query)
        self.assertIn("comedy", preferences["genres"])
        self.assertNotIn("family", preferences["genres"])
        self.assertEqual(preferences["era"], "80s")
        self.assertIn("Will Smith", preferences["actors"])
        self.assertIn("Martin Scorsese", preferences["directors"])
        self.assertIn("crime", preferences["themes"])

if __name__ == '__main__':
    recommender = VoiceMovieRecommender()
    recommender.main_web()  # Initialize for web use
    # Handle requests through handle_web_request method 