import pandas as pd
from imdb import IMDb
from tqdm import tqdm
df = pd.read_csv('test_movies.csv')

imdb_ids = df['imdb_id']


def get_movie_rating(imdb_id):
    ia = IMDb()
    movie = ia.get_movie(imdb_id[2:])  # Remove the 'tt' prefix from the IMDb ID
    if 'rating' in movie:
        return movie['rating']
    else:
        return "Rating not found"

# Replace with the IMDb ID of the movie you want to query
imdb_id = "tt0111161"  # Example IMDb ID for "The Shawshank Redemption"

rating = get_movie_rating(imdb_id)
print(f"The IMDb rating for movie ID {imdb_id} is {rating}")
ratings = []
for id in tqdm(imdb_ids):
    rating = get_movie_rating(id)
    ratings.append(rating)

df['rating'] = ratings
df.to_csv('test_movies_r.csv')

