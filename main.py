from flask import Flask, render_template, request, jsonify, redirect, url_for
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
        # Check if the request contains audio data
        if 'audio_data' in request.files:
            # Save the audio file temporarily
            audio_file = request.files['audio_data']
            temp_filename = f"temp_recording_{int(time.time())}.wav"
            audio_file.save(temp_filename)
            
            # Transcribe the audio using Deepgram
            transcript = voice_recommender.transcribe_audio(temp_filename)
            
            if not transcript:
                return jsonify({
                    "success": False,
                    "error": "Failed to transcribe audio. Please try again.",
                    "transcript": ""
                })
            
            # Extract preferences from the transcript
            voice_recommender.extract_preferences(transcript)
            
            # Get movie recommendations based on the extracted preferences
            recommendations = voice_recommender.recommend_movies(limit=5)
            
            if not recommendations:
                return jsonify({
                    "success": False,
                    "error": "No movies found matching your preferences. Try different criteria.",
                    "transcript": transcript
                })
            
            # Use TMDB API to get posters and additional details
            my_api_key = '3b9553fe71eb09a8552cecc1dfd02e92'
            formatted_recs = []
            
            for movie in recommendations:
                movie_title = movie["title"]
                # Search for the movie in TMDB
                search_url = f'https://api.themoviedb.org/3/search/movie?api_key={my_api_key}&query={movie_title}'
                
                try:
                    response = requests.get(search_url)
                    if response.status_code == 200 and response.json()['results']:
                        tmdb_movie = response.json()['results'][0]
                        
                        # Get poster path, or use placeholder if not available
                        poster_path = tmdb_movie.get('poster_path', '')
                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else f"https://via.placeholder.com/300x450.png?text={movie_title.replace(' ', '+')}"
                        
                        # Get TMDB movie ID for linking to details
                        tmdb_id = tmdb_movie.get('id')
                        
                        # Get release year from TMDB if not in our data
                        year = movie.get("year")
                        if not year and 'release_date' in tmdb_movie and tmdb_movie['release_date']:
                            try:
                                year = int(tmdb_movie['release_date'][:4])
                            except:
                                pass
                        
                        formatted_recs.append({
                            "title": movie_title,
                            "year": year,
                            "genres": ", ".join(movie["genres"]) if movie.get("genres") else "",
                            "plot": tmdb_movie.get('overview') or movie.get("plot", ""),
                            "poster": poster_url,
                            "tmdb_id": tmdb_id
                        })
                    else:
                        # If not found in TMDB, use our data with placeholder
                        formatted_recs.append({
                            "title": movie_title,
                            "year": movie.get("year"),
                            "genres": ", ".join(movie["genres"]) if movie.get("genres") else "",
                            "plot": movie.get("plot", ""),
                            "poster": f"https://via.placeholder.com/300x450.png?text={movie_title.replace(' ', '+')}",
                            "tmdb_id": None
                        })
                except Exception as e:
                    print(f"Error fetching TMDB data for {movie_title}: {e}")
                    # Use placeholder data if API call fails
                    formatted_recs.append({
                        "title": movie_title,
                        "year": movie.get("year"),
                        "genres": ", ".join(movie["genres"]) if movie.get("genres") else "",
                        "plot": movie.get("plot", ""),
                        "poster": f"https://via.placeholder.com/300x450.png?text={movie_title.replace(' ', '+')}",
                        "tmdb_id": None
                    })
            
            # Return the recommendations along with the transcript
            return jsonify({
                "success": True,
                "transcript": transcript,
                "recommendations": formatted_recs,
                "preferences": voice_recommender.user_preferences
            })
        
        # If no audio file was provided, check for a text transcript
        elif 'transcript' in request.json:
            transcript = request.json['transcript']
            
            # Extract preferences from the transcript
            voice_recommender.extract_preferences(transcript)
            
            # Get movie recommendations based on the extracted preferences
            recommendations = voice_recommender.recommend_movies(limit=5)
            
            if not recommendations:
                return jsonify({
                    "success": False,
                    "error": "No movies found matching your preferences. Try different criteria.",
                    "transcript": transcript
                })
            
            # Use TMDB API to get posters and additional details
            my_api_key = '3b9553fe71eb09a8552cecc1dfd02e92'
            formatted_recs = []
            
            for movie in recommendations:
                movie_title = movie["title"]
                # Search for the movie in TMDB
                search_url = f'https://api.themoviedb.org/3/search/movie?api_key={my_api_key}&query={movie_title}'
                
                try:
                    response = requests.get(search_url)
                    if response.status_code == 200 and response.json()['results']:
                        tmdb_movie = response.json()['results'][0]
                        
                        # Get poster path, or use placeholder if not available
                        poster_path = tmdb_movie.get('poster_path', '')
                        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else f"https://via.placeholder.com/300x450.png?text={movie_title.replace(' ', '+')}"
                        
                        # Get TMDB movie ID for linking to details
                        tmdb_id = tmdb_movie.get('id')
                        
                        # Get release year from TMDB if not in our data
                        year = movie.get("year")
                        if not year and 'release_date' in tmdb_movie and tmdb_movie['release_date']:
                            try:
                                year = int(tmdb_movie['release_date'][:4])
                            except:
                                pass
                        
                        formatted_recs.append({
                            "title": movie_title,
                            "year": year,
                            "genres": ", ".join(movie["genres"]) if movie.get("genres") else "",
                            "plot": tmdb_movie.get('overview') or movie.get("plot", ""),
                            "poster": poster_url,
                            "tmdb_id": tmdb_id
                        })
                    else:
                        # If not found in TMDB, use our data with placeholder
                        formatted_recs.append({
                            "title": movie_title,
                            "year": movie.get("year"),
                            "genres": ", ".join(movie["genres"]) if movie.get("genres") else "",
                            "plot": movie.get("plot", ""),
                            "poster": f"https://via.placeholder.com/300x450.png?text={movie_title.replace(' ', '+')}",
                            "tmdb_id": None
                        })
                except Exception as e:
                    print(f"Error fetching TMDB data for {movie_title}: {e}")
                    # Use placeholder data if API call fails
                    formatted_recs.append({
                        "title": movie_title,
                        "year": movie.get("year"),
                        "genres": ", ".join(movie["genres"]) if movie.get("genres") else "",
                        "plot": movie.get("plot", ""),
                        "poster": f"https://via.placeholder.com/300x450.png?text={movie_title.replace(' ', '+')}",
                        "tmdb_id": None
                    })
            
            # Return the recommendations along with the transcript
            return jsonify({
                "success": True,
                "transcript": transcript,
                "recommendations": formatted_recs,
                "preferences": voice_recommender.user_preferences
            })
        
        else:
            return jsonify({
                "success": False,
                "error": "No audio data or transcript provided",
                "transcript": ""
            })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e),
            "transcript": ""
        })


if __name__ == '__main__':
    app.run(debug=True)