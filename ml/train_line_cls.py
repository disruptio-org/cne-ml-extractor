from __future__ import annotations
import os, pandas as pd
from datasets import load_dataset
from sklearn.model_selection import train_test_split
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

DATA = './data/line_cls/all_lines.csv'
OUT  = './models/line-cls-xlmr'

def main():
    os.makedirs(OUT, exist_ok=True)
    df = pd.read_csv(DATA)
    train_df, val_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['label'])
    train_df.to_csv('./data/line_cls/train.csv', index=False)
    val_df.to_csv('./data/line_cls/dev.csv', index=False)

    ds = load_dataset('csv', data_files={'train':'./data/line_cls/train.csv','validation':'./data/line_cls/dev.csv'})
    labels = sorted(list(set(df['label'])))
    label2id = {l:i for i,l in enumerate(labels)}
    id2label = {i:l for l,i in label2id.items()}

    tok = AutoTokenizer.from_pretrained('xlm-roberta-base')
    def tok_fn(ex): return tok(ex['text'], truncation=True)
    ds = ds.map(tok_fn, batched=True)
    ds = ds.map(lambda ex: {'labels': [label2id[l] for l in ex['label']]} if isinstance(ex['label'], list) else {'labels': label2id[ex['label']]})

    m = AutoModelForSequenceClassification.from_pretrained('xlm-roberta-base', num_labels=len(labels), id2label=id2label, label2id=label2id)
    args = TrainingArguments(output_dir=OUT, per_device_train_batch_size=16, per_device_eval_batch_size=16, learning_rate=3e-5,
                             num_train_epochs=5, evaluation_strategy='epoch', save_strategy='epoch', logging_steps=50)
    tr = Trainer(model=m, args=args, train_dataset=ds['train'], eval_dataset=ds['validation'], tokenizer=tok)
    tr.train()
    m.save_pretrained(OUT); tok.save_pretrained(OUT)
    print("[OK] Modelo salvo em", OUT)

if __name__ == '__main__':
    main()
