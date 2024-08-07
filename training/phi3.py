import sys
import logging

import datasets
from datasets import load_dataset
from peft import LoraConfig
import torch
import transformers
from trl import SFTTrainer
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig



logger = logging.getLogger(__name__)


###################
# Hyper-parameters
###################
training_config = {
    "fp16": True,
    "do_eval": False,
    "learning_rate": 5.0e-06,
    "log_level": "info",
    "logging_steps": 20,
    "logging_strategy": "steps",
    "lr_scheduler_type": "cosine",
    "num_train_epochs": 1,
    "max_steps": -1,
    "output_dir": "./checkpoint_dir",
    "overwrite_output_dir": True,
    "per_device_eval_batch_size": 1,
    "per_device_train_batch_size": 1,
    "remove_unused_columns": True,
    "save_steps": 100,
    "save_total_limit": 1,
    "seed": 0,
    "gradient_checkpointing": True,
    "gradient_checkpointing_kwargs":{"use_reentrant": False},
    "gradient_accumulation_steps": 1,
    "warmup_ratio": 0.2,
    }

peft_config = {
    "r": 16,
    "lora_alpha": 32,
    "lora_dropout": 0.05,
    "bias": "none",
    "task_type": "CAUSAL_LM",
    "target_modules": "all-linear",
    "modules_to_save": None,
}
train_conf = TrainingArguments(**training_config)
peft_conf = LoraConfig(**peft_config)


###############
# Setup logging
###############
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log_level = train_conf.get_process_log_level()
logger.setLevel(log_level)
datasets.utils.logging.set_verbosity(log_level)
transformers.utils.logging.set_verbosity(log_level)
transformers.utils.logging.enable_default_handler()
transformers.utils.logging.enable_explicit_format()

# Log on each process a small summary
logger.warning(
    f"Process rank: {train_conf.local_rank}, device: {train_conf.device}, n_gpu: {train_conf.n_gpu}"
    + f" distributed training: {bool(train_conf.local_rank != -1)}, 16-bits training: {train_conf.fp16}"
)
logger.info(f"Training/evaluation parameters {train_conf}")
logger.info(f"PEFT parameters {peft_conf}")




################
# Model Loading
################
# checkpoint_path = "microsoft/Phi-3-mini-4k-instruct"
checkpoint_path = "microsoft/Phi-3-mini-128k-instruct"
model_kwargs = dict(
    use_cache=False,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,
    device_map=None
)
model = AutoModelForCausalLM.from_pretrained(checkpoint_path, **model_kwargs)
tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
tokenizer.model_max_length = 2048
tokenizer.pad_token = tokenizer.unk_token  # use unk rather than eos token to prevent endless generation
tokenizer.pad_token_id = tokenizer.convert_tokens_to_ids(tokenizer.pad_token)
tokenizer.padding_side = 'right'


import pandas as pd
import ast
import json
import datasets
from datasets import load_dataset
df = pd.read_csv('sample.csv')
df['reviews'] = df['reviews'].apply(ast.literal_eval)

res_dict = []
for row_dict in df.to_dict(orient="records"):
    row = []
    for review in row_dict["reviews"]:
        row.append(
    {
        "content": row_dict["subtilte"],
        "role": "user"
    }
        )
        row.append(
    {
        "content": review,
        "role": "assistant"
    }
        )
        res_dict.append({"messages":row})
with open("dataset.json", "w") as f:
   json.dump(res_dict, f)

dataset = load_dataset("json", data_files="dataset.json", split = "train")




##################
# Data Processing
##################
def apply_chat_template(
    example,
    tokenizer,
):
    messages = example["messages"]
    example["text"] = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False)
    return example

#raw_dataset = load_dataset("HuggingFaceH4/ultrachat_200k")
#train_dataset = raw_dataset["train_sft"]
#test_dataset = raw_dataset["test_sft"]
column_names = list(dataset.features)

processed_train_dataset = dataset.map(
    apply_chat_template,
    fn_kwargs={"tokenizer": tokenizer},
    num_proc=1,
    remove_columns=column_names,
    desc="Applying chat template to data",
)



###########
# Training
###########
trainer = SFTTrainer(
    model=model,
    args=train_conf,
    peft_config=peft_conf,
    train_dataset=processed_train_dataset,
    #eval_dataset=processed_test_dataset,
    max_seq_length=1024*16,
    dataset_text_field="text",
    tokenizer=tokenizer,
    packing=True
)
train_result = trainer.train()
metrics = train_result.metrics
trainer.log_metrics("train", metrics)
trainer.save_metrics("train", metrics)
trainer.save_state()

"""
#############
# Evaluation
#############
tokenizer.padding_side = 'left'
metrics = trainer.evaluate()
metrics["eval_samples"] = len(processed_test_dataset)
trainer.log_metrics("eval", metrics)
trainer.save_metrics("eval", metrics)"""


# ############
# # Save model
# ############
trainer.save_model(train_conf.output_dir)

