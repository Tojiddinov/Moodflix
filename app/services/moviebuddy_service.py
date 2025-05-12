"""
MovieBuddy AI Service module for MoodFlix application.
Provides advanced conversational AI capabilities for movie recommendations.
"""
import re
import json
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.movie_service import MovieService
from app.services.mood_service import MoodService
from app.services.user_service import UserService
from app.models.movie import Movie

class MovieBuddyService:
    """Advanced conversational AI service for movie recommendations."""
    
    def __init__(self, movie_service: MovieService = None, mood_service: MoodService = None, user_service: UserService = None):
        """Initialize MovieBuddy AI service."""
        self.movie_service = movie_service or MovieService()
        self.mood_service = mood_service or MoodService()
        self.user_service = user_service or UserService()
        
        # Conversation state
        self.conversation_history = {}  # User ID -> list of messages
        self.current_context = {}  # User ID -> current context
        
        # Greeting templates
        self.greetings = [
            "Hey there! I'm MovieBuddy AI. What kind of movie are you in the mood for today?",
            "Hello! I'm your MovieBuddy AI assistant. Tell me what you're feeling like watching!",
            "Hi! MovieBuddy AI here. What type of movie would you like to watch?",
            "Welcome to MoodFlix! I'm MovieBuddy AI, ready to find your perfect movie match. What are you in the mood for?"
        ]
        
        # Follow-up templates
        self.follow_ups = [
            "Would you like more specific recommendations?",
            "Is there a particular actor or director you're interested in?",
            "Would you prefer something more recent or a classic?",
            "Any specific genre you'd like to focus on?",
            "Would you like me to recommend something similar to a movie you've enjoyed before?"
        ]
        
        # Response templates for different intents
        self.response_templates = {
            "greeting": [
                "Hello! I'm MovieBuddy AI. How can I help you find a movie today?",
                "Hi there! I'm your personal movie recommendation assistant. What kind of movie are you looking for?",
                "Hey! I'm MovieBuddy AI. Tell me what you're in the mood for, and I'll find the perfect movie for you!"
            ],
            "recommendation": [
                "Based on your mood, I think you might enjoy {movie_titles}.",
                "I've found some movies that match your preferences: {movie_titles}.",
                "Here are some recommendations for you: {movie_titles}."
            ],
            "no_results": [
                "I couldn't find any movies matching your criteria. Could you try different preferences?",
                "I don't have any movies that match exactly what you're looking for. Maybe try broadening your criteria?",
                "No exact matches found. Would you like to try a different genre or mood?"
            ],
            "clarification": [
                "Could you tell me more about what kind of movie you're looking for?",
                "I'd like to understand your preferences better. What genres or themes do you enjoy?",
                "To give you better recommendations, could you share more about your movie preferences?"
            ],
            "thanks": [
                "You're welcome! I'm happy to help you find great movies to watch.",
                "My pleasure! Let me know if you need more recommendations.",
                "Glad I could help! Enjoy your movie!"
            ]
        }
        
        # Intent recognition patterns
        self.intent_patterns = {
            "greeting": [
                r"(?:hello|hi|hey|greetings|howdy)",
                r"^(?:good\s+(?:morning|afternoon|evening))"
            ],
            "thanks": [
                r"(?:thanks|thank\s+you|thx)",
                r"(?:appreciate\s+it)"
            ],
            "recommendation": [
                r"(?:recommend|suggest|find)(?:\s+me)?(?:\s+a)?(?:\s+movie)?",
                r"(?:what\s+(?:movie|film)(?:\s+should\s+I\s+watch)?)",
                r"(?:I'm\s+(?:in\s+the\s+mood|looking)\s+for)"
            ],
            "specific_movie": [
                r"(?:tell\s+me\s+about|what\s+is|how\s+is)(?:\s+the\s+movie)?\s+([A-Za-z0-9\s]+)",
                r"(?:have\s+you\s+(?:seen|heard\s+of))\s+([A-Za-z0-9\s]+)"
            ],
            "actor": [
                r"(?:movies?\s+with|starring|featuring)\s+([A-Za-z\s]+)",
                r"(?:what\s+(?:has|did)\s+([A-Za-z\s]+)\s+(?:been\s+in|starred\s+in|acted\s+in))"
            ],
            "director": [
                r"(?:movies?\s+(?:by|directed\s+by))\s+([A-Za-z\s]+)",
                r"(?:what\s+(?:has|did)\s+([A-Za-z\s]+)\s+direct(?:ed)?)"
            ],
            "genre": [
                r"(?:I\s+(?:like|enjoy|love|want)\s+(?:to\s+watch)?\s+([A-Za-z\s]+)\s+movies)",
                r"(?:show\s+me\s+(?:some)?\s+([A-Za-z\s]+)\s+movies)"
            ],
            "year": [
                r"(?:movies?\s+from\s+(?:the\s+)?(\d{4}s?|\d{4}))",
                r"(?:(\d{4}s?|\d{4})\s+movies?)"
            ],
            "mood": [
                r"(?:I'm\s+feeling\s+([A-Za-z\s]+))",
                r"(?:I\s+feel\s+([A-Za-z\s]+))",
                r"(?:I'm\s+in\s+a\s+([A-Za-z\s]+)\s+mood)"
            ]
        }
    
    def process_voice_input(self, user_id: str, transcription: str) -> Dict[str, Any]:
        """
        Process voice input and generate a response with movie recommendations.
        
        Args:
            user_id: User ID for personalization
            transcription: Transcribed text from voice input
            
        Returns:
            Response with recommendations and conversation context
        """
        # Initialize user conversation history if not exists
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            self.current_context[user_id] = {
                "last_recommendations": [],
                "last_query": None,
                "follow_up_count": 0,
                "preferences": {}
            }
        
        # Add user message to history
        self.conversation_history[user_id].append({
            "role": "user",
            "content": transcription,
            "timestamp": datetime.now().isoformat()
        })
        
        # Analyze intent
        intent, entities = self._analyze_intent(transcription)
        
        # Get user context
        context = self.current_context[user_id]
        
        # Update context with new entities
        if entities:
            if "preferences" not in context:
                context["preferences"] = {}
            
            for key, value in entities.items():
                if key in ["genre", "genres"] and value:
                    if "genres" not in context["preferences"]:
                        context["preferences"]["genres"] = []
                    if isinstance(value, list):
                        context["preferences"]["genres"].extend(value)
                    else:
                        context["preferences"]["genres"].append(value)
                elif key == "mood" and value:
                    context["preferences"]["mood"] = value
                elif key == "year" and value:
                    context["preferences"]["year"] = value
                elif key == "actor" and value:
                    context["preferences"]["actor"] = value
                elif key == "director" and value:
                    context["preferences"]["director"] = value
        
        # Process intent
        response = {}
        waiting_for_follow_up = False
        
        if intent == "greeting":
            response["response"] = random.choice(self.response_templates["greeting"])
            waiting_for_follow_up = True
            
        elif intent == "thanks":
            response["response"] = random.choice(self.response_templates["thanks"])
            
        elif intent == "specific_movie" and entities.get("movie_title"):
            movie_title = entities["movie_title"]
            movie = self.movie_service.find_movie_by_title(movie_title)
            
            if movie:
                response["response"] = f"I found '{movie.title}' ({movie.year}). {movie.overview[:150]}..."
                response["movie"] = movie.to_dict()
            else:
                response["response"] = f"I couldn't find information about '{movie_title}'. Would you like me to recommend something similar?"
                waiting_for_follow_up = True
        
        elif intent == "recommendation" or intent == "mood" or intent == "genre":
            # Extract preferences from transcription
            preferences = self.mood_service.extract_preferences(transcription)
            
            # Merge with context preferences
            if "preferences" in context:
                for key, value in context["preferences"].items():
                    if key not in preferences or not preferences[key]:
                        preferences[key] = value
            
            # Get recommendations
            recommendations = self.movie_service.recommend_movies(preferences)
            
            if recommendations:
                # Format movie titles for response
                movie_titles = ", ".join([f"'{movie.title}'" for movie in recommendations[:3]])
                
                # Generate response
                template = random.choice(self.response_templates["recommendation"])
                response_text = template.format(movie_titles=movie_titles)
                
                # Add follow-up question
                if random.random() < 0.7:  # 70% chance to add follow-up
                    response_text += f" {random.choice(self.follow_ups)}"
                    waiting_for_follow_up = True
                
                response["response"] = response_text
                response["recommendations"] = [movie.to_dict() for movie in recommendations]
                
                # Update context
                context["last_recommendations"] = [movie.title for movie in recommendations]
                context["last_query"] = transcription
                context["follow_up_count"] += 1
            else:
                response["response"] = random.choice(self.response_templates["no_results"])
                waiting_for_follow_up = True
        
        else:
            # Default to clarification if intent not recognized
            response["response"] = random.choice(self.response_templates["clarification"])
            waiting_for_follow_up = True
        
        # Add response to conversation history
        self.conversation_history[user_id].append({
            "role": "assistant",
            "content": response["response"],
            "timestamp": datetime.now().isoformat()
        })
        
        # Update context
        self.current_context[user_id] = context
        
        # Add waiting_for_follow_up flag
        response["waiting_for_follow_up"] = waiting_for_follow_up
        
        # Add success flag
        response["success"] = True
        
        # Add transcript
        response["transcript"] = transcription
        
        return response
    
    def _analyze_intent(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analyze the intent and extract entities from user input.
        
        Args:
            text: User input text
            
        Returns:
            Tuple of (intent, entities)
        """
        text = text.lower().strip()
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Extract entities based on intent
                    entities = {}
                    
                    if intent == "specific_movie" and len(match.groups()) > 0:
                        entities["movie_title"] = match.group(1).strip()
                    
                    elif intent == "actor" and len(match.groups()) > 0:
                        entities["actor"] = match.group(1).strip()
                    
                    elif intent == "director" and len(match.groups()) > 0:
                        entities["director"] = match.group(1).strip()
                    
                    elif intent == "genre" and len(match.groups()) > 0:
                        genre = match.group(1).strip()
                        # Check if it's a valid genre
                        if genre.lower() in self.mood_service.genres:
                            entities["genre"] = genre.lower()
                    
                    elif intent == "year" and len(match.groups()) > 0:
                        entities["year"] = match.group(1).strip()
                    
                    elif intent == "mood" and len(match.groups()) > 0:
                        mood = match.group(1).strip()
                        # Check if it's a valid mood
                        if mood.lower() in self.mood_service.moods:
                            entities["mood"] = mood.lower()
                    
                    # Also extract preferences using mood service
                    preferences = self.mood_service.extract_preferences(text)
                    entities.update(preferences)
                    
                    return intent, entities
        
        # Default to recommendation intent if no specific intent found
        preferences = self.mood_service.extract_preferences(text)
        return "recommendation", preferences
    
    def get_greeting(self) -> str:
        """
        Get a random greeting message.
        
        Returns:
            Greeting message
        """
        return random.choice(self.greetings)
    
    def get_follow_up(self) -> str:
        """
        Get a random follow-up question.
        
        Returns:
            Follow-up question
        """
        return random.choice(self.follow_ups)
    
    def clear_conversation(self, user_id: str) -> None:
        """
        Clear the conversation history for a user.
        
        Args:
            user_id: User ID
        """
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []
            self.current_context[user_id] = {
                "last_recommendations": [],
                "last_query": None,
                "follow_up_count": 0,
                "preferences": {}
            }
    
    def get_conversation_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of conversation messages
        """
        return self.conversation_history.get(user_id, [])
