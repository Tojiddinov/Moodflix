import unittest
from voice_movie_recommender import VoiceMovieRecommender

class TestVoiceMovieRecommender(unittest.TestCase):
    def setUp(self):
        """Initialize the recommender for each test"""
        self.recommender = VoiceMovieRecommender()
    
    def test_preference_extraction_genres(self):
        """Test that genre preferences are correctly extracted"""
        test_text = "I would like to watch an action movie with some comedy elements"
        self.recommender.extract_preferences(test_text)
        self.assertIn("action", self.recommender.user_preferences["genres"])
        self.assertIn("comedy", self.recommender.user_preferences["genres"])
    
    def test_preference_extraction_actors(self):
        """Test that actor preferences are correctly extracted"""
        test_text = "I want a movie with Tom Hanks"
        self.recommender.extract_preferences(test_text)
        self.assertIn("Tom Hanks", self.recommender.user_preferences["actors"])
    
    def test_preference_extraction_era(self):
        """Test that era preferences are correctly extracted"""
        test_text = "I want to watch something from the 90s"
        self.recommender.extract_preferences(test_text)
        self.assertEqual("90s", self.recommender.user_preferences["era"])
    
    def test_preference_extraction_mood(self):
        """Test that mood preferences are correctly extracted"""
        test_text = "I'm in the mood for something uplifting and happy"
        self.recommender.extract_preferences(test_text)
        self.assertEqual("happy", self.recommender.user_preferences["mood"])
    
    def test_movie_recommendation(self):
        """Test that movie recommendations are generated based on preferences"""
        # Set some preferences directly
        self.recommender.user_preferences = {
            "genres": ["action", "sci-fi"],
            "mood": "excited",
            "era": "90s",
            "actors": [],
            "directors": [],
            "themes": []
        }
        
        # Get recommendations
        recommendations = self.recommender.recommend_movies(limit=3)
        
        # Check that we got recommendations
        self.assertTrue(len(recommendations) > 0, "Should return at least one recommendation")
        
        # Check that recommendations are in expected format
        for movie in recommendations:
            self.assertIn("title", movie, "Movie should have a title")
            self.assertIn("genres", movie, "Movie should have genres")
    
    def test_multiple_preference_extraction(self):
        """Test that multiple preferences can be extracted from a single text"""
        test_text = "I want a funny 80s movie directed by Spielberg with a family theme"
        self.recommender.extract_preferences(test_text)
        
        self.assertIn("comedy", self.recommender.user_preferences["genres"])
        self.assertEqual("80s", self.recommender.user_preferences["era"])
        self.assertIn("Spielberg", self.recommender.user_preferences["directors"])
        self.assertIn("family", self.recommender.user_preferences["themes"])

if __name__ == "__main__":
    unittest.main() 