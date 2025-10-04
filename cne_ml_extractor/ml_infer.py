from __future__ import annotations
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForTokenClassification

LABELS = ["OUTRO","SECAO","HEADER_LISTA","CANDIDATO"]

class MLExtractor:
    def __init__(self, line_model_dir: str, ner_model_dir: str, device: str = "cpu", conf_thr: float = 0.55):
        self.dev = device
        self.conf_thr = conf_thr
        self.tok_line = AutoTokenizer.from_pretrained(line_model_dir)
        self.m_line   = AutoModelForSequenceClassification.from_pretrained(line_model_dir).to(device).eval()
        self.tok_ner  = AutoTokenizer.from_pretrained(ner_model_dir)
        self.m_ner    = AutoModelForTokenClassification.from_pretrained(ner_model_dir).to(device).eval()
        self.softmax  = torch.nn.Softmax(dim=-1)

    def classify_line(self, text: str):
        with torch.no_grad():
            enc = self.tok_line(text, return_tensors="pt", truncation=True).to(self.dev)
            logits = self.m_line(**enc).logits
            probs = self.softmax(logits)[0].cpu().tolist()
            idx = int(logits.argmax(-1).item())
            return LABELS[idx], float(probs[idx])

    def extract_nome(self, text: str):
        words = text.split()
        if not words:
            return None
        with torch.no_grad():
            enc = self.tok_ner(words, is_split_into_words=True, return_tensors="pt", truncation=True).to(self.dev)
            logits = self.m_ner(**enc).logits[0].cpu()
            ids = logits.argmax(-1).tolist()
            id2label = self.m_ner.config.id2label
            tags = [id2label.get(i, "O") for i in ids]
        tags = tags[1:len(words)+1]
        nome_tokens = []
        collecting = False
        for w, t in zip(words, tags):
            if t.startswith("B-"):
                nome_tokens = [w]; collecting = True
            elif t.startswith("I-") and collecting:
                nome_tokens.append(w)
            elif collecting:
                break
        return " ".join(nome_tokens) if nome_tokens else None
