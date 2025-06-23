from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
import pandas as pd
import numpy as np
import pickle
import requests
import time
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
# Import the voice movie recommender
from voice_movie_recommender import VoiceMovieRecommender
from realtime_voice_recommender import RealTimeVoiceRecommender
from enhanced_moviebuddy_ai import EnhancedMovieBuddyAI
import os
import hashlib
import random
import string
from flask_session import Session
from functools import wraps
from datetime import datetime, timedelta
import tempfile
import asyncio

# Load NLP model and vectorizer for sentiment analysis
try:
    # load the nlp model and tfidf vectorizer from disk
    filename = 'nlp_model.pkl'
    clf = pickle.load(open(filename, 'rb'))
    vectorizer = pickle.load(open('tranform.pkl', 'rb'))
    sentiment_model_loaded = True
    print("Sentiment analysis model loaded successfully")
except Exception as e:
    print(f"Error loading sentiment analysis model: {e}")
    sentiment_model_loaded = False

# Load the updated dataset with mood information
try:
    mood_data = pd.read_csv('main_data_updated.csv')
    mood_data_loaded = True
    print("Mood dataset loaded successfully")
except Exception as e:
    print(f"Error loading mood dataset: {e}")
    mood_data_loaded = False

# Initialize the voice recommender
voice_recommender = VoiceMovieRecommender()

# Initialize the real-time voice recommender
realtime_voice_recommender = None  # Will be initialized when needed

# Initialize the enhanced MovieBuddy AI
enhanced_ai = None  # Will be initialized when needed

def create_similarity():
    data = pd.read_csv('main_data.csv')
    # creating a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    # creating a similarity score matrix
    similarity = cosine_similarity(count_matrix)
    return data, similarity


def get_movies_by_mood(mood):
    """Get movies by mood from the dataset"""
    if not mood_data_loaded:
        return []
    
    # Clean the mood string (remove emoji and trim)
    clean_mood = mood.split(' ')[0].lower() if ' ' in mood else mood.lower()
    
    # Comprehensive mood mapping that better captures the essence of each mood
    mood_mapping = {
        # Basic mappings
        'date': 'romantic',
        'joy': 'joyful',
        'excited': 'exciting',
        'adventure': 'adventurous',
        'adventurous': 'adventurous',
        'romance': 'romantic',
        'romantic': 'romantic',
        'inspiration': 'inspired',
        'inspired': 'inspired',
        'relaxed': 'relaxing',
        'energy': 'energetic',
        'energetic': 'energetic',
        'mystery': 'mysterious',
        'mystical': 'mysterious',
        'peaceful': 'calm',
        'serene': 'calm',
        'focus': 'focused',
        'focused': 'focused',
        'brave': 'courage',
        'wonder': 'intrigued',
        'melancholy': 'sad',
        'spontaneous': 'surprising',
        'playful': 'fun',
        'grateful': 'heartwarming',
        'motivated': 'inspiring',
        'chilled': 'relaxing',
        'empowered': 'powerful',
        'curious': 'intriguing',
        'cheerful': 'joyful',
        'silly': 'funny',
        'confident': 'powerful',
        'free': 'liberating',
        'quirky': 'unusual',
        'triumphant': 'victorious',
    }
    
    # Map genre preferences for moods where direct mood mapping may not work well
    # This will help find movies that match the spirit of the mood
    genre_preferences = {
        'melancholy': ['Drama', 'Romance', 'War'],
        'inspired': ['Biography', 'Drama', 'History'],
        'relaxed': ['Animation', 'Family', 'Fantasy'],
        'adventurous': ['Adventure', 'Action', 'Fantasy'],
        'romantic': ['Romance', 'Drama', 'Comedy'],
        'joyful': ['Comedy', 'Family', 'Animation'],
        'exciting': ['Action', 'Thriller', 'Sci-Fi'],
        'chilled': ['Comedy', 'Drama', 'Music'],
        'curious': ['Mystery', 'Sci-Fi', 'Thriller'],
        'empowered': ['Biography', 'Drama', 'War'],
        'sad': ['Drama', 'War', 'Romance'],
        'mysterious': ['Mystery', 'Thriller', 'Horror'],
        'quirky': ['Comedy', 'Independent', 'Drama'],
        'triumphant': ['Sport', 'Biography', 'War'],
        'brave': ['War', 'Action', 'Biography'],
    }
    
    # Apply mood mapping if available
    if clean_mood in mood_mapping:
        clean_mood = mood_mapping[clean_mood]
    
    print(f"Searching for movies with mood: {clean_mood}")
    
    # First try exact mood match
    filtered_movies = mood_data[mood_data['mood'].str.lower() == clean_mood]
    
    # If not enough exact matches, try partial mood match
    if len(filtered_movies) < 5:
        filtered_movies = mood_data[mood_data['mood'].str.lower().str.contains(clean_mood)]
    
    # If still not enough matches, use genre preferences as fallback
    if len(filtered_movies) < 5 and clean_mood in genre_preferences:
        preferred_genres = genre_preferences[clean_mood]
        genre_matches = []
        
        for genre in preferred_genres:
            # Look for movies with these genres
            genre_match = mood_data[mood_data['genres'].str.contains(genre, case=False)]
            genre_matches.append(genre_match)
        
        if genre_matches:
            # Combine all genre matches and drop duplicates
            combined_matches = pd.concat(genre_matches).drop_duplicates(subset=['movie_title'])
            
            # If we already have some mood matches, prioritize those and add genre matches
            if len(filtered_movies) > 0:
                # Only add new movies not already in filtered_movies
                new_movies = combined_matches[~combined_matches['movie_title'].isin(filtered_movies['movie_title'])]
                filtered_movies = pd.concat([filtered_movies, new_movies])
            else:
                filtered_movies = combined_matches
    
    # If still not enough movies, use alternative moods that are semantically similar
    if len(filtered_movies) < 5:
        alternative_moods = {
            'sad': ['emotional', 'touching', 'sentimental'],
            'joyful': ['happy', 'fun', 'cheerful', 'comedy'],
            'exciting': ['thrilling', 'suspenseful', 'action'],
            'romantic': ['love', 'passion', 'emotional'],
            'adventurous': ['exploration', 'journey', 'quest'],
            'mysterious': ['suspense', 'thriller', 'intriguing'],
            'relaxing': ['calm', 'peaceful', 'soothing'],
            'inspiring': ['uplifting', 'motivational', 'powerful']
        }
        
        # Find the closest alternative mood
        for key, alternatives in alternative_moods.items():
            if clean_mood in alternatives:
                # Try the main mood
                alt_mood_movies = mood_data[mood_data['mood'].str.lower() == key]
                if len(alt_mood_movies) >= 3:
                    # If we have existing movies, combine them, else just use alternative mood movies
                    if len(filtered_movies) > 0:
                        filtered_movies = pd.concat([filtered_movies, alt_mood_movies]).drop_duplicates(subset=['movie_title'])
                    else:
                        filtered_movies = alt_mood_movies
                    break
    
    # Last resort: if we still don't have enough movies, add a few curated classics based on mood
    if len(filtered_movies) < 5:
        # These are fallback movies that we'll use when no other matches are found
        fallback_movies = {
            'sad': ['titanic', 'the fault in our stars', 'schindler\'s list'],
            'joyful': ['toy story', 'the lego movie', 'despicable me'],
            'exciting': ['the dark knight', 'mission impossible', 'john wick'],
            'romantic': ['the notebook', 'pride and prejudice', 'before sunrise'],
            'adventurous': ['indiana jones', 'jurassic park', 'star wars'],
            'mysterious': ['the prestige', 'shutter island', 'gone girl'],
            'relaxing': ['the secret life of walter mitty', 'soul', 'inside out'],
            'inspiring': ['the pursuit of happyness', 'hidden figures', 'the theory of everything']
        }
        
        # Select movies from the dataset that match our fallback titles for this mood type
        closest_mood = clean_mood
        if clean_mood not in fallback_movies:
            # If our mood doesn't have fallbacks, find the closest match
            for key in fallback_movies.keys():
                if clean_mood in alternative_moods.get(key, []):
                    closest_mood = key
                    break
            # If no match found, default to a mood that has good variety
            if closest_mood == clean_mood and closest_mood not in fallback_movies:
                closest_mood = 'exciting'  # Default fallback
        
        # Look up the fallback movies in our dataset
        if closest_mood in fallback_movies:
            for fallback_title in fallback_movies[closest_mood]:
                fallback_match = mood_data[mood_data['movie_title'].str.lower().str.contains(fallback_title)]
                if not fallback_match.empty:
                    filtered_movies = pd.concat([filtered_movies, fallback_match]).drop_duplicates(subset=['movie_title'])
    
    # Ensure we don't exceed 10 movies for performance
    return filtered_movies.head(10)


def rcmd(m):
    m = m.lower()
    try:
        data.head()
        similarity.shape
    except:
        data, similarity = create_similarity()
    if m not in data['movie_title'].unique():
        return (
            'Sorry! The movie you requested is not in our database. Please check the spelling or try with some other movies')
    else:
        i = data.loc[data['movie_title'] == m].index[0]
        lst = list(enumerate(similarity[i]))
        lst = sorted(lst, key=lambda x: x[1], reverse=True)
        lst = lst[1:11]  # excluding first item since it is the requested movie itself
        l = []
        for i in range(len(lst)):
            a = lst[i][0]
            l.append(data['movie_title'][a])
        return l


# converting list of string to list (eg. "["abc","def"]" to ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["', '')
    my_list[-1] = my_list[-1].replace('"]', '')
    return my_list


def get_suggestions():
    data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.environ.get('SECRET_KEY', ''.join(random.choice(string.ascii_letters + string.digits) for i in range(30)))
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
Session(app)

# Simple user database simulation - in production, use a real database
users_db = {}

# User authentication
def hash_password(password, salt=None):
    """Hash a password with salt for secure storage"""
    if salt is None:
        salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + pwdhash

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:32]
    stored_password = stored_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash == stored_password

# Login required decorator
def login_required(f):
    """Decorator to require login for certain routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@app.route('/home')
def home():
    search_query = request.args.get('search', '')
    trending_movies = [
        {"title": "Gladiator II", "poster": "/static/glad.jpg",
         "url": "https://movieshdwatch.to/movie/watch-gladiator-ii-online-116161"},
        {"title": "Dune Prophecy", "poster": "/static/duns.jpg",
         "url": "https://movieshdwatch.to/tv/watch-dune-prophecy-online-117067"},
        {"title": "Venom: The Last Dance", "poster": "/static/vens.jpg",
         "url": "https://movieshdwatch.to/movie/watch-venom-the-last-dance-online-115885"},
        {"title": "Saturday Night 2024", "poster": "/static/sat.webp",
         "url": "https://movieshdwatch.to/movie/watch-saturday-night-online-114820"},
        {"title": "Joker: Folie à Deux", "poster": "/static/jok.jpg",
         "url": "https://movieshdwatch.to/movie/watch-joker-folie-a-deux-online-114916"},
        {"title": "Substance 2024", "poster": "/static/substance.jpg",
         "url": "https://movieshdwatch.to/movie/watch-the-substance-online-114055"}
    ]
    return render_template('home.html', suggestions=get_suggestions(), trending_movies=trending_movies, search_query=search_query)


@app.route("/similarity", methods=["POST"])
def similarity():
    movie = request.form['name']
    rc = rcmd(movie)
    if type(rc) == type('string'):
        return rc
    else:
        m_str = "---".join(rc)
        return m_str


@app.route('/search_movie', methods=['POST'])
def search_movie():
    """Handle direct movie search and redirect to the appropriate route"""
    try:
        title = request.form.get('title', '')
        print(f"Search request received for movie: '{title}'")
        
        if not title:
            print("No title provided, redirecting to home")
            return redirect(url_for('home'))
        
        # Check if movie exists in our database using rcmd function
        print(f"Checking if movie '{title}' exists in database")
        result = rcmd(title)
        
        if isinstance(result, str) and "Sorry" in result:
            print(f"Movie '{title}' not found in database")
            # Return error page
            return render_template('recommend.html', 
                               title=title,
                               error_message="Sorry! The movie you requested is not in our database. Please check the spelling or try with another movie.",
                               suggestions=get_suggestions())
        else:
            print(f"Movie '{title}' found! Redirecting to movie_details")
            # Movie exists - redirect to movie_details route with the title
            return redirect(url_for('movie_details', title=title))
    except Exception as e:
        print(f"Error in search_movie: {e}")
        # Return an error page instead of redirecting silently
        return render_template('recommend.html',
                           title=title if 'title' in locals() else "Unknown movie",
                           error_message=f"An error occurred while processing your request: {str(e)}",
                           suggestions=get_suggestions())


@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        # Check if this is a direct search with just title
        if 'title' in request.form and len(request.form) == 1:
            title = request.form['title']
            print(f"Simple search for movie: {title}")
            
            # Check if movie exists in our database using rcmd function
            result = rcmd(title)
            
            if isinstance(result, str) and "Sorry" in result:
                # Movie not found
                return render_template('recommend.html', 
                               title=title,
                               error_message="Sorry! The movie you requested is not in our database. Please check the spelling or try with another movie.",
                               suggestions=get_suggestions())
            else:
                # Movie found - redirect to home with search query to trigger the full search process
                return redirect(f'/?search={title}')
        
        # Check if this is an error case
        if 'error_message' in request.form and request.form['error_message'] == 'true':
            title = request.form['title']
            movie_id = request.form.get('movie_id', '')
            
            # Log this event for debugging
            print(f"Movie not found: {title} - Redirecting to recommend.html with error message")
            
            # Return recommend.html with error message
            return render_template('recommend.html', 
                                title=title,
                                error_message="Sorry! The movie you requested is not in our database. Please check the spelling or try with another movie.",
                                suggestions=get_suggestions())
        
        # Normal case (movie found) - existing code
        # getting data from AJAX request
        title = request.form.get('title', '')
        
        # Ensure all required fields are in the request
        required_fields = ['cast_ids', 'cast_names', 'cast_chars', 'cast_bdays', 
                           'cast_bios', 'cast_places', 'cast_profiles', 'imdb_id', 
                           'poster', 'genres', 'overview', 'rating', 'vote_count', 
                           'release_date', 'runtime', 'status', 'rec_movies', 'rec_posters']
        
        for field in required_fields:
            if field not in request.form:
                print(f"Missing required field in request: {field}")
                return redirect(f'/?search={title}')
        
        # Continue with existing code - all fields present
        cast_ids = request.form['cast_ids']
        cast_names = request.form['cast_names']
        cast_chars = request.form['cast_chars']
        cast_bdays = request.form['cast_bdays']
        cast_bios = request.form['cast_bios']
        cast_places = request.form['cast_places']
        cast_profiles = request.form['cast_profiles']
        imdb_id = request.form['imdb_id']
        poster = request.form['poster']
        genres = request.form['genres']
        overview = request.form['overview']
        vote_average = request.form['rating']
        vote_count = request.form['vote_count']
        release_date = request.form['release_date']
        runtime = request.form['runtime']
        status = request.form['status']
        rec_movies = request.form['rec_movies']
        rec_posters = request.form['rec_posters']

        # get movie suggestions for auto complete
        suggestions = get_suggestions()

        # call the convert_to_list function for every string that needs to be converted to list
        rec_movies = convert_to_list(rec_movies)
        rec_posters = convert_to_list(rec_posters)
        cast_names = convert_to_list(cast_names)
        cast_chars = convert_to_list(cast_chars)
        cast_profiles = convert_to_list(cast_profiles)
        cast_bdays = convert_to_list(cast_bdays)
        cast_bios = convert_to_list(cast_bios)
        cast_places = convert_to_list(cast_places)

        # convert string to list (eg. "[1,2,3]" to [1,2,3])
        cast_ids = cast_ids.split(',')
        cast_ids[0] = cast_ids[0].replace("[", "")
        cast_ids[-1] = cast_ids[-1].replace("]", "")

        # rendering the string to python string
        for i in range(len(cast_bios)):
            cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"', '\"')

        # combining multiple lists as a dictionary which can be passed to the html file so that it can be processed easily and the order of information will be preserved
        movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}

        casts = {cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}

        cast_details = {cast_names[i]: [cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in
                        range(len(cast_places))}
        print(f"calling imdb api: {'https://www.imdb.com/title/{}/reviews/?ref_=tt_ov_rt'.format(imdb_id)}")
        # web scraping to get user reviews from IMDB site
        url = f'https://www.imdb.com/title/{imdb_id}/reviews/?ref_=tt_ov_rt'
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

        response = requests.get(url, headers=headers)
        print(response.status_code)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            soup_result = soup.find_all("div", {"class": "ipc-html-content-inner-div"})
            print(soup_result)

            reviews_list = []  # list of reviews
            reviews_status = []  # list of comments (good or bad)
            for reviews in soup_result:
                if reviews.string:
                    reviews_list.append(reviews.string)
                    # passing the review to our model
                    if sentiment_model_loaded:
                        try:
                            movie_review_list = np.array([reviews.string])
                            movie_vector = vectorizer.transform(movie_review_list)
                            pred = clf.predict(movie_vector)
                            reviews_status.append('Good' if pred else 'Bad')
                        except Exception as e:
                            print(f"Error analyzing review: {e}")
                            reviews_status.append('Unknown')
                    else:
                        # If model isn't loaded, just use a placeholder
                        reviews_status.append('Unknown')

            # combining reviews and comments into a dictionary
            movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}

            # passing all the data to the movie_details.html file
            return render_template('movie_details.html', title=title, poster=poster, overview=overview,
                               vote_average=vote_average,
                               vote_count=vote_count, release_date=release_date, runtime=runtime, status=status,
                               genres=genres,
                               movie_cards=movie_cards, reviews=movie_reviews, casts=casts, cast_details=cast_details)
        else:
            print("Failed to retrieve reviews")
            return render_template('movie_details.html', title=title, poster=poster, overview=overview,
                               vote_average=vote_average,
                               vote_count=vote_count, release_date=release_date, runtime=runtime, status=status,
                               genres=genres,
                               movie_cards=movie_cards, reviews={}, casts=casts, cast_details=cast_details)
    except Exception as e:
        print(f"Error in recommendation: {e}")
        return jsonify({'error': str(e)}), 500


@app.route("/movie_details", methods=["GET"])
def movie_details():
    # Redirect to home if no movie parameters
    if 'title' not in request.args:
        print("No title parameter in movie_details route")
        return redirect(url_for('home'))
    
    # Get the movie title from the URL parameters
    title = request.args.get('title')
    print(f"Movie details requested for: '{title}'")
    
    # Check if the movie exists in the database
    print(f"Checking if movie '{title}' exists in database")
    result = rcmd(title)
    if isinstance(result, str) and "Sorry" in result:
        print(f"Movie '{title}' not found in database")
        # Movie not found - show error page
        return render_template('recommend.html', 
                              title=title,
                              error_message="Sorry! The movie you requested is not in our database. Please check the spelling or try with another movie.",
                              suggestions=get_suggestions())
    
    try:
        print(f"Movie '{title}' found, fetching details from TMDB API")
        # Movie exists, get details using TMDB API
        my_api_key = '3b9553fe71eb09a8552cecc1dfd02e92'
        
        # Step 1: Search for the movie to get its ID
        search_url = f'https://api.themoviedb.org/3/search/movie?api_key={my_api_key}&query={title}'
        print(f"Requesting movie search: {search_url}")
        response = requests.get(search_url)
        print(f"Search response status code: {response.status_code}")
        
        if response.status_code == 200 and response.json()['results']:
            movie_data = response.json()['results'][0]
            movie_id = movie_data['id']
            print(f"Found movie ID: {movie_id}")
            
            # Step 2: Get detailed movie information
            movie_url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={my_api_key}'
            movie_response = requests.get(movie_url)
            
            if movie_response.status_code == 200:
                movie_details = movie_response.json()
                
                # Step 3: Get movie credits
                credits_url = f'https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={my_api_key}'
                credits_response = requests.get(credits_url)
                
                if credits_response.status_code == 200:
                    credits_data = credits_response.json()
                    
                    # Process movie details
                    imdb_id = movie_details.get('imdb_id', '')
                    poster = f"https://image.tmdb.org/t/p/original{movie_details['poster_path']}" if movie_details.get('poster_path') else ""
                    overview = movie_details.get('overview', '')
                    genres = ", ".join([genre['name'] for genre in movie_details.get('genres', [])])
                    vote_average = movie_details.get('vote_average', 0)
                    vote_count = movie_details.get('vote_count', 0)
                    release_date = movie_details.get('release_date', '')
                    runtime = f"{movie_details.get('runtime', 0) // 60} hour(s) {movie_details.get('runtime', 0) % 60} min(s)"
                    status = movie_details.get('status', '')
                    
                    # Process cast data
                    cast_data = credits_data.get('cast', [])[:10]  # Get top 10 cast members
                    cast_names = []
                    cast_chars = []
                    cast_profiles = []
                    cast_ids = []
                    
                    for cast in cast_data:
                        cast_names.append(cast['name'])
                        cast_chars.append(cast['character'])
                        profile_path = cast.get('profile_path', '')
                        if profile_path:
                            cast_profiles.append(f"https://image.tmdb.org/t/p/original{profile_path}")
                        else:
                            cast_profiles.append("https://via.placeholder.com/200x300")
                        cast_ids.append(str(cast['id']))
                    
                    # Get similar movies
                    similar_url = f'https://api.themoviedb.org/3/movie/{movie_id}/similar?api_key={my_api_key}'
                    similar_response = requests.get(similar_url)
                    
                    rec_movies = []
                    rec_posters = []
                    
                    if similar_response.status_code == 200:
                        similar_data = similar_response.json()['results'][:10]
                        for movie in similar_data:
                            rec_movies.append(movie['title'])
                            poster_path = movie.get('poster_path', '')
                            if poster_path:
                                rec_posters.append(f"https://image.tmdb.org/t/p/original{poster_path}")
                            else:
                                rec_posters.append("https://via.placeholder.com/200x300")
                    
                    # Create movie cards dictionary
                    movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}
                    
                    # Create casts dictionary
                    casts = {cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}
                    
                    # Get placeholder data for missing information
                    cast_bdays = ["Not Available"] * len(cast_names)
                    cast_bios = ["Biography not available"] * len(cast_names)
                    cast_places = ["Not Available"] * len(cast_names)
                    
                    # Create cast_details dictionary
                    cast_details = {cast_names[i]: [cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_names))}
                    
                    # Get reviews if imdb_id is available
                    reviews = {}
                    
                    if imdb_id:
                        url = f'https://www.imdb.com/title/{imdb_id}/reviews/?ref_=tt_ov_rt'
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'
                        }
                        
                        try:
                            response = requests.get(url, headers=headers)
                            if response.status_code == 200:
                                soup = BeautifulSoup(response.content, 'html.parser')
                                soup_result = soup.find_all("div", {"class": "ipc-html-content-inner-div"})
                                
                                reviews_list = []
                                reviews_status = []
                                
                                for review in soup_result:
                                    if review.string:
                                        reviews_list.append(review.string)
                                        reviews_status.append('Unknown')  # Simplified - skip sentiment analysis
                                
                                reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}
                        except Exception as e:
                            print(f"Error fetching reviews: {e}")
                    
                    # Render the movie_details.html template with all the data
                    return render_template('movie_details.html',
                                       title=title,
                                       poster=poster,
                                       overview=overview,
                                       vote_average=vote_average,
                                       vote_count=vote_count,
                                       release_date=release_date,
                                       runtime=runtime,
                                       status=status,
                                       genres=genres,
                                       movie_cards=movie_cards,
                                       reviews=reviews,
                                       casts=casts,
                                       cast_details=cast_details)
        
        # If any API call fails, redirect to error
        return render_template('recommend.html',
                           title=title,
                           error_message="Sorry! We couldn't fetch the details for this movie. Please try another one.",
                           suggestions=get_suggestions())
    
    except Exception as e:
        print(f"Error in movie_details: {e}")
        return render_template('recommend.html',
                           title=title,
                           error_message="An error occurred while processing your request. Please try again.",
                           suggestions=get_suggestions())


@app.route("/recommend", methods=["GET"])
def recommend_redirect():
    # Check if this is a voice recommendation request
    if request.args.get('voice') == 'true':
        print("Voice recommendation request - rendering recommend template with voice data")
        return render_template('recommend.html', 
                            title="Voice Recommendations",
                            voice_recommendations=True,  # Flag to indicate voice recommendations
                            suggestions=get_suggestions())
    
    # For regular GET requests, render the recommend.html template with default content
    print("GET request to /recommend route - rendering recommend template")
    return render_template('recommend.html', 
                          title="Movie Recommendations",
                          suggestions=get_suggestions())


@app.route("/mood", methods=["POST"])
def mood_recommendations():
    """Handle mood-based movie recommendations"""
    try:
        mood = request.form.get('mood', '')
        print(f"Mood-based recommendation request received for: '{mood}'")
        
        if not mood:
            return jsonify({
                'status': 'error',
                'message': 'No mood provided'
            })
        
        # Get movies for this mood
        mood_movies = get_movies_by_mood(mood)
        
        if len(mood_movies) == 0:
            return jsonify({
                'status': 'error',
                'message': f"No movies found for mood: {mood}"
            })
        
        # Prepare movie data for response
        movies_data = []
        for idx, movie in mood_movies.iterrows():
            # Get poster and additional details if possible
            movie_title = movie['movie_title']
            movie_genres = movie['genres']
            
            # Call TMDB API to get movie poster
            try:
                my_api_key = '3b9553fe71eb09a8552cecc1dfd02e92'
                tmdb_info = requests.get(f'https://api.themoviedb.org/3/search/movie?api_key={my_api_key}&query={movie_title}').json()
                
                if tmdb_info['results'] and len(tmdb_info['results']) > 0:
                    poster_path = tmdb_info['results'][0]['poster_path']
                    poster = f'https://image.tmdb.org/t/p/w500{poster_path}' if poster_path else '/static/default_poster.jpg'
                    
                    # Get movie id for linking
                    movie_id = tmdb_info['results'][0]['id']
                    
                    movies_data.append({
                        'title': movie_title,
                        'poster': poster,
                        'genres': movie_genres,
                        'id': movie_id
                    })
            except Exception as e:
                print(f"Error fetching TMDB data for {movie_title}: {e}")
                # Still include the movie even without poster
                movies_data.append({
                    'title': movie_title,
                    'poster': '/static/default_poster.jpg',
                    'genres': movie_genres,
                    'id': None
                })
        
        return render_template('recommend.html',
                           title=f"{mood} Movies",
                           mood=mood,
                           mood_movies=movies_data,
                           suggestions=get_suggestions())
                           
    except Exception as e:
        print(f"Error in mood_recommendations: {e}")
        return jsonify({
            'status': 'error',
            'message': f"An error occurred: {str(e)}"
        })


@app.route("/voice_recommend", methods=["POST"])
def voice_recommend():
    """Handle voice-based movie recommendations"""
    try:
        if 'audio_data' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No audio file received'
            }), 400
            
        audio_file = request.files['audio_data']
        if not audio_file:
            return jsonify({
                'success': False,
                'error': 'Empty audio file'
            }), 400
            
        # Save audio file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, 'recording.wav')
        audio_file.save(temp_path)
        
        try:
            # Process voice input and get recommendations
            result = voice_recommender.voice_interaction()
            
            # Clean up temporary file
            os.unlink(temp_path)
            os.rmdir(temp_dir)
            
            if not result:
                return jsonify({
                    'success': False,
                    'error': 'Could not process voice input'
                }), 400
                
            return jsonify(result)
            
        except Exception as e:
            # Clean up temporary file in case of error
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
            raise e
            
    except Exception as e:
        print(f"Error in voice_recommend: {str(e)}")
        return jsonify({
            'success': False,
            'error': f"An error occurred: {str(e)}"
        }), 500


@app.route('/auth')
def auth():
    if 'user_id' in session:
        return redirect(url_for('profile'))
    return render_template('auth.html')

@app.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')
    
    if email in users_db:
        if verify_password(users_db[email]['password'], password):
            session['user_id'] = email
            session['user_name'] = users_db[email]['name']
            return jsonify({'success': True, 'redirect': url_for('profile')})
    return jsonify({'success': False, 'message': 'Invalid email or password'})

@app.route('/register', methods=['POST'])
def register():
    email = request.form.get('email')
    password = request.form.get('password')
    name = request.form.get('name')
    
    if email in users_db:
        return jsonify({'success': False, 'message': 'Email already registered'})
    
    # Create new user with secure password hashing
    users_db[email] = {
        'name': name,
        'password': hash_password(password),
        'created_at': datetime.now(),
        'watchlist': [],
        'watched': [],
        'ratings': {}
    }
    
    session['user_id'] = email
    session['user_name'] = name
    return jsonify({'success': True, 'redirect': url_for('profile')})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    user_email = session.get('user_id')
    if user_email and user_email in users_db:
        user_data = users_db[user_email]
        return render_template('profile.html', user=user_data, email=user_email)
    return redirect(url_for('logout'))

# Watchlist management
@app.route('/add_to_watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    movie_data = request.json
    user_email = session.get('user_id')
    
    if not user_email or user_email not in users_db:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Initialize watchlist if it doesn't exist
    if 'watchlist' not in users_db[user_email]:
        users_db[user_email]['watchlist'] = []
    
    # Check if movie is already in watchlist
    if not any(m.get('id') == movie_data.get('id') for m in users_db[user_email]['watchlist']):
        movie_data['added_at'] = datetime.now()
        users_db[user_email]['watchlist'].append(movie_data)
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': 'Movie already in watchlist'})

@app.route('/remove_from_watchlist', methods=['POST'])
@login_required
def remove_from_watchlist():
    movie_id = request.json.get('id')
    user_email = session.get('user_id')
    
    if not user_email or user_email not in users_db:
        return jsonify({'success': False, 'message': 'User not found'})
    
    if 'watchlist' in users_db[user_email]:
        users_db[user_email]['watchlist'] = [m for m in users_db[user_email]['watchlist'] if m.get('id') != movie_id]
    return jsonify({'success': True})

# Movie rating
@app.route('/rate_movie', methods=['POST'])
@login_required
def rate_movie():
    movie_data = request.json
    rating = movie_data.pop('rating')
    movie_id = movie_data.get('id')
    user_email = session.get('user_id')
    
    if not user_email or user_email not in users_db:
        return jsonify({'success': False, 'message': 'User not found'})
    
    # Initialize ratings if it doesn't exist
    if 'ratings' not in users_db[user_email]:
        users_db[user_email]['ratings'] = {}
    
    movie_data['rating'] = rating
    movie_data['rated_at'] = datetime.now()
    users_db[user_email]['ratings'][movie_id] = movie_data
    return jsonify({'success': True})

# Mark movie as watched
@app.route('/mark_as_watched', methods=['POST'])
@login_required
def mark_as_watched():
    """Mark a movie as watched for the current user"""
    try:
        user_email = session.get('user_id')
        if not user_email:
            return jsonify({'success': False, 'error': 'User not authenticated'}), 401
        
        data = request.get_json()
        movie_title = data.get('movie_title')
        
        if not movie_title:
            return jsonify({'success': False, 'error': 'Movie title is required'}), 400
        
        # Here you would typically save to a database
        # For now, we'll just return success
        
        return jsonify({
            'success': True,
            'message': f'Marked "{movie_title}" as watched'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error marking movie as watched: {str(e)}'
        }), 500

@app.route('/realtime_voice', methods=['GET', 'POST'])
def realtime_voice():
    """Handle real-time voice conversation"""
    try:
        if request.method == 'GET':
            # Return the real-time voice interface
            return render_template('realtime_voice.html')
        
        elif request.method == 'POST':
            # Handle real-time voice commands
            data = request.get_json()
            action = data.get('action')
            
            if action == 'start':
                # Start the real-time conversation
                return jsonify({
                    'success': True,
                    'message': 'Real-time voice conversation started',
                    'instructions': [
                        "Say 'Hey Movie Buddy' to wake up the AI",
                        "Ask for movie recommendations",
                        "Say 'goodbye' to end the conversation"
                    ]
                })
            
            elif action == 'status':
                # Return conversation status
                return jsonify({
                    'success': True,
                    'status': 'ready',
                    'message': 'Real-time voice system is ready'
                })
            
            else:
                return jsonify({
                    'success': False,
                    'error': 'Unknown action'
                }), 400
                
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error in real-time voice: {str(e)}'
        }), 500

@app.route('/launch_realtime_voice')
def launch_realtime_voice():
    """Launch the real-time voice recommender as a separate process"""
    try:
        import subprocess
        import sys
        
        # Launch the real-time voice recommender in a separate process
        process = subprocess.Popen([
            sys.executable, 'test_realtime_voice.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return jsonify({
            'success': True,
            'message': 'Real-time voice recommender launched!',
            'instructions': [
                "Check your terminal/console for the voice interface",
                "Say 'Hey Movie Buddy' to start chatting",
                "The AI will respond with voice recommendations"
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error launching real-time voice: {str(e)}'
        }), 500

@app.route('/voice_assistants')
def voice_assistants():
    """Render the voice assistants page"""
    return render_template('voice_assistants.html')

@app.route('/enhanced_voice')
def enhanced_voice():
    """Render the enhanced voice interface"""
    return render_template('enhanced_voice.html')

@app.route('/launch_enhanced_voice')
def launch_enhanced_voice():
    """Initialize the enhanced MovieBuddy AI system for web interface"""
    try:
        global enhanced_ai
        
        # Initialize enhanced AI if not already done
        if enhanced_ai is None:
            enhanced_ai = EnhancedMovieBuddyAI()
        
        return jsonify({
            'success': True,
            'message': 'Enhanced MovieBuddy AI is ready! Start speaking to interact.',
            'status': 'initialized',
            'features': [
                'Real-time emotion detection from voice',
                'Advanced movie matching algorithm',
                'Continuous conversation like Siri/Alexa',
                'Personalized recommendations',
                'Smart wake word detection'
            ],
            'instructions': [
                'Click the microphone button to start recording',
                'Say "Hey Movie Buddy" to activate the AI',
                'Ask for movie recommendations based on your mood',
                'The AI will analyze your voice emotion and provide personalized suggestions'
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Failed to initialize Enhanced MovieBuddy AI.'
        })

@app.route('/api/enhanced_voice_recommend', methods=['POST'])
def api_enhanced_voice_recommend():
    """API endpoint for enhanced voice recommendations with emotion detection"""
    try:
        global enhanced_ai
        
        # Initialize enhanced AI if not already done
        if enhanced_ai is None:
            enhanced_ai = EnhancedMovieBuddyAI()
        
        # Check if it's a file upload (audio) or text input
        if 'audio' in request.files:
            # Handle audio file upload
            audio_file = request.files['audio']
            
            # Save the audio file temporarily
            import tempfile
            import soundfile as sf
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                audio_file.save(temp_audio.name)
                
                # Process the audio file
                try:
                    # Load audio data as numpy array
                    audio_data, sample_rate = sf.read(temp_audio.name)
                    
                    # Ensure audio is in the right format
                    if len(audio_data.shape) > 1:
                        audio_data = audio_data[:, 0]  # Take first channel if stereo
                    
                    # Extract emotion from audio features
                    emotion, confidence = enhanced_ai.detect_emotion_from_audio(audio_data)
                    
                    # Transcribe the audio for text processing
                    user_input = enhanced_ai.transcribe_audio(audio_data) or "I want a movie recommendation"
                    
                    # Clean up temp file
                    os.unlink(temp_audio.name)
                    
                except Exception as audio_error:
                    # Clean up temp file on error
                    if os.path.exists(temp_audio.name):
                        os.unlink(temp_audio.name)
                    emotion = 'neutral'
                    user_input = "I want a movie recommendation"
                    
        else:
            # Handle text input
            data = request.get_json()
            user_input = data.get('text', '')
            emotion = data.get('emotion', 'neutral')
            introduction_text = data.get('introduction_text', '')
            
            # Handle introduction request
            if user_input == 'introduction' and introduction_text:
                try:
                    # Generate audio for introduction only
                    import tempfile
                    from gtts import gTTS
                    import base64
                    
                    tts = gTTS(text=introduction_text, lang='en', slow=False)
                    
                    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                        tts.save(tmp_file.name)
                        
                        # Read the audio file and encode as base64
                        with open(tmp_file.name, 'rb') as audio_file:
                            audio_data = audio_file.read()
                            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                            audio_url = f"data:audio/mp3;base64,{audio_base64}"
                        
                        # Clean up temp file
                        os.unlink(tmp_file.name)
                    
                    return jsonify({
                        'success': True,
                        'audio_url': audio_url,
                        'response': introduction_text,
                        'type': 'introduction'
                    })
                    
                except Exception as e:
                    return jsonify({
                        'success': False,
                        'error': f'Error generating introduction: {str(e)}'
                    })
            
            if not user_input:
                return jsonify({
                    'success': False,
                    'error': 'No input provided'
                })
        
        # Process the input with emotion context
        preferences = enhanced_ai.extract_enhanced_preferences(user_input, emotion)
        recommendations = enhanced_ai.get_enhanced_recommendations(preferences, n_recommendations=5)
        
        # If no recommendations found, get fallback recommendations
        if not recommendations:
            print("No specific matches found, getting popular movies...")
            # Get some popular movies as fallback
            fallback_preferences = {
                'genres': ['Comedy', 'Action', 'Drama'],
                'moods': ['entertaining', 'popular'],
                'keywords': [],
                'actors': [],
                'directors': [],
                'year_range': None,
                'emotion': emotion,
                'exclude': []
            }
            recommendations = enhanced_ai.get_enhanced_recommendations(fallback_preferences, n_recommendations=5)
        
        response = enhanced_ai.format_empathetic_response(recommendations, preferences, emotion)
        
        # Generate audio response
        audio_url = None
        try:
            # Create TTS audio file for the response
            import tempfile
            from gtts import gTTS
            import base64
            
            # Create a shorter version for TTS
            tts_text = response[:200] + "..." if len(response) > 200 else response
            tts_text = tts_text.replace('**', '').replace('\n', ' ')  # Clean formatting
            
            tts = gTTS(text=tts_text, lang='en', slow=False)
            
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp_file:
                tts.save(tmp_file.name)
                
                # Read the audio file and encode as base64
                with open(tmp_file.name, 'rb') as audio_file:
                    audio_data = audio_file.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    audio_url = f"data:audio/mp3;base64,{audio_base64}"
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                
        except Exception as audio_error:
            print(f"Warning: Could not generate audio response: {audio_error}")
        
        # Format recommendations for web display
        formatted_recommendations = []
        for movie in recommendations[:5]:  # Limit to top 5
            # Format genres
            genres = movie.get('genres', [])
            if isinstance(genres, list):
                genres_text = ', '.join(genres[:3])  # Top 3 genres
            else:
                genres_text = str(genres)
            
            # Format actors
            actors = movie.get('actors', [])
            if isinstance(actors, list):
                actors_text = ', '.join(actors[:3])  # Top 3 actors
            else:
                actors_text = str(actors)
            
            # Format directors
            directors = movie.get('directors', [])
            if isinstance(directors, list):
                directors_text = ', '.join(directors[:2])  # Top 2 directors
            else:
                directors_text = str(directors)
            
            formatted_recommendations.append({
                'title': movie['title'],
                'year': movie.get('year', 'N/A'),
                'genres': genres_text or 'N/A',
                'imdb_score': f"{movie.get('imdb_score', 0):.1f}" if movie.get('imdb_score') else 'N/A',
                'actors': actors_text or 'N/A',
                'directors': directors_text or 'N/A',
                'mood': ', '.join(movie.get('mood', [])) if movie.get('mood') else 'N/A',
                'description': f"Perfect for when you're feeling {emotion}!"
            })
        
        return jsonify({
            'success': True,
            'recommendations': formatted_recommendations,
            'response': response,
            'audio_url': audio_url,
            'detected_emotion': emotion,
            'preferences': preferences,
            'user_input': user_input,
            'total_found': len(recommendations)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error processing your request. Please try again.'
        })

if __name__ == '__main__':
    app.run(debug=True)