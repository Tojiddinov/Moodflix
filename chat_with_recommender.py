import sys
import time
import random
import json
import re
from voice_movie_recommender import VoiceMovieRecommender

class MovieBuddyAI:
    def __init__(self):
        print("Initializing MovieBuddyAI...")
        self.recommender = VoiceMovieRecommender()
        self.conversation_history = []
        self.current_preferences = {}
        self.last_recommendations = []
        self.current_movie = None
        self.last_query = None
        
        # Enhanced mood responses with genre-specific suggestions
        self.mood_responses = {
            'sad': [
                "I understand you're feeling down. Let me find something uplifting for you.",
                "When you're feeling sad, sometimes a good movie can help lift your spirits.",
                "I'll find something that might help brighten your day."
            ],
            'happy': [
                "Great to hear you're feeling happy! Let's find something to match your mood.",
                "Your positive energy is contagious! Let's find a movie to match that."
            ],
            'excited': [
                "That excitement is contagious! Let's find something thrilling for you.",
                "I'll find something that matches your energy level!"
            ],
            'tired': [
                "I understand you're feeling tired. Let me find something relaxing for you.",
                "When you're tired, sometimes a good movie can be just what you need."
            ],
            'stressed': [
                "I understand you're feeling stressed. Let me find something calming for you.",
                "A good movie can help you unwind. Let me find something perfect for that."
            ],
            'romantic': [
                "Looking for something romantic? I'll find the perfect movie for your mood.",
                "Let me find something that will set the right romantic atmosphere."
            ],
            'nostalgic': [
                "Feeling nostalgic? I'll find something that will take you back in time.",
                "Let me find a movie that will bring back those good memories."
            ]
        }
        
        # Genre-specific mood suggestions
        self.genre_mood_suggestions = {
            'comedy': ['happy', 'excited', 'romantic'],
            'drama': ['sad', 'tired', 'stressed'],
            'action': ['excited', 'happy'],
            'romance': ['romantic', 'happy'],
            'thriller': ['excited', 'alert'],
            'horror': ['excited', 'alert'],
            'documentary': ['intrigued', 'alert']
        }
        
        # Streaming platform suggestions
        self.streaming_platforms = ['Netflix', 'Amazon Prime', 'Hulu', 'Disney+', 'HBO Max']
        
        print("MovieBuddyAI is ready to help!")

    def print_welcome_message(self):
        print("\n" + "="*50)
        print("Welcome to MovieBuddyAI - Your AI Movie Companion!")
        print("="*50)
        print("\nI'm your personal movie buddy, here to help you find the perfect movie to watch.")
        print("You can ask me about movies, tell me your preferences, or just chat!")
        print("\nSome example queries:")
        print("- I want to watch something exciting")
        print("- Can you recommend a good drama from the 90s?")
        print("- I'm in the mood for a comedy with Tom Hanks")
        print("- What's a good movie for a date night?")
        print("- I'm feeling sad today, what should I watch?")
        print("- Tell me more about [movie title]")
        print("- Where can I watch this movie?")
        print("\nType 'quit' or 'exit' to end our conversation.")
        print("="*50 + "\n")

    def get_mood_response(self, mood):
        if mood in self.mood_responses:
            return random.choice(self.mood_responses[mood])
        return "Let me find something great for you!"

    def find_movie_by_title(self, title):
        """Find a movie by title with fuzzy matching"""
        try:
            if not title:
                return None
                
            # Clean the input title
            search_title = title.lower().strip()
            
            # First try exact match
            for movie in self.recommender.movies:
                if movie.get('title', '').lower() == search_title:
                    return movie
            
            # Then try contains match
            for movie in self.recommender.movies:
                if search_title in movie.get('title', '').lower():
                    return movie
            
            # Finally try fuzzy match
            best_ratio = 0
            best_match = None
            
            for movie in self.recommender.movies:
                movie_title = movie.get('title', '').lower()
                # Calculate similarity ratio
                ratio = sum(a == b for a, b in zip(search_title, movie_title)) / max(len(search_title), len(movie_title))
                if ratio > best_ratio and ratio > 0.8:  # 80% similarity threshold
                    best_ratio = ratio
                    best_match = movie
            
            return best_match
            
        except Exception as e:
            print(f"Error finding movie: {str(e)}")
            return None

    def get_streaming_suggestions(self, user_input):
        """Get streaming suggestions for a movie"""
        try:
            # Check if this is actually a streaming query
            streaming_phrases = [
                'where can i watch',
                'how to watch',
                'streaming',
                'available on',
                'stream',
                'watch online'
            ]
            
            if not any(phrase in user_input.lower() for phrase in streaming_phrases):
                return None
            
            # Extract movie title from the input
            title_patterns = [
                r'where can i watch "(.*?)"',
                r'where can i watch (.*?)(?:\?|\s|$)',
                r'how to watch "(.*?)"',
                r'how to watch (.*?)(?:\?|\s|$)',
                r'streaming "(.*?)"',
                r'streaming (.*?)(?:\?|\s|$)',
                r'available on "(.*?)"',
                r'available on (.*?)(?:\?|\s|$)',
                r'stream "(.*?)"',
                r'stream (.*?)(?:\?|\s|$)',
                r'watch online "(.*?)"',
                r'watch online (.*?)(?:\?|\s|$)'
            ]
            
            movie_title = None
            for pattern in title_patterns:
                match = re.search(pattern, user_input.lower())
                if match:
                    movie_title = match.group(1).strip()
                    break
            
            # If no title found through patterns, try to use the last part of the input
            if not movie_title and len(user_input.split()) > 2:
                movie_title = ' '.join(user_input.split()[-2:])  # Take last two words as potential title
            
            if not movie_title:
                return None
            
            # Find the movie in our database
            movie = self.find_movie_by_title(movie_title)
            if not movie:
                return f"I couldn't find '{movie_title}' in my database. Could you please check the spelling or try another movie?"
            
            # Mock streaming platforms data (in a real system, you'd query a streaming API)
            available_on = random.sample(self.streaming_platforms, random.randint(1, 3))
            
            if available_on:
                platforms = ', '.join(available_on[:-1]) + (' and ' + available_on[-1] if len(available_on) > 1 else available_on[0])
                response = f"{movie.get('title', movie_title)} might be available on {platforms}.\n"
                response += "Please note that streaming availability may vary by region and over time. "
                response += "You can check JustWatch.com for the most up-to-date streaming information in your region."
            else:
                response = f"I couldn't find streaming information for {movie.get('title', movie_title)}. "
                response += "You might want to:\n"
                response += "1. Check your local streaming services directly\n"
                response += "2. Try rental services like iTunes, Google Play, or Vudu\n"
                response += "3. Look for the movie on JustWatch.com for up-to-date streaming information"
            
            return response
            
        except Exception as e:
            print(f"Error getting streaming suggestions: {str(e)}")
            return None

    def get_movie_details(self, user_input):
        try:
            # Extract movie title from user input
            words = user_input.lower().split()
            title = None
            
            if 'about' in words:
                title = ' '.join(words[words.index('about')+1:])
            elif 'movie' in words:
                title = ' '.join(words[:words.index('movie')])
            else:
                # Try to find the movie title at the end of the input
                title = ' '.join(words[-3:])  # Take last 3 words as potential title
            
            if not title:
                return "I'm not sure which movie you'd like to know more about. Could you please specify the movie title?"
            
            movie = self.find_movie_by_title(title)
            if not movie:
                return f"I couldn't find information about '{title}'. Could you please try another movie?"
            
            self.current_movie = movie
            
            # Format the response with proper error handling
            response = f"\nDetailed information about {movie.get('title', 'Unknown Title')}:\n"
            response += f"Year: {movie.get('year', 'N/A')}\n"
            response += f"Genres: {', '.join(movie.get('genres', []))}\n"
            
            directors = movie.get('directors', [])
            response += f"Director: {directors[0] if directors else 'N/A'}\n"
            
            actors = movie.get('actors', [])
            response += f"Main Cast: {', '.join(actors[:3]) if actors else 'N/A'}\n"
            
            themes = movie.get('themes', [])
            response += f"Themes: {', '.join(themes)}\n"
            
            response += f"Mood: {movie.get('mood', 'N/A')}\n"
            response += f"Plot: {movie.get('plot', 'No plot available.')}\n\n"
            
            response += "Would you like to:\n"
            response += "1. Know where to watch this movie?\n"
            response += "2. Get similar recommendations?\n"
            response += "3. Know more about the cast or director?\n"
            response += "Just let me know what you'd like to explore!"
            
            return response
            
        except Exception as e:
            print(f"Error getting movie details: {str(e)}")
            return "I'm sorry, I couldn't process that request. Could you please try again?"

    def handle_follow_up(self, user_input):
        follow_up_keywords = {
            'more': ['more', 'another', 'different', 'other'],
            'details': ['tell me more', 'details', 'about', 'explain'],
            'similar': ['similar', 'like', 'same', 'alike'],
            'watch': ['watch', 'streaming', 'where to watch', 'available'],
            'cast': ['cast', 'actors', 'director', 'crew']
        }
        
        user_input = user_input.lower().strip()
        
        # Check for streaming availability
        if any(keyword in user_input for keyword in follow_up_keywords['watch']):
            # Try to extract movie title from the query
            words = user_input.split()
            movie_title = None
            
            if len(words) > 1:
                # Look for the movie title in the query
                for i, word in enumerate(words):
                    if word in follow_up_keywords['watch'] and i + 1 < len(words):
                        movie_title = ' '.join(words[i+1:])
                        break
            
            return self.get_streaming_suggestions(movie_title)
        
        # Check for cast/director information
        if any(keyword in user_input for keyword in follow_up_keywords['cast']):
            if self.current_movie:
                return f"\nAbout the cast and crew of {self.current_movie['title']}:\n" + \
                       f"Director: {self.current_movie['directors'][0]}\n" + \
                       f"Main Cast: {', '.join(self.current_movie['actors'][:3])}\n" + \
                       "Would you like to know more about any specific cast member or the director?"
            return "I'm not sure which movie you're asking about. Could you please specify the movie title?"
        
        # Handle other follow-up categories
        for category, keywords in follow_up_keywords.items():
            if any(keyword in user_input for keyword in keywords):
                if category == 'more':
                    return self.get_recommendations(self.current_preferences, is_follow_up=True)
                elif category == 'details':
                    return self.get_movie_details(user_input)
                elif category == 'similar':
                    return self.get_similar_movies(user_input)
        
        return None

    def get_similar_movies(self, user_input):
        """Get similar movie recommendations based on user input"""
        try:
            # Extract movie title from user_input
            words = user_input.lower().split()
            title = None
            
            # Check for "like this" or "similar" phrases
            if "like this" in user_input.lower():
                # Use the last recommended movie if available
                if self.last_recommendations:
                    movie = self.last_recommendations[0]
                else:
                    return "I'm not sure which movie you'd like similar recommendations for. Could you please specify the movie title?"
            else:
                # Try to find title after "like" or "similar"
                if 'like' in words:
                    title = ' '.join(words[words.index('like')+1:])
                elif 'similar' in words:
                    title = ' '.join(words[words.index('similar')+1:])
                elif 'to' in words and words.index('to') > 0:
                    title = ' '.join(words[words.index('to')+1:])
                
                if not title:
                    return "I'm not sure which movie you'd like similar recommendations for. Could you please specify the movie title?"
                
                movie = self.find_movie_by_title(title)
                if not movie:
                    return f"I couldn't find information about '{title}'. Could you please try another movie?"
            
            # Create preferences based on the movie's attributes
            similar_preferences = {
                'genres': movie.get('genres', []),
                'mood': movie.get('mood', []),
                'themes': movie.get('themes', []),
                'era': str(movie.get('year', ''))[:3] + '0s'  # Convert year to decade
            }
            
            # Get recommendations
            recommendations = self.recommender.recommend_movies(similar_preferences)
            
            if not recommendations:
                return "I couldn't find any similar movies. Could you please try a different movie?"
            
            # Format the response
            response = "\nHere are some similar movies you might enjoy:\n\n"
            for movie in recommendations:
                response += f"• {movie.get('title', 'Unknown Title')}"
                if movie.get('year'):
                    response += f" ({movie['year']})"
                response += "\n"
                if movie.get('genres'):
                    response += f"  Genres: {', '.join(movie['genres'])}\n"
                if movie.get('plot'):
                    response += f"  Plot: {movie['plot']}\n"
                response += "\n"
            
            response += "Would you like to:\n"
            response += "1. Know where to watch any of these movies?\n"
            response += "2. Get more details about a specific movie?\n"
            response += "3. Get more similar recommendations?\n"
            response += "Just let me know what you'd like to explore!"
            
            return response
            
        except Exception as e:
            print(f"Error getting similar movies: {str(e)}")
            return "I'm sorry, I encountered an error while finding similar movies. Could you please try again?"

    def get_recommendations(self, preferences, is_follow_up=False):
        try:
            # Get recommendations
            recommendations = self.recommender.recommend_movies(preferences)
            self.last_recommendations = recommendations
            
            if not recommendations:
                return "I couldn't find any movies matching your preferences. Could you please try different criteria?"
            
            # Format the response
            response = "\nHere are some movies you might like:\n\n"
            
            for i, movie in enumerate(recommendations, 1):
                # Safely get values with defaults
                title = movie.get('title', 'Unknown Title')
                year = movie.get('year', 'N/A')
                genres = movie.get('genres', [])
                directors = movie.get('directors', [])
                actors = movie.get('actors', [])
                themes = movie.get('themes', [])
                mood = movie.get('mood', 'N/A')
                plot = movie.get('plot', 'No plot available.')
                
                response += f"{i}. {title} ({year})\n"
                response += f"   Genres: {', '.join(genres)}\n"
                response += f"   Director: {directors[0] if directors else 'N/A'}\n"
                response += f"   Main Cast: {', '.join(actors[:3]) if actors else 'N/A'}\n"
                response += f"   Themes: {', '.join(themes)}\n"
                response += f"   Mood: {mood}\n"
                response += f"   Plot: {plot[:200]}...\n\n"
            
            response += "\nWould you like to:\n"
            response += "1. Know where to watch any of these movies?\n"
            response += "2. Get more details about a specific movie?\n"
            response += "3. Get similar recommendations?\n"
            response += "Just let me know what you'd like to explore!"
            
            return response
            
        except Exception as e:
            print(f"Error in get_recommendations: {str(e)}")
            return "I'm sorry, I encountered an error while processing that request. Could you please try again?"

    def get_ai_response(self, user_input):
        """Generate a system response based on the conversation state"""
        try:
            # Store the last query
            self.last_query = user_input.strip()
            user_input_lower = user_input.lower().strip()
            
            # Check for exit commands first
            if user_input_lower in ['quit', 'exit', 'bye', 'goodbye']:
                return "Goodbye! Hope you found some great movies to watch!"
            
            # Handle greetings
            greetings = ['hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 'good evening']
            if user_input_lower in greetings or user_input_lower.startswith(tuple(greetings)):
                return "Hello! I'm your MovieBuddyAI assistant. How can I help you find the perfect movie today? You can ask for recommendations based on genre, mood, actors, or tell me what kind of movie you're in the mood for!"
            
            # Extract preferences from user input first
            preferences = self.recommender.extract_preferences(user_input)
            print("Extracted preferences:", preferences)  # Debug line
            self.current_preferences = preferences
            
            # Handle mood-based queries first
            if preferences.get('mood'):
                mood = preferences['mood'][0] if isinstance(preferences['mood'], list) else preferences['mood']
                response = self.get_mood_response(mood) + "\n\n"
                recommendations = self.recommender.recommend_movies(preferences)
                
                if recommendations:
                    response += "Here are some movies that might help:\n\n"
                    for movie in recommendations:
                        response += f"• {movie.get('title', 'Unknown Title')}"
                        if movie.get('year'):
                            response += f" ({movie['year']})"
                        response += "\n"
                        if movie.get('genres'):
                            response += f"  Genres: {', '.join(movie['genres'])}\n"
                        if movie.get('plot'):
                            response += f"  Plot: {movie['plot']}\n"
                        response += "\n"
                    
                    response += "Would you like more recommendations or should I refine these based on additional preferences?"
                    return response
            
            # Check for movie details request
            if any(phrase in user_input_lower for phrase in ['tell me more about', 'about the movie', 'movie details', 'details about']):
                return self.get_movie_details(user_input)
            
            # Check for streaming availability
            if any(phrase in user_input_lower for phrase in ['where can i watch', 'how to watch', 'streaming', 'available on']):
                return self.get_streaming_suggestions(user_input)
            
            # Check for follow-up questions
            follow_up_response = self.handle_follow_up(user_input)
            if follow_up_response:
                return follow_up_response
            
            # If no preferences were extracted, ask for more specific input
            if not any(preferences.values()):
                return "I'd love to help you find the perfect movie! Could you tell me more about what you're looking for? For example:\n" + \
                       "- What genre do you prefer? (action, comedy, drama, etc.)\n" + \
                       "- How are you feeling today? (happy, sad, excited, etc.)\n" + \
                       "- Any favorite actors or directors?\n" + \
                       "- What era of movies do you like? (90s, recent, classic, etc.)"
            
            # Get recommendations based on preferences
            recommendations = self.recommender.recommend_movies(preferences)
            
            if not recommendations:
                return "I'm having trouble finding movies that match your preferences. Could you tell me more about what you're looking for?"
            
            # Format recommendations
            response = "Here are some movies you might enjoy:\n\n"
            for movie in recommendations:
                response += f"• {movie.get('title', 'Unknown Title')}"
                if movie.get('year'):
                    response += f" ({movie['year']})"
                response += "\n"
                if movie.get('genres'):
                    response += f"  Genres: {', '.join(movie['genres'])}\n"
                if movie.get('plot'):
                    response += f"  Plot: {movie['plot']}\n"
                response += "\n"
            
            response += "Would you like more recommendations or should I refine these based on additional preferences?"
            return response
            
        except Exception as e:
            print(f"Error in get_ai_response: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request. Could you please try again with different wording?"

    def chat(self):
        # Print welcome message
        self.print_welcome_message()
        
        # Start the conversation loop
        while True:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Get AI response
            response = self.get_ai_response(user_input)
            
            # Print AI response
            print("\nMovieBuddyAI:", response)
            
            # Check if user wants to exit
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                break

def main():
    buddy = MovieBuddyAI()
    buddy.chat()

if __name__ == "__main__":
    main() 