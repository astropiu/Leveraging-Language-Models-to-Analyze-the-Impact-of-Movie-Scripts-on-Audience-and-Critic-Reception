from unsloth import FastLanguageModel
import torch
import os
import pandas as pd
max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True # Use 4bit quantization to reduce memory usage. Can be False.

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "lora_model", # YOUR MODEL YOU USED FOR TRAINING
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
)
FastLanguageModel.for_inference(model) # Enable native 2x faster inference

alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

dir = 'subs_corrected'

for sub_id in os.listdir(dir):
    sub_path = os.path.join(dir,sub_id)
    summary_path = os.path.join(sub_path,'summary.csv')
    review_path = os.path.join(sub_path,'review.csv')
    if not os.path.exists(summary_path):
        continue
    summary_df = pd.read_csv(summary_path)
    text = ''.join(summary_df['summary'])
    inputs = tokenizer(
    [
    alpaca_prompt.format(
            "Generate review from subtitles", # instruction
            text, # input
            "", # output - leave this blank for generation!
        )
    ], return_tensors = "pt").to("cuda")

    outputs = model.generate(**inputs, max_new_tokens = 1024, use_cache = True)
    out = tokenizer.batch_decode(outputs)
    review = list(out[0][out[0].find('### Response:')+14:out[0].find('<|end_of_text|>') ])
    df = pd.DataFrame(review,columns=['review'])
    df.to_csv(review_path)

