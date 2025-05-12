"""
Compatibility module for MoodFlix application.
Provides backward compatibility with the original MoodFlix code.
"""
import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.config import settings

def create_similarity():
    """
    Create similarity matrix for movie recommendations.
    This function is designed to be compatible with the original MoodFlix code.
    
    Returns:
        Tuple of (DataFrame, similarity_matrix)
    """
    try:
        # Get the CSV path from settings
        csv_path = settings.MOVIE_DATA_PATH
        abs_path = os.path.abspath(csv_path)
        print(f"Attempting to load for similarity: {abs_path}")
        
        # Check if file exists
        if not os.path.exists(csv_path):
            print(f"ERROR: File {csv_path} does not exist!")
            # Fall back to sample data
            return _create_sample_data()
            
        # Load the CSV file
        data = pd.read_csv(csv_path)
        
        # Check if 'comb' column exists, if not create it
        if 'comb' not in data.columns:
            # Check if required columns exist
            if 'movie_title' in data.columns:
                # Create a combined feature column
                data['comb'] = data['movie_title']
                
                # Add genres if available
                if 'genres' in data.columns:
                    data['comb'] = data['comb'] + ' ' + data['genres'].fillna('')
                
                # Add plot if available
                if 'plot' in data.columns:
                    data['comb'] = data['comb'] + ' ' + data['plot'].fillna('')
            else:
                print("Error: Required column 'movie_title' not found in CSV")
                return _create_sample_data()
        
        # Create count matrix and similarity matrix
        cv = CountVectorizer()
        count_matrix = cv.fit_transform(data['comb'])
        similarity = cosine_similarity(count_matrix)
        
        return data, similarity
    except Exception as e:
        print(f"Error in create_similarity: {e}")
        # Fall back to sample data
        return _create_sample_data()

def _create_sample_data():
    """
    Create a sample dataset for fallback.
    
    Returns:
        Tuple of (DataFrame, similarity_matrix)
    """
    print("Using sample data as fallback")
    
    # Create a minimal sample dataframe
    sample_data = pd.DataFrame({
        'movie_title': [
            'the shawshank redemption',
            'the godfather',
            'the dark knight',
            'pulp fiction',
            'fight club',
            'forrest gump',
            'inception',
            'the matrix',
            'star wars',
            'titanic',
            'the godfather part ii',
            'jurassic park'
        ],
        'genres': [
            'Drama',
            'Crime, Drama',
            'Action, Crime, Drama',
            'Crime, Drama',
            'Drama',
            'Drama, Romance',
            'Action, Adventure, Sci-Fi',
            'Action, Sci-Fi',
            'Action, Adventure, Fantasy',
            'Drama, Romance',
            'Crime, Drama',
            'Adventure, Sci-Fi, Thriller'
        ],
        'plot': [
            'prison drama about hope and redemption',
            'crime drama about an italian mafia family',
            'superhero crime thriller with the joker',
            'crime stories that intertwine in los angeles',
            'man starts an underground fight club',
            'man with low iq witnesses historical events',
            'thieves enter dreams to steal information',
            'hacker discovers reality is a computer simulation',
            'space fantasy adventure with jedi knights',
            'romantic drama about a sinking ship',
            'continuation of the corleone family saga',
            'adventure movie about dinosaurs in a theme park'
        ]
    })
    
    # Create a combined feature column
    sample_data['comb'] = sample_data['movie_title'] + ' ' + sample_data['genres'] + ' ' + sample_data['plot']
    
    # Create count matrix and similarity matrix
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(sample_data['comb'])
    similarity = cosine_similarity(count_matrix)
    
    return sample_data, similarity

def get_recommendations(movie_title, data=None, similarity=None):
    """
    Get movie recommendations based on similarity.
    This function is designed to be compatible with the original MoodFlix code.
    
    Args:
        movie_title: Title of the movie to find recommendations for
        data: DataFrame containing movie data
        similarity: Similarity matrix
        
    Returns:
        List of recommended movie titles
    """
    movie_title = movie_title.lower()
    
    # Create similarity if not provided
    if data is None or similarity is None:
        data, similarity = create_similarity()
    
    # Check if movie exists in database
    print(f"Checking if movie '{movie_title}' exists in database")
    if movie_title not in data['movie_title'].values:
        print(f"Movie '{movie_title}' not found in database")
        return []
    
    # Get recommendations
    i = data.loc[data['movie_title'] == movie_title].index[0]
    lst = list(enumerate(similarity[i]))
    lst = sorted(lst, key=lambda x: x[1], reverse=True)
    lst = lst[1:11]  # excluding first item since it is the requested movie itself
    
    # Extract movie titles
    recommendations = []
    for i in range(len(lst)):
        a = lst[i][0]
        recommendations.append(data['movie_title'][a])
    
    return recommendations
