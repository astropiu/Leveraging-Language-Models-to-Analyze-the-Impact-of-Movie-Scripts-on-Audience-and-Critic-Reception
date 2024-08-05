


from unsloth import FastLanguageModel
import torch
max_seq_length = 2048 # Choose any! We auto support RoPE Scaling internally!
dtype = None # None for auto detection. Float16 for Tesla T4, V100, Bfloat16 for Ampere+
load_in_4bit = True # Use 4bit quantization to reduce memory usage. Can be False.

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "unsloth/llama-3-8b-bnb-4bit",
    max_seq_length = max_seq_length,
    dtype = dtype,
    load_in_4bit = load_in_4bit,
    # token = "hf_...", # use one if using gated models like meta-llama/Llama-2-7b-hf
)

model = FastLanguageModel.get_peft_model(
     model,
     r = 16, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
     target_modules = ["q_proj", "k_proj", "v_proj", "o_proj",
                       "gate_proj", "up_proj", "down_proj",],
     lora_alpha = 16,
     lora_dropout = 0, # Supports any, but = 0 is optimized
     bias = "none",    # Supports any, but = "none" is optimized
     # [NEW] "unsloth" uses 30% less VRAM, fits 2x larger batch sizes!
     use_gradient_checkpointing = "unsloth", # True or "unsloth" for very long context
     random_state = 3407,
     use_rslora = False,  # We support rank stabilized LoRA
     loftq_config = None, # And LoftQ
 )

from datasets import load_dataset
import json
import pandas as pd
import ast
df = pd.read_csv("sample.csv")
df['reviews'] = df['reviews'].apply(ast.literal_eval)

res_dict = []
for row_dict in df.to_dict(orient="records"):
    for review in row_dict["reviews"]:
        res_dict.append(
    {
        "instruction": "Generate review from subtitles",
        "input": row_dict["subtilte"],
        "output": review
    }
        )

with open("dataset.json", "w") as f:
   json.dump(res_dict, f)

dataset = load_dataset("json", data_files="dataset.json", split = "train")


alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

EOS_TOKEN = tokenizer.eos_token # Must add EOS_TOKEN
def formatting_prompts_func(examples):
    instructions = examples["instruction"]
    inputs       = examples["input"]
    outputs      = examples["output"]
    texts = []
    for instruction, input, output in zip(instructions, inputs, outputs):
        # Must add EOS_TOKEN, otherwise your generation will go on forever!
        text = alpaca_prompt.format(instruction, input, output) + EOS_TOKEN
        texts.append(text)
    return { "text" : texts, }
pass

dataset = dataset.map(formatting_prompts_func, batched = True,)


from trl import SFTTrainer
from transformers import TrainingArguments

trainer = SFTTrainer(
    model = model,
    tokenizer = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = max_seq_length,
    dataset_num_proc = 2,
    packing = False, # Can make training 5x faster for short sequences.
    args = TrainingArguments(
        per_device_train_batch_size = 4,
        gradient_accumulation_steps = 4,
        warmup_steps = 5,
        num_train_epochs=10,
        learning_rate = 2e-4,
        fp16 = not torch.cuda.is_bf16_supported(),
        bf16 = torch.cuda.is_bf16_supported(),
        logging_steps = 1,
        optim = "adamw_8bit",
        save_strategy="steps",
        save_steps=500,
        weight_decay = 0.01,
        lr_scheduler_type = "linear",
        seed = 3407,
        output_dir = "outputs",
    ),
)

trainer_stats = trainer.train()