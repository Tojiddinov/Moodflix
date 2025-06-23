#!/usr/bin/env python3
"""
Test script for Real-Time Voice Recommender
"""

import asyncio
import sys
import os
from realtime_voice_recommender import RealTimeVoiceRecommender

async def test_realtime_voice():
    """Test the real-time voice recommendation system"""
    print("🔧 Testing Real-Time Voice Recommendation System")
    print("=" * 60)
    
    try:
        # Create the recommender instance
        recommender = RealTimeVoiceRecommender()
        
        print("✅ Recommender initialized successfully")
        print(f"📊 Loaded {len(recommender.movies)} movies")
        
        # Test basic functionality
        print("\n🧪 Testing basic functionality...")
        
        # Test preference extraction
        test_input = "I want to watch a funny action movie"
        preferences = recommender.extract_preferences(test_input)
        print(f"🔍 Extracted preferences from '{test_input}': {preferences}")
        
        # Test recommendations
        recommendations = recommender.recommend_movies(preferences)
        print(f"🎬 Found {len(recommendations)} recommendations")
        
        if recommendations:
            for i, movie in enumerate(recommendations[:3], 1):
                print(f"   {i}. {movie['title']} ({movie['year']}) - {', '.join(movie['genres'])}")
        
        print("\n🚀 Starting real-time conversation...")
        print("💡 Instructions:")
        print("   - Say 'Hey Movie Buddy' to wake up the AI")
        print("   - Ask for movie recommendations")
        print("   - Say 'goodbye' or press Ctrl+C to exit")
        print("=" * 60)
        
        # Start the real-time conversation
        await recommender.start_conversation()
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure your microphone is working")
        print("   2. Check your internet connection")
        print("   3. Verify your Deepgram API key is valid")
        print("   4. Try installing missing dependencies:")
        print("      pip install -r requirements.txt")

if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ This script requires Python 3.8 or higher")
        sys.exit(1)
    
    # Check if main_data_updated.csv exists
    if not os.path.exists('main_data_updated.csv'):
        print("❌ Movie database file 'main_data_updated.csv' not found")
        print("   Make sure you're running this from the correct directory")
        sys.exit(1)
    
    # Run the test
    asyncio.run(test_realtime_voice()) 