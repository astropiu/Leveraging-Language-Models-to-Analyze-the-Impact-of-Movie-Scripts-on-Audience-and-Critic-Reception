import torch
from transformers import BartForConditionalGeneration, BartTokenizer
import textwrap
import pandas as pd
from torch.utils.data import DataLoader, Dataset
from multiprocessing import Pool
import os

# Load the pre-trained BART model and tokenizer
model_name = "facebook/bart-large-cnn"
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

# Move model to GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def summarize_text(text, max_length=130, min_length=30):
    inputs = tokenizer.batch_encode_plus([text], max_length=1024, return_tensors='pt', truncation=True).to(device)
    summary_ids = model.generate(inputs['input_ids'], max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

def split_text(text, max_chunk_size=1024):
    # Split text into manageable chunks
    return textwrap.wrap(text, max_chunk_size, break_long_words=False, replace_whitespace=False)

# Custom Dataset class for DataLoader
class SubtitlesDataset(Dataset):
    def __init__(self, scenes):
        self.scenes = scenes

    def __len__(self):
        return len(self.scenes)

    def __getitem__(self, idx):
        return self.scenes[idx]

dir = 'subs_inf'

sub_ids =  os.listdir(dir)
for sub_id in sub_ids:
    sub_path = os.path.join(dir,sub_id)
    sub_scene = os.path.join(sub_path,'scenes.csv')
    summary_path = os.path.join(sub_path,'summary.csv')
    if os.path.exists(summary_path):
        continue
    df = pd.read_csv(sub_scene)
    scenes = df['scene'].tolist()

    # Create DataLoader
    dataset = SubtitlesDataset(scenes)
    dataloader = DataLoader(dataset, batch_size=1, num_workers=16, shuffle=False)

    # Process subtitles
    final_summary = []
    model.eval()  # Set model to evaluation mode

    print('loading data')
    with torch.no_grad():  # Disable gradient calculation
        for scene in dataloader:
            scene = scene[0]  # Extract the text from the DataLoader
            chunks = split_text(scene)
            summaries = [summarize_text(chunk) for chunk in chunks if chunk]
            summary = " ".join(summaries)
            final_summary.append(summary)

    # Save summaries to CSV
    summary_df = pd.DataFrame(final_summary, columns=["summary"])
    summary_df.to_csv(summary_path, index=False)

    #print("Summarization complete. Output saved to summary.csv.")
