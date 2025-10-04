from __future__ import annotations
import fitz, re
from typing import List, Optional

def pdf_to_lines(pdf_path: str) -> list[list[str]]:
    pages = []
    with fitz.open(pdf_path) as doc:
        for page in doc:
            txt = page.get_text("text") or ""
            lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
            pages.append(lines)
    return pages

SEC_EFETIVOS  = re.compile(r"CANDIDAT[OA]S?\s+EFETIV[OA]S", re.I)
SEC_SUPLENTES = re.compile(r"CANDIDAT[OA]S?\s+SUPLENTES",   re.I)
LINE_NUM      = re.compile(r"^\s*(\d+)[\.\-ºo]?\s+(.+?)\s*$")

_SIGLA_TOKEN = r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9]{2,}"
_SIGLA_PART = rf"{_SIGLA_TOKEN}(?:[/-]{_SIGLA_TOKEN})*"
_SIGLA_BEFORE_LISTA = re.compile(rf"\b({_SIGLA_PART})\b(?=\s*-\s*LISTA)", re.I)
_SIGLA_BEFORE_HYPHEN = re.compile(rf"\b({_SIGLA_PART})\b(?=\s*-\s*)")
_SIGLA_GENERIC = re.compile(rf"\b({_SIGLA_PART})\b")

def normalize_quotes_dashes(s: str) -> str:
    return (s.replace("–","-").replace("—","-")
            .replace("’","'").replace("‘","'")
            .replace("“",'"').replace("”",'"'))

def guess_sigla(line: str) -> Optional[str]:
    """Heuristically extract a sigla from a list header line."""
    upper_line = line.upper()

    for pattern in (_SIGLA_BEFORE_LISTA, _SIGLA_BEFORE_HYPHEN):
        m = pattern.search(upper_line)
        if m:
            return m.group(1)

    stopwords = {"DE", "DA", "DO", "DAS", "DOS", "E", "LISTA", "LISTAS"}

    for token in _SIGLA_GENERIC.findall(upper_line):
        cleaned = token.strip(".,;:()[]{}")
        if len(cleaned) < 2:
            continue
        if cleaned in stopwords:
            continue
        return cleaned

    return None
