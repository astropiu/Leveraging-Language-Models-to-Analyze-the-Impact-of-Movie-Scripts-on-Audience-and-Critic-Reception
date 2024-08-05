import requests
from bs4 import BeautifulSoup
import os
from fake_useragent import UserAgent
import pandas as pd
import os
from tqdm import tqdm
ua = UserAgent()
userAgent = ua.random
headers = {'User-Agent': userAgent, 'accept-language': 'en'}
dir = 'subtitles_test'
os.makedirs(dir,exist_ok=True)
def get_movie_page(movie_id):
    search_url = f'https://yifysubtitles.ch/movie-imdb/{movie_id}'
    print(search_url)
    response = requests.get(search_url)
    #print(response.text)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Find the first movie result link
    links = soup.find_all('a',href=True)
    #print(links.text)
    for link in links:
            download_link = link['href']
            #print(download_link)
            if 'english' in download_link:
                print(download_link)
                return f'https://yifysubtitles.ch{download_link}'


def download_subtitle(subtitle_url, movie_id):
    print('url is ',subtitle_url)
    response = requests.get(subtitle_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    download_link = soup.find('a', class_='btn-icon download-subtitle')['href']
    download_link = f'https://yifysubtitles.ch{download_link}'
    download_response = requests.get(download_link)
    file_name = f"{os.path.join(dir,movie_id)}.zip"
    print('downloading')
    with open(file_name, 'wb') as file:
        file.write(download_response.content)
    print(f"Downloaded subtitle: {file_name}")

def download_subtitles_for_movies(movie_id):
        try:
            movie_url = get_movie_page(movie_id)
            print(movie_url)
            #subtitle_url = get_subtitle_page(movie_url)
            if movie_url:
                download_subtitle(movie_url, movie_id)
            else:
                print(f"No English subtitles found for {movie_id}")
        except Exception as e:
            print(f"Error occurred for {movie_id}: {e}")

# List of movies to download subtitles for
df = pd.read_csv('test_movies.csv')

movie_ids = list(df['imdb_id'])
failed = []
for id in tqdm(movie_ids):
    file = os.path.join(dir, f'{id}.zip')
    if os.path.exists(file):
         continue
    try:
        download_subtitles_for_movies(id)
    except:
        failed.append(id)
failed = pd.DataFrame(failed)
failed.to_csv('failed.csv')
