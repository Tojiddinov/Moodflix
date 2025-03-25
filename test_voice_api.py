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
        text = "I want a happy family comedy from the 80s directed by Spielberg with a family theme"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("comedy", prefs["genres"])
        self.assertIn("family", prefs["genres"])
        self.assertEqual("happy", prefs["mood"])
        self.assertEqual("80s", prefs["era"])
        self.assertIn("Spielberg", prefs["directors"])
        self.assertIn("family", prefs["themes"])
    
    def test_basic_preference_extraction(self):
        # Test basic preference extraction
        text = "I want to watch an action movie with Tom Hanks"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("action", prefs["genres"])
        self.assertIn("Tom Hanks", prefs["actors"])
    
    def test_negation_patterns(self):
        # Test that negation patterns are properly handled
        text = "I want a comedy but not horror with Will Smith"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("comedy", prefs["genres"])
        self.assertNotIn("horror", prefs["genres"])
        self.assertIn("Will Smith", prefs["actors"])
    
    def test_complex_query(self):
        # Test a more complex query with multiple preferences
        text = "I want to watch a thriller movie from the 90s directed by Nolan with a theme of revenge"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("thriller", prefs["genres"])
        self.assertEqual("90s", prefs["era"])
        self.assertIn("Nolan", prefs["directors"])
        self.assertIn("revenge", prefs["themes"])
    
    def test_mood_extraction(self):
        # Test mood extraction with direct expression
        text = "I'm feeling sad, show me something emotional"
        prefs = self.recommender.extract_preferences(text)
        self.assertEqual("sad", prefs["mood"])
    
    def test_filler_words(self):
        # Test that filler words are removed properly
        text = "Um, I like, want to see you know, a sci-fi movie with um aliens"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("sci-fi", prefs["genres"])
    
    def test_era_extraction(self):
        # Test different era formats
        text = "Show me movies from the 80s"
        prefs = self.recommender.extract_preferences(text)
        self.assertEqual("80s", prefs["era"])
        
        text = "I want recent movies"
        prefs = self.recommender.extract_preferences(text)
        self.assertEqual("2020s", prefs["era"])
    
    def test_actor_name_detection(self):
        # Test proper detection and formatting of actor names
        text = "I want movies with robert downey jr and scarlett johansson"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("Robert Downey Jr", prefs["actors"])
        self.assertIn("Scarlett Johansson", prefs["actors"])
    
    def test_theme_context(self):
        # Test theme detection with contextual clues
        text = "I want a movie about friendship and personal growth"
        prefs = self.recommender.extract_preferences(text)
        self.assertIn("friendship", prefs["themes"])
        
if __name__ == "__main__":
    unittest.main() 