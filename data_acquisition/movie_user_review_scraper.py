# ## IMDb User Reviews Scraper

import pandas as pd 
import selenium
from selenium import webdriver
import requests #needed to load the page for BS4
from bs4 import BeautifulSoup
from tqdm import tqdm
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import re
import numpy as np
import time
import os
from multiprocessing import Pool
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

# ### Retrieve URLs using IMDbPY package


from imdb import IMDb

def get_imdb_url(movie_id):
    print(movie_id)
    ia = IMDb()
    failed = False
    #for movie_id in tqdm(movie_ids):
    try:
            search_id = movie_id[2:]
            movie_data = ia.get_movie(search_id)
            #search_results = ia.search_movie(movie)
            if not movie_data:
                print(f"Movie '{movie_id}' not found on IMDb.")
                failed = True
            movie_url = ia.get_imdbURL(movie_data)
            movie_title = movie_data.get('title')
            
    except:
            failed = True

    #Build data dictionary for dataframe
    
    if failed:
        movie_url = movie_title = 'NA'
    return [movie_id, movie_url, movie_title]

#PATH = r"/opt/homebrew/bin/chromedriver"  # path to the webdriver file
PATH = r"/Users/mohitshah/Downloads/chromedriver-mac-arm64/chromedriver"
service = Service(PATH)
folder_name = 'reviews_test'
os.makedirs(folder_name,exist_ok=True)
#### Scraping Movie Reviews
def get_review(row):
        try:
            movie = row['movie_titles'] #grab the movie name from the top50 list    

            url = row['review_link']
            global service, folder_name

            if os.path.exists(f'{folder_name}/{movie}.csv'):
                print('movie already done')
                return True

            options = webdriver.ChromeOptions()
            options.add_argument("--headless")  

            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)
            driver.implicitly_wait(2) # tell the webdriver to wait for 1 second for the page to load to prevent blocked by anti spam software


            # Set up action to click on 'load more' button
            # note that each page on imdb has 25 reviews
            page = 1 #Set initial variable for while loop
            #We want at least 1000 review, so get 50 at a safe number
            while page<2:  
                try:
                    #find the load more button on the webpage
                    load_more = driver.find_element(By.ID,'load-more-trigger')
                    #click on that button
                    load_more.click()
                    page+=1 #move on to next loadmore button
                except:
                    #If couldnt find any button to click, stop
                    print("No button to click! Page ", page)
                    break
            # After fully expand the page, we will grab data from whole website
            review = driver.find_elements(By.CLASS_NAME,'review-container')
            #Set list for each element:
            title = []
            content = []
            rating = []
            date = []
            user_name = []
            
            #run for loop to get
            if len(review) > 0:
                for n in range(0,100):
                    try:
                        #Some reviewers only give review text or rating without the other, 
                        #so we use try/except here to make sure each block of content must has all the element before 
                        #append them to the list

                        #Check if each review has all the elements
                        ftitle = review[n].find_element(By.CLASS_NAME,'title').text
                        #For the review content, some of them are hidden as spoiler, 
                        #so we use the attribute 'textContent' here after extracting the 'content' tag
                        fcontent = review[n].find_element(By.CLASS_NAME,'content').get_attribute("textContent").strip()
                        frating = review[n].find_element(By.CLASS_NAME,'rating-other-user-rating').text
                        fdate = review[n].find_element(By.CLASS_NAME,'review-date').text
                        fname = review[n].find_element(By.CLASS_NAME,'display-name-link').text


                        #Then add them to the respective list
                        title.append(ftitle)
                        content.append(fcontent)
                        rating.append(frating)
                        date.append(fdate)
                        user_name.append(fname)
                    except:
                        continue
            #Build data dictionary for dataframe
            data = {'User_name': user_name, 
                'Review title': title, 
                'Review Rating': rating,
                'Review date' : date,
                'Review_body' : content
            }
            #Build dataframe for each movie to export
            review = pd.DataFrame(data = data)
            movie = row['movie_titles'] #grab the movie name from the top50 list    
            review['Movie_name'] = movie #create new column with the same movie name column    
            mid = row['movie_id']
            review['movie_id'] = mid
            path = f'{folder_name}/{movie}.csv'
            print(path)
            review.to_csv(path) #store them into individual file for each movies, so we can combine or check them later
            driver.quit()
            return True
        except Exception as e:
             print(e)
             return False

def get_review_chunk(url_chunk):
     return url_chunk.apply(get_review, axis = 1)
def get_reviews(url_df):
    '''
    Get the review from input as url for IMDB movies list.
    The function takes 2 input the url of the movies and the name of the folder to store the data
    For each folder, the function will grab the review for each movies and store into respective file.
    '''

    #Set initial empty list for each element:
    title = []
    link = url_df['imdb_url']
    year = []      

    # After that, we can use BeautifulSoup to extract the user reviews link 
    #Set an empty list to store user review link
    user_review_links = []
    for i in range(len(url_df)):
        #print(url_df['imdb_url'][i])
        review_link = url_df['imdb_url'][i]+'reviews/?ref_=tt_ql_2'
            
        #Append the newly grabed link into its list
        user_review_links.append(review_link)
    url_df['review_link'] = user_review_links
    

    # Step 2, we will grab the data from each user review page
    # Use Selenium to go to each user review page
    url_df_chunks = np.array_split(url_df,8)

    with Pool(8) as pool:
        reviews = pool.map(get_review_chunk,url_df_chunks)
     
        
    print("Done processing")


if __name__ == '__main__':
    list_csv = 'test_movies.csv'
    rev_dir = 'reviews_test'
    movie_url = 'movies_url_test.csv'
    url_avail = True
    df = pd.read_csv(list_csv)

    movie_ids = list(df['imdb_id'])
    #movies['year'] = movies['movie_title'].str.extract('.*\((.*)\).*', expand=False)
    #movies['stripped_title'] = movies['movie_title'].str.replace(r'\s*\(\d+\)$', '')

    #Retrieve movie IMDb URL
    if not url_avail:
        with Pool(4) as pool:
            data = pool.map(get_imdb_url, movie_ids)


        print("!!!Done retrieving links!!!")
        movies_data = pd.DataFrame(data, columns = ['movie_id','imdb_url','movie_titles'])
    
        # Save URLs in a CSV file
        movies_data.to_csv(movie_url)
    #Scrape movie reviews

    movies_imdb = movies = pd.read_csv(movie_url)
    print(movies_imdb.shape)
    movies_imdb = movies_imdb[movies_imdb['imdb_url'].apply(lambda x : isinstance(x,str))]
    
    movies_imdb = movies_imdb.drop(movies_imdb.columns[movies_imdb.columns.str.contains('Unnamed', case=False)], axis=1)
    movies_imdb = movies_imdb.reset_index(drop=True)
    print(movies_imdb.shape)

    get_reviews(movies_imdb)

