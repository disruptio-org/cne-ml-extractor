from __future__ import annotations
import fitz, re
from typing import List

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

def normalize_quotes_dashes(s: str) -> str:
    return (s.replace("–","-").replace("—","-")
            .replace("’","'").replace("‘","'")
            .replace("“",'"').replace("”",'"'))
