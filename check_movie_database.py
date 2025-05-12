from voice_movie_recommender import VoiceMovieRecommender

# Initialize recommender
recommender = VoiceMovieRecommender()

# Print information about the database
print(f"Total movies in database: {len(recommender.movie_database)}")

# Check if movies have all required fields
missing_fields = {
    "title": 0,
    "year": 0,
    "genres": 0,
    "actors": 0,
    "directors": 0,
    "themes": 0,
    "plot": 0,
    "mood": 0
}

for movie in recommender.movie_database:
    for field in missing_fields.keys():
        if field not in movie or movie[field] is None or (isinstance(movie[field], list) and len(movie[field]) == 0):
            missing_fields[field] += 1

print("\nMissing fields count:")
for field, count in missing_fields.items():
    print(f"{field}: {count} movies missing this field ({count/len(recommender.movie_database)*100:.1f}%)")

# Print sample of movies with genres
print("\nSample movies with genres:")
genre_movies = [movie for movie in recommender.movie_database if movie.get("genres") and len(movie["genres"]) > 0]
for i, movie in enumerate(genre_movies[:5]):
    print(f"{i+1}. {movie['title']} ({movie.get('year', 'Unknown')}) - Genres: {movie['genres']}")

# Print sample of movies with actors
print("\nSample movies with actors:")
actor_movies = [movie for movie in recommender.movie_database if movie.get("actors") and len(movie["actors"]) > 0]
for i, movie in enumerate(actor_movies[:5]):
    print(f"{i+1}. {movie['title']} ({movie.get('year', 'Unknown')}) - Actors: {movie['actors']}")

# Print sample of movies with directors
print("\nSample movies with directors:")
director_movies = [movie for movie in recommender.movie_database if movie.get("directors") and len(movie["directors"]) > 0]
for i, movie in enumerate(director_movies[:5]):
    print(f"{i+1}. {movie['title']} ({movie.get('year', 'Unknown')}) - Directors: {movie['directors']}")

# Print sample of 90s sci-fi movies
print("\nSample 90s sci-fi movies:")
scifi_90s = [
    movie for movie in recommender.movie_database 
    if movie.get("genres") and "sci-fi" in movie["genres"] 
    and movie.get("year") and 1990 <= movie["year"] <= 1999
]
for i, movie in enumerate(scifi_90s[:5]):
    print(f"{i+1}. {movie['title']} ({movie['year']}) - Genres: {movie['genres']}") 