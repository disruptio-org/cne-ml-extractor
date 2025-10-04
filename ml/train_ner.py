from __future__ import annotations
import os, random
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer
from datasets import DatasetDict

DATA = './data/ner/all.conll'
OUT  = './models/ner-nome-xlmr'

def load_conll(path):
    sents, tags = [], []
    with open(path, 'r', encoding='utf-8') as f:
        tokens, t = [], []
        for line in f:
            line=line.rstrip()
            if not line:
                if tokens:
                    sents.append(tokens); tags.append(t)
                    tokens, t = [], []
                continue
            tok, tag = line.split()
            tokens.append(tok); t.append(tag)
    if tokens: sents.append(tokens); tags.append(t)
    return sents, tags

def main():
    os.makedirs(OUT, exist_ok=True)
    sents, tags = load_conll(DATA)
    idx = list(range(len(sents)))
    random.Random(42).shuffle(idx)
    m = int(0.8*len(idx))
    train_idx, dev_idx = idx[:m], idx[m:]
    train = {'tokens':[s for i,s in enumerate(sents) if i in train_idx], 'ner_tags':[t for i,t in enumerate(tags) if i in train_idx]}
    dev   = {'tokens':[s for i,s in enumerate(sents) if i in dev_idx],   'ner_tags':[t for i,t in enumerate(tags) if i in dev_idx]}

    labels = sorted({tag for seq in (train['ner_tags']+dev['ner_tags']) for tag in seq})
    label2id = {l:i for i,l in enumerate(labels)}
    id2label = {i:l for l,i in label2id.items()}

    tok = AutoTokenizer.from_pretrained('xlm-roberta-base')

    def to_features(batch):
        from transformers import BatchEncoding
        input_ids, attn, lab = [], [], []
        for tokens, tags in zip(batch['tokens'], batch['ner_tags']):
            enc = tok(tokens, is_split_into_words=True, truncation=True)
            word_ids = enc.word_ids()
            y = []
            for wid in word_ids:
                if wid is None: y.append(-100)
                else: y.append(label2id[tags[wid]])
            input_ids.append(enc['input_ids']); attn.append(enc['attention_mask']); lab.append(y)
        return {'input_ids': input_ids, 'attention_mask': attn, 'labels': lab}

    ds = DatasetDict(train=train, validation=dev).map(to_features, batched=True)

    m = AutoModelForTokenClassification.from_pretrained('xlm-roberta-base', num_labels=len(labels), id2label=id2label, label2id=label2id)
    args = TrainingArguments(output_dir=OUT, per_device_train_batch_size=8, per_device_eval_batch_size=8, learning_rate=3e-5,
                             num_train_epochs=8, evaluation_strategy='epoch', save_strategy='epoch', logging_steps=50)

    def collate(features):
        from torch.nn.utils.rnn import pad_sequence
        import torch
        def pad(key, pad_val):
            return pad_sequence([torch.tensor(f[key]) for f in features], batch_first=True, padding_value=pad_val)
        return {'input_ids': pad('input_ids', 1), 'attention_mask': pad('attention_mask', 0), 'labels': pad('labels', -100)}

    tr = Trainer(model=m, args=args, train_dataset=ds['train'], eval_dataset=ds['validation'], tokenizer=tok, data_collator=collate)
    tr.train()
    m.save_pretrained(OUT); tok.save_pretrained(OUT)
    print("[OK] Modelo salvo em", OUT)

if __name__ == '__main__':
    main()
