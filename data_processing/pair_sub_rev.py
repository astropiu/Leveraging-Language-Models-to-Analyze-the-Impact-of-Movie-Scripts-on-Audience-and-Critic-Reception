import pandas as pd
import os
from tqdm import tqdm

subs_dir = '/Users/mohitshah/Downloads/subs_corrected'
rev_dir = 'cleaned_review_by_id'
res_csv = 'dataset.csv'
revs = os.listdir(rev_dir)
res = []
failed = []
for sub_id in tqdm(os.listdir(subs_dir)):
    try:
        rev_csv = sub_id + '.csv'
        if not rev_csv in revs:
            continue
        rev_df = pd.read_csv(os.path.join(rev_dir, rev_csv))
        sub_df = pd.read_csv(os.path.join(subs_dir,sub_id,'summary.csv'))
        sub_data = ''.join(sub_df['summary'])
        rev_data = list(rev_df['Review_body'])
        movie = list(rev_df['Movie_name'])[0]
        id = list(rev_df['movie_id'])[0]
        res.append([sub_data, rev_data, movie, id])
    except:
        failed.append(sub_id)

res_df = pd.DataFrame(res, columns = ['subtilte','reviews', 'movie', 'id'])
res_df.to_csv(res_csv)
print(failed)