from transformers import BertTokenizer, BertForMaskedLM, BertModel
from bert_score import BERTScorer
import pandas as pd
import os
import numpy as np
from tqdm import tqdm

rev_dir = '/home/ul/ul_student/ul_wka55/llama3/cleaned_review_test_by_id_done'
gen_dir = '/home/ul/ul_student/ul_wka55/llama3/subs_corrected_3_done'

scorer = BERTScorer(model_type='bert-base-uncased')
movie_metrics = []

for mov in tqdm(os.listdir(gen_dir)):
    try:
        path = os.path.join(gen_dir,mov,'review.csv')
        gen_rev = ''.join(pd.read_csv(path))
        actual_rev_path = os.path.join(rev_dir,mov+'.csv')
        actual_revs = pd.read_csv(actual_rev_path)['Review_body']
        metrics = []
        for actual_rev in actual_revs:
            P, R, F1 = scorer.score([gen_rev], [actual_rev])
            metrics.append([P,R,F1])
            #print(f"BERTScore Precision: {P.mean():.4f}, Recall: {R.mean():.4f}, F1: {F1.mean():.4f}")
        metrics = np.array(metrics)
        avg = np.mean(metrics,axis=0)
        movie_metrics.append([mov,*avg])
    except:
        continue

movie_metrics = pd.DataFrame(movie_metrics,columns = ['movie', 'P', 'R', 'F1'])
movie_metrics.to_csv('pred_metrics.csv')

movie_data_df = pd.read_csv('test_movies_r.csv')


actual_movie_metrics = []
for mov in tqdm(os.listdir(gen_dir)):
    try:
        actual_rev_path = os.path.join(rev_dir,mov+'.csv')
        rev_df = pd.read_csv(actual_rev_path)
        actual_revs = list(rev_df['Review_body'])
        metrics = []
        review_ratings = list(rev_df['Review Rating'].apply(lambda x: float(x.split('/')[0])))
        movie_rating = movie_data_df.loc[movie_data_df['imdb_id'] == mov]['rating'].values[0]
        best_ind = np.argmin(abs(np.array(review_ratings) - movie_rating))

        rev1 = actual_revs[best_ind]
        for ind,actual_rev in enumerate(actual_revs):
            if ind == best_ind:
                continue
            P, R, F1 = scorer.score([rev1], [actual_rev])
            metrics.append([P,R,F1])
            #print(f"BERTScore Precision: {P.mean():.4f}, Recall: {R.mean():.4f}, F1: {F1.mean():.4f}")
        metrics = np.array(metrics)
        avg = np.mean(metrics,axis=0)
        actual_movie_metrics.append([mov,*avg]) 
    except Exception as e:
        print(e)
        continue

actual_movie_metrics = pd.DataFrame(actual_movie_metrics,columns = ['movie', 'P', 'R', 'F1'])
actual_movie_metrics.to_csv('actual_metrics.csv')





