"""
Web Routes for MoodFlix application.
Defines all web page routes for the application.
"""
from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
import os
from app.services.movie_service import MovieService
from app.services.speech_service import SpeechService
from app.services.mood_service import MoodService
from app.services.tmdb_service import TMDBService
from app.services.user_service import UserService
from app.core.config import settings

# Initialize blueprint
web_bp = Blueprint('web', __name__, template_folder='../templates', static_folder='../static')

# Initialize services
movie_service = MovieService()
speech_service = SpeechService()
mood_service = MoodService()
tmdb_service = TMDBService()
user_service = UserService()

@web_bp.route('/', methods=['GET'])
def index():
    """Home page."""
    # Get trending movies for the homepage
    trending_movies = movie_service.get_trending_movies(limit=10)
    return render_template('index.html', trending_movies=trending_movies)

@web_bp.route('/mood', methods=['GET'])
def mood_page():
    """Mood selection page."""
    return render_template('mood.html')

@web_bp.route('/recommendations', methods=['GET', 'POST'])
def recommendations():
    """Movie recommendations page."""
    if request.method == 'POST':
        # Get mood from form
        mood = request.form.get('mood', '')
        genres = request.form.getlist('genres')
        year_range = request.form.get('year_range', '')
        
        # Create preferences dictionary
        preferences = {
            'mood': mood,
            'genres': genres
        }
        
        if year_range:
            try:
                start_year, end_year = year_range.split('-')
                preferences['year_range'] = (int(start_year), int(end_year))
            except (ValueError, TypeError):
                pass
        
        # Get recommendations
        recommendations = movie_service.recommend_movies(preferences)
        return render_template('recommendations.html', movies=recommendations, preferences=preferences)
    
    # If GET request, show empty recommendations page
    return render_template('recommendations.html', movies=[], preferences={})

@web_bp.route('/movie/<movie_title>', methods=['GET'])
def movie_detail(movie_title):
    """Movie detail page."""
    movie = movie_service.find_movie_by_title(movie_title)
    if not movie:
        return render_template('error.html', message=f"Movie '{movie_title}' not found"), 404
    
    # Get similar movies
    preferences = {
        'genres': movie.genres,
        'mood': movie.mood if hasattr(movie, 'mood') else None,
        'year': movie.year
    }
    similar_movies = movie_service.recommend_movies(preferences)
    similar_movies = [m for m in similar_movies if m.title != movie_title][:5]
    
    return render_template('movie_detail.html', movie=movie, similar_movies=similar_movies)

@web_bp.route('/voice', methods=['GET'])
def voice_interface():
    """Voice interface page."""
    return render_template('voice.html')

@web_bp.route('/profile', methods=['GET'])
def profile():
    """User profile page."""
    # For now, just show a dummy profile
    # In the future, this will be tied to user authentication
    user = user_service.get_user_by_id("default_user")
    if not user:
        user = user_service.create_user("default_user", "Default User")
    
    # Get user's recommendation history
    history = user_service.get_user_history(user.id)
    
    return render_template('profile.html', user=user, history=history)

@web_bp.route('/about', methods=['GET'])
def about():
    """About page."""
    return render_template('about.html')

@web_bp.route('/login', methods=['GET'])
def login():
    """Login page."""
    return render_template('login.html')

@web_bp.route('/register', methods=['GET'])
def register():
    """Registration page."""
    return render_template('register.html')
