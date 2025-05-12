"""
API Routes for MoodFlix application.
Defines all API endpoints for the application.
"""
from flask import Blueprint, request, jsonify, current_app
import os
import tempfile
from werkzeug.utils import secure_filename

from app.services.movie_service import MovieService
from app.services.speech_service import SpeechService
from app.services.mood_service import MoodService
from app.services.moviebuddy_service import MovieBuddyService
from app.core.config import settings

# Initialize blueprint
api_bp = Blueprint('api', __name__)

# Initialize services
movie_service = MovieService()
speech_service = SpeechService()
mood_service = MoodService()
moviebuddy_service = MovieBuddyService(movie_service=movie_service, mood_service=mood_service)

# History storage (will be replaced with database in future)
recommendation_history = []

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'version': settings.VERSION,
        'name': settings.PROJECT_NAME
    })

@api_bp.route('/chat', methods=['POST'])
def chat():
    """Process text chat input and return movie recommendations."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Extract preferences from user message
        preferences = mood_service.extract_preferences(user_message)
        
        # Get movie recommendations
        recommendations = movie_service.recommend_movies(preferences)
        
        # Format the response
        if recommendations:
            response = {
                'type': 'recommendations',
                'movies': [movie.to_dict() for movie in recommendations]
            }
            
            # Store in history
            recommendation_history.append({
                'timestamp': movie_service.get_timestamp(),
                'mood': preferences.get('mood', 'unknown'),
                'recommendations': [movie.to_dict() for movie in recommendations[:3]]
            })
            
            # Keep history at a reasonable size
            if len(recommendation_history) > 10:
                recommendation_history.pop(0)
        else:
            response = {
                'type': 'error',
                'message': "I couldn't find any movies matching your preferences. Could you try different criteria?"
            }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/voice', methods=['POST'])
def voice():
    """Process voice input and return movie recommendations."""
    try:
        # Check if file is provided
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'error': 'Empty audio file'}), 400
        
        # Save the file temporarily
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        # Transcribe the audio
        transcription = speech_service.transcribe_audio(filepath)
        
        if not transcription:
            return jsonify({'error': 'Could not transcribe audio'}), 400
        
        # Extract preferences from transcription
        preferences = mood_service.extract_preferences(transcription)
        
        # Get movie recommendations
        recommendations = movie_service.recommend_movies(preferences)
        
        # Format the response
        if recommendations:
            response = {
                'type': 'recommendations',
                'transcription': transcription,
                'movies': [movie.to_dict() for movie in recommendations]
            }
            
            # Store in history
            recommendation_history.append({
                'timestamp': movie_service.get_timestamp(),
                'mood': preferences.get('mood', 'unknown'),
                'transcription': transcription,
                'recommendations': [movie.to_dict() for movie in recommendations[:3]]
            })
            
            # Keep history at a reasonable size
            if len(recommendation_history) > 10:
                recommendation_history.pop(0)
        else:
            response = {
                'type': 'error',
                'message': "I couldn't find any movies matching your preferences. Could you try different criteria?"
            }
        
        # Clean up temporary file
        os.remove(filepath)
        os.rmdir(temp_dir)
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in voice endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/history', methods=['GET'])
def history():
    """Get recommendation history."""
    return jsonify({
        'success': True,
        'history': recommendation_history
    })

@api_bp.route('/movie_details', methods=['POST'])
def movie_details():
    """Get details for a specific movie."""
    try:
        data = request.get_json()
        movie_title = data.get('title', '').strip()
        
        if not movie_title:
            return jsonify({'error': 'Movie title is required'}), 400
        
        # Find movie details
        movie = movie_service.find_movie_by_title(movie_title)
        
        if movie:
            response = {
                'type': 'movie_details',
                'movie': movie.to_dict()
            }
        else:
            response = {
                'type': 'error',
                'message': f"Couldn't find details for movie: {movie_title}"
            }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in movie_details endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/similar_movies', methods=['POST'])
def similar_movies():
    """Get similar movies to a given movie."""
    try:
        data = request.get_json()
        movie_title = data.get('title', '').strip()
        
        if not movie_title:
            return jsonify({'error': 'Movie title is required'}), 400
        
        # Find similar movies
        movie = movie_service.find_movie_by_title(movie_title)
        if movie:
            # Create preferences based on the movie's attributes
            preferences = {
                'genres': movie.genres,
                'mood': movie.mood if hasattr(movie, 'mood') else None,
                'year': movie.year
            }
            
            similar_movies = movie_service.recommend_movies(preferences)
            
            if similar_movies:
                response = {
                    'type': 'similar_movies',
                    'movies': [m.to_dict() for m in similar_movies if m.title != movie_title]
                }
            else:
                response = {
                    'type': 'error',
                    'message': f"Couldn't find similar movies for: {movie_title}"
                }
        else:
            response = {
                'type': 'error',
                'message': f"Couldn't find movie: {movie_title}"
            }
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in similar_movies endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/set_volume', methods=['POST'])
def set_volume():
    """Set the text-to-speech volume."""
    try:
        data = request.get_json()
        volume = data.get('volume', 0.9)
        
        # Validate volume
        volume = max(0.0, min(1.0, float(volume)))
        
        # Set the volume
        speech_service.set_volume(volume)
        
        return jsonify({
            'success': True,
            'volume': volume
        })
        
    except Exception as e:
        current_app.logger.error(f"Error setting volume: {str(e)}")
        return jsonify({'error': str(e)}), 500

@api_bp.route('/moviebuddy', methods=['POST'])
def moviebuddy_voice():
    """Process voice input with MovieBuddy AI for enhanced conversational recommendations."""
    try:
        # Check if file is provided
        if 'audio_data' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        file = request.files['audio_data']
        if file.filename == '':
            return jsonify({'error': 'Empty audio file'}), 400
        
        # Save the file temporarily
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)
        
        # Transcribe the audio
        transcription = speech_service.transcribe_audio(filepath)
        
        if not transcription:
            # Clean up temporary file
            os.remove(filepath)
            os.rmdir(temp_dir)
            return jsonify({
                'success': False,
                'error': 'Could not transcribe audio'
            }), 400
        
        # Get user ID from session or use default
        user_id = request.form.get('user_id', 'default_user')
        
        # Process with MovieBuddy AI
        response = moviebuddy_service.process_voice_input(user_id, transcription)
        
        # Add transcription to response
        response['transcript'] = transcription
        
        # Store in history if recommendations were made
        if 'recommendations' in response and response['recommendations']:
            recommendation_history.append({
                'timestamp': movie_service.get_timestamp(),
                'mood': response.get('mood', 'unknown'),
                'transcription': transcription,
                'recommendations': response['recommendations'][:3] if len(response['recommendations']) > 3 else response['recommendations']
            })
            
            # Keep history at a reasonable size
            if len(recommendation_history) > 10:
                recommendation_history.pop(0)
        
        # Clean up temporary file
        os.remove(filepath)
        os.rmdir(temp_dir)
        
        return jsonify(response)
        
    except Exception as e:
        current_app.logger.error(f"Error in MovieBuddy AI voice endpoint: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/clear_conversation', methods=['POST'])
def clear_conversation():
    """Clear the conversation history for a user."""
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'default_user')
        
        # Clear conversation in MovieBuddy service
        moviebuddy_service.clear_conversation(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Conversation cleared successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error clearing conversation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
