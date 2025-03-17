from email.mime import application
import numpy as np
import pandas as pd
from flask import Flask, render_template, request
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
from bs4 import BeautifulSoup
import pickle
import requests



from flask import Flask, render_template, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import numpy as np
from bs4 import BeautifulSoup
import requests

# Load pre-trained models
filename = 'nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('tranform.pkl', 'rb'))

def create_similarity():
    data = pd.read_csv('main_data.csv')
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    similarity = cosine_similarity(count_matrix)
    return data, similarity

data, similarity = create_similarity()

def get_suggestions():
    return list(data['movie_title'].str.capitalize())

def rcmd(movie):
    movie = movie.lower()
    if movie not in data['movie_title'].unique():
        return 'Sorry! The movie you requested is not in our database.'
    else:
        idx = data.loc[data['movie_title'] == movie].index[0]
        scores = list(enumerate(similarity[idx]))
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
        scores = scores[1:11]
        recommended = [data['movie_title'][i[0]] for i in scores]
        return recommended

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    suggestions = get_suggestions()
    trending_movies = [
        {"title": "Gladiator II", "poster": "/static/glad.jpg", "url": "https://movieshdwatch.to/movie/watch-gladiator-ii-online-116161"},
        {"title": "Dune Prophecy", "poster": "/static/duns.jpg", "url": "https://movieshdwatch.to/tv/watch-dune-prophecy-online-117067"},
        {"title": "Venom: The Last Dance", "poster": "/static/vens.jpg", "url": "https://movieshdwatch.to/movie/watch-venom-the-last-dance-online-115885"},
        {"title": "Saturday Night 2024", "poster": "/static/sat.webp", "url": "https://movieshdwatch.to/movie/watch-saturday-night-online-114820"},
        {"title": "Joker: Folie à Deux", "poster": "/static/jok.jpg", "url": "https://movieshdwatch.to/movie/watch-joker-folie-a-deux-online-114916"},
        {"title": "Substance 2024", "poster": "/static/substance.jpg", "url": "https://movieshdwatch.to/movie/watch-the-substance-online-114055"}

    ]
    return render_template('home.html', suggestions=suggestions, trending_movies=trending_movies)

@app.route('/similarity', methods=['POST'])
def similarity_route():
    movie_name = request.form.get('name', '').strip()
    if not movie_name:
        return "Please provide a movie name.", 400

    recommendations = rcmd(movie_name)
    if isinstance(recommendations, str):
        return recommendations
    else:
        return jsonify(recommendations)

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        title = request.form.get('title', 'Unknown Title')
        cast_ids = request.form.get('cast_ids', '[]')
        cast_names = request.form.get('cast_names', '[]')
        cast_chars = request.form.get('cast_chars', '[]')
        cast_bdays = request.form.get('cast_bdays', '[]')
        cast_bios = request.form.get('cast_bios', '[]')
        cast_places = request.form.get('cast_places', '[]')
        cast_profiles = request.form.get('cast_profiles', '[]')
        imdb_id = request.form.get('imdb_id', '')
        poster = request.form.get('poster', '')
        genres = request.form.get('genres', '')
        overview = request.form.get('overview', '')
        vote_average = request.form.get('rating', '0')
        vote_count = request.form.get('vote_count', '0')
        release_date = request.form.get('release_date', '')
        runtime = request.form.get('runtime', '0')
        status = request.form.get('status', '')
        rec_movies = request.form.get('rec_movies', '[]')
        rec_posters = request.form.get('rec_posters', '[]')

        # Convert strings to lists
        rec_movies = eval(rec_movies)
        rec_posters = eval(rec_posters)
        cast_names = eval(cast_names)
        cast_chars = eval(cast_chars)
        cast_profiles = eval(cast_profiles)
        cast_bdays = eval(cast_bdays)
        cast_bios = eval(cast_bios)
        cast_places = eval(cast_places)
        cast_ids = eval(cast_ids)

        # Combine data into dictionaries for rendering
        movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}
        casts = {cast_names[i]: [cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}
        cast_details = {cast_names[i]: [cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}

        # Scrape IMDB reviews
        url = f'https://www.imdb.com/title/{imdb_id}/reviews/?ref_=tt_ov_rt'
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}
        response = requests.get(url, headers=headers)
        reviews_list, reviews_status = [], []

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'lxml')
            reviews = soup.find_all("div", {"class": "ipc-html-content-inner-div"})

            for review in reviews:
                if review.string:
                    reviews_list.append(review.string)
                    review_vector = vectorizer.transform([review.string])
                    pred = clf.predict(review_vector)
                    reviews_status.append('Good' if pred else 'Bad')

        movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}

        return render_template('recommend.html', title=title, poster=poster, overview=overview,
                               vote_average=vote_average, vote_count=vote_count, release_date=release_date,
                               runtime=runtime, status=status, genres=genres, movie_cards=movie_cards,
                               reviews=movie_reviews, casts=casts, cast_details=cast_details)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)

# load the nlp model and tfidf vectorizer from disk
filename = 'nlp_model.pkl'
clf = pickle.load(open(filename, 'rb'))
vectorizer = pickle.load(open('tranform.pkl','rb'))

def create_similarity():
    data = pd.read_csv('main_data.csv')
    # creating a count matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(data['comb'])
    # creating a similarity score matrix
    similarity = cosine_similarity(count_matrix)
    return data,similarity

def rcmd(m):
    m = m.lower()
    try:
        data.head()
        similarity.shape
    except:
        data, similarity = create_similarity()
    if m not in data['movie_title'].unique():
        return('Sorry! The movie you requested is not in our database. Please check the spelling or try with some other movies')
    else:
        i = data.loc[data['movie_title']==m].index[0]
        lst = list(enumerate(similarity[i]))
        lst = sorted(lst, key = lambda x:x[1] ,reverse=True)
        lst = lst[1:11] # excluding first item since it is the requested movie itself
        l = []
        for i in range(len(lst)):
            a = lst[i][0]
            l.append(data['movie_title'][a])
        return l

# converting list of string to list (eg. "["abc","def"]" to ["abc","def"])
def convert_to_list(my_list):
    my_list = my_list.split('","')
    my_list[0] = my_list[0].replace('["','')
    my_list[-1] = my_list[-1].replace('"]','')
    return my_list

def get_suggestions():
    data = pd.read_csv('main_data.csv')
    return list(data['movie_title'].str.capitalize())

app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():
    suggestions = get_suggestions()
    return render_template('home.html',suggestions=suggestions)

@app.route("/similarity",methods=["POST"])
def similarity():
    movie = request.form['name']
    rc = rcmd(movie)
    if type(rc)==type('string'):
        return rc
    else:
        m_str="---".join(rc)
        return m_str

@app.route("/recommend",methods=["POST"])
def recommend():
    # getting data from AJAX request
    title = request.form['title']
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
    cast_ids[0] = cast_ids[0].replace("[","")
    cast_ids[-1] = cast_ids[-1].replace("]","")

    # rendering the string to python string
    for i in range(len(cast_bios)):
        cast_bios[i] = cast_bios[i].replace(r'\n', '\n').replace(r'\"','\"')

    # combining multiple lists as a dictionary which can be passed to the html file so that it can be processed easily and the order of information will be preserved
    movie_cards = {rec_posters[i]: rec_movies[i] for i in range(len(rec_posters))}

    casts = {cast_names[i]:[cast_ids[i], cast_chars[i], cast_profiles[i]] for i in range(len(cast_profiles))}

    cast_details = {cast_names[i]:[cast_ids[i], cast_profiles[i], cast_bdays[i], cast_places[i], cast_bios[i]] for i in range(len(cast_places))}
    print(f"calling imdb api: {'https://www.imdb.com/title/{}/reviews/?ref_=tt_ov_rt'.format(imdb_id)}")
    # web scraping to get user reviews from IMDB site
    url = f'https://www.imdb.com/title/{imdb_id}/reviews/?ref_=tt_ov_rt'
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36'}

    response = requests.get(url, headers=headers)
    print(response.status_code)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml')
        soup_result = soup.find_all("div", {"class": "ipc-html-content-inner-div"})
        print(soup_result)

        reviews_list = [] # list of reviews
        reviews_status = [] # list of comments (good or bad)
        for reviews in soup_result:
            if reviews.string:
                reviews_list.append(reviews.string)
                # passing the review to our model
                movie_review_list = np.array([reviews.string])
                movie_vector = vectorizer.transform(movie_review_list)
                pred = clf.predict(movie_vector)
                reviews_status.append('Good' if pred else 'Bad')

        # combining reviews and comments into a dictionary
        movie_reviews = {reviews_list[i]: reviews_status[i] for i in range(len(reviews_list))}

        # passing all the data to the html file
        return render_template('recommend.html',title=title,poster=poster,overview=overview,vote_average=vote_average,
            vote_count=vote_count,release_date=release_date,runtime=runtime,status=status,genres=genres,
            movie_cards=movie_cards,reviews=movie_reviews,casts=casts,cast_details=cast_details)
    else:
        print("Failed to retrieve reviews")

if __name__ == '__main__':
    app.run(debug=True)
