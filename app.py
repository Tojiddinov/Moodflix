from flask import Flask, render_template, request, jsonify, session
from voice_movie_recommender import VoiceMovieRecommender
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a secure secret key

# Initialize MovieBuddyAI
movie_buddy = VoiceMovieRecommender()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Get recommendations from MovieBuddyAI
        preferences = movie_buddy.extract_preferences(user_message)
        recommendations = movie_buddy.recommend_movies(preferences)
        
        # Format the response
        if recommendations:
            response = {
                'type': 'recommendations',
                'movies': []
            }
            
            for movie in recommendations:
                movie_data = {
                    'title': movie.get('title', 'Unknown Title'),
                    'year': movie.get('year', 'N/A'),
                    'genres': movie.get('genres', []),
                    'plot': movie.get('plot', 'No plot available'),
                    'actors': movie.get('actors', [])[:3],  # Get top 3 actors
                    'directors': movie.get('directors', []),
                    'mood': movie.get('mood', 'N/A')
                }
                response['movies'].append(movie_data)
        else:
            response = {
                'type': 'error',
                'message': "I couldn't find any movies matching your preferences. Could you try different criteria?"
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie_details', methods=['POST'])
def movie_details():
    try:
        data = request.get_json()
        movie_title = data.get('title', '').strip()
        
        if not movie_title:
            return jsonify({'error': 'Movie title is required'}), 400
        
        # Find movie details
        movie = movie_buddy.find_movie_by_title(movie_title)
        
        if movie:
            response = {
                'type': 'movie_details',
                'movie': {
                    'title': movie.get('title', 'Unknown Title'),
                    'year': movie.get('year', 'N/A'),
                    'genres': movie.get('genres', []),
                    'plot': movie.get('plot', 'No plot available'),
                    'actors': movie.get('actors', [])[:3],
                    'directors': movie.get('directors', []),
                    'mood': movie.get('mood', 'N/A'),
                    'themes': movie.get('themes', [])
                }
            }
        else:
            response = {
                'type': 'error',
                'message': f"Couldn't find details for movie: {movie_title}"
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/similar_movies', methods=['POST'])
def similar_movies():
    try:
        data = request.get_json()
        movie_title = data.get('title', '').strip()
        
        if not movie_title:
            return jsonify({'error': 'Movie title is required'}), 400
        
        # Find similar movies
        movie = movie_buddy.find_movie_by_title(movie_title)
        if movie:
            # Create preferences based on the movie's attributes
            preferences = {
                'genres': movie.get('genres', []),
                'mood': movie.get('mood', []),
                'themes': movie.get('themes', []),
                'era': str(movie.get('year', ''))[:3] + '0s'
            }
            
            similar_movies = movie_buddy.recommend_movies(preferences)
            
            if similar_movies:
                response = {
                    'type': 'similar_movies',
                    'movies': []
                }
                
                for movie in similar_movies:
                    movie_data = {
                        'title': movie.get('title', 'Unknown Title'),
                        'year': movie.get('year', 'N/A'),
                        'genres': movie.get('genres', []),
                        'plot': movie.get('plot', 'No plot available'),
                        'actors': movie.get('actors', [])[:3],
                        'directors': movie.get('directors', []),
                        'mood': movie.get('mood', 'N/A')
                    }
                    response['movies'].append(movie_data)
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
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True) 