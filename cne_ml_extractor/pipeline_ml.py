from __future__ import annotations
import os, csv, re
from typing import Optional, List
from .utils import pdf_to_lines, SEC_EFETIVOS, SEC_SUPLENTES, LINE_NUM, normalize_quotes_dashes
from .ml_infer import MLExtractor

PARTY_HINT = re.compile(r"\b(PSD|CDS|PS|CHEGA|IL|VOLT|CDU|PAN|BLOCO|LIVRE|COLIGA|ALIAN[ÇC]A)\b", re.I)

def ensure_dir(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)

def process_pdf_to_csv(pdf_path: str, dtmnfr: str, out_csv: str,
                       line_model_dir: str = "models/line-cls-xlmr",
                       ner_model_dir: str = "models/ner-nome-xlmr",
                       device: str = "cpu") -> str:
    pages = pdf_to_lines(pdf_path)
    ml = MLExtractor(line_model_dir, ner_model_dir, device=device, conf_thr=0.55)

    current_sigla: Optional[str] = None
    current_nome_lista: Optional[str] = None
    orgao = "AM"
    in_section: Optional[str] = None
    seq_in_list = 0

    rows: List[List] = []
    header = ["DTMNFR","ORGAO","TIPO","SIGLA","SIMBOLO","NOME_LISTA","NUM_ORDEM","NOME_CANDIDATO","PARTIDO_PROPONENTE","INDEPENDENTE"]

    for page_idx, lines in enumerate(pages):
        joined = " \n ".join(lines).upper()
        if re.search(r"\b2\.\s*C[ÂA]MARA\s+MUNICIPAL\b", joined, re.I):
            orgao = "CM"

        for raw in lines:
            line = normalize_quotes_dashes(raw.strip())
            if not line:
                continue
            lbl, prob = ml.classify_line(line)

            # secções
            if lbl == "SECAO" and prob >= 0.55:
                if SEC_EFETIVOS.search(line):
                    in_section = "EFETIVOS"; seq_in_list = 0;  continue
                if SEC_SUPLENTES.search(line):
                    in_section = "SUPLENTES"; seq_in_list = 0; continue

            # header de lista
            if lbl == "HEADER_LISTA" and prob >= 0.55:
                current_nome_lista = line
                m = PARTY_HINT.search(line)
                current_sigla = (m.group(1) if m else "").upper() if m else ""
                seq_in_list = 0
                in_section = None
                continue

            # candidato
            if lbl == "CANDIDATO" and prob >= 0.55 and current_sigla:
                nome = ml.extract_nome(line)
                if not nome:
                    m = LINE_NUM.match(line)
                    nome = m.group(2) if m else line
                if in_section is None:
                    in_section = "EFETIVOS"; seq_in_list = 0
                seq_in_list += 1
                tipo = "2" if in_section == "EFETIVOS" else "3"
                rows.append([dtmnfr, orgao, tipo, current_sigla, current_sigla, current_nome_lista, seq_in_list, nome, current_sigla, False])
                continue

            # fallbacks
            if SEC_EFETIVOS.search(line): in_section="EFETIVOS"; seq_in_list=0; continue
            if SEC_SUPLENTES.search(line): in_section="SUPLENTES"; seq_in_list=0; continue
            if PARTY_HINT.search(line) and "-" in line:
                current_nome_lista = line
                m = PARTY_HINT.search(line)
                current_sigla = (m.group(1) if m else "").upper()
                seq_in_list = 0; in_section=None; continue

            m = LINE_NUM.match(line)
            if m and current_sigla:
                in_section = in_section or "EFETIVOS"
                seq_in_list += 1
                rows.append([dtmnfr, orgao, ("2" if in_section=="EFETIVOS" else "3"),
                             current_sigla, current_sigla, current_nome_lista, seq_in_list,
                             m.group(2), current_sigla, False])

    ensure_dir(out_csv)
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(header)
        w.writerows(rows)
    return out_csv
