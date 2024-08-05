import os
import re
from multiprocessing import Pool
import pandas as pd

os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'

def preprocess_text(text):
    """
    Preprocesses the input text by removing unwanted symbols and fixing spacing issues.

    Parameters:
    text (str): The text to be preprocessed.

    Returns:
    str: The preprocessed text.
    """
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
    text = re.sub(r'(?<=[a-zA-Z])(?=[0-9])', ' ', text)
    text = re.sub(r'(?<=[0-9])(?=[a-zA-Z])', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

dir = 'subtitles_test'
new_dir = 'subs_corrected'
os.makedirs(new_dir,exist_ok=True)

sub_ids =  os.listdir(dir)

def process_summaries(sub_id):
    try:
        sub_path = os.path.join(dir,sub_id)
        summary_path = os.path.join(sub_path,'summary.csv')
        new_path = os.path.join(new_dir, sub_id)
        os.makedirs(new_path, exist_ok=True)
        new_summary_path = os.path.join(new_path,'summary.csv')
        suumary_df = pd.read_csv(summary_path)
        suumary_df['summary'] = suumary_df['summary'].apply(preprocess_text)
        suumary_df.to_csv(new_summary_path, index=False)
        return True
    except:
        return False

if __name__ == '__main__':
    with Pool(8) as pool:
        res = pool.map(process_summaries,sub_ids)
    failed = [file for file,suc in zip(sub_ids,res) if not suc]
    print(failed)
