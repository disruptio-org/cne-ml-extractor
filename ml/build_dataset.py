from __future__ import annotations
import os, csv
from cne_ml_extractor.utils import (
    pdf_to_lines,
    SEC_EFETIVOS,
    SEC_SUPLENTES,
    LINE_NUM,
    normalize_quotes_dashes,
    guess_sigla,
)

IN_ROOT = './samples'
OUT_DIR = './data'
os.makedirs(os.path.join(OUT_DIR,'line_cls'), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR,'ner'), exist_ok=True)

def main():
    line_csv = os.path.join(OUT_DIR, 'line_cls', 'all_lines.csv')
    ner_conll = os.path.join(OUT_DIR, 'ner', 'all.conll')
    w_line = csv.writer(open(line_csv, 'w', newline='', encoding='utf-8')); w_line.writerow(['text','label'])
    ner_out = open(ner_conll, 'w', encoding='utf-8')

    for dirpath, dirnames, filenames in os.walk(IN_ROOT):
        for fn in filenames:
            if not fn.lower().endswith('.pdf'): continue
            pdf = os.path.join(dirpath, fn)
            pages = pdf_to_lines(pdf)
            for lines in pages:
                for raw in lines:
                    line = normalize_quotes_dashes(raw.strip())
                    if not line: continue
                    if SEC_EFETIVOS.search(line):
                        w_line.writerow([line,'SECAO']); continue
                    if SEC_SUPLENTES.search(line):
                        w_line.writerow([line,'SECAO']); continue
                    sigla_hint = guess_sigla(line)
                    if sigla_hint and ("-" in line or "LISTA" in line.upper()):
                        w_line.writerow([line,'HEADER_LISTA']); continue
                    if LINE_NUM.match(line):
                        w_line.writerow([line,'CANDIDATO'])
                        m = LINE_NUM.match(line)
                        tokens = line.split()
                        # marca tokens do nome como BIO (heurístico simples)
                        try:
                            num_tok = tokens.index(m.group(1))
                            start = num_tok + 1
                        except Exception:
                            start = 1
                        for i,t in enumerate(tokens):
                            if i < start: tag = 'O'
                            elif i == start: tag = 'B-NOME'
                            else: tag = 'I-NOME'
                            ner_out.write(f"{t} {tag}\n")
                        ner_out.write("\n")
                        continue
                    w_line.writerow([line,'OUTRO'])

    ner_out.close()
    print(f"[OK] Dataset: {line_csv} / {ner_conll}")

if __name__ == '__main__':
    main()
