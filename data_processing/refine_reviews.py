import pandas as pd
import os
from multiprocessing import Pool
src = 'review_test_by_id'
dest = 'cleaned_review_test_by_id'
os.makedirs(dest,exist_ok=True)
def refine(file):
        src_file = os.path.join(src,file)
        dest_file = os.path.join(dest,file)
        df = pd.read_csv(src_file)

        def trim_end(review):
            lines = review.split('\n')
            if 'Permalink' in lines[-1]:
                review = '\n'.join(lines[:-7])
            review = review.rstrip()
            return review
        try: 
            df['Review_body'] = df.apply(lambda x: trim_end(x['Review_body']),axis=1)
        except :
             #print(file)
             return False

        df.to_csv(dest_file)
        return True
    
if __name__ == '__main__':
    files = os.listdir(src)
    with Pool(8) as pool:
        res = pool.map(refine,files)
    failed = [file for file,keep in zip(files,res) if not keep]
    print(failed)
    failed = pd.DataFrame(failed)
    failed.to_csv('review_failed.csv')