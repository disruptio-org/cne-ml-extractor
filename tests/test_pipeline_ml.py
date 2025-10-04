import csv
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from cne_ml_extractor import pipeline_ml


@pytest.fixture(autouse=True)
def stub_ml(monkeypatch):
    monkeypatch.setattr(pipeline_ml, "pdf_to_lines", lambda path: [])

    class DummyML:
        def __init__(self, *args, **kwargs):
            pass

        def classify_line(self, line):
            return "OTHER", 0.0

        def extract_nome(self, line):
            return line

    monkeypatch.setattr(pipeline_ml, "MLExtractor", DummyML)


@pytest.mark.parametrize(
    "out_csv",
    [
        "results.csv",
        Path("nested") / "dir" / "results.csv",
    ],
)
def test_process_pdf_to_csv_creates_output(tmp_path, monkeypatch, out_csv):
    monkeypatch.chdir(tmp_path)
    output_path = pipeline_ml.process_pdf_to_csv("dummy.pdf", "DTMNFR", str(out_csv))

    assert Path(output_path).exists()
    with Path(output_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    assert rows[0] == [
        "DTMNFR",
        "ORGAO",
        "TIPO",
        "SIGLA",
        "SIMBOLO",
        "NOME_LISTA",
        "NUM_ORDEM",
        "NOME_CANDIDATO",
        "PARTIDO_PROPONENTE",
        "INDEPENDENTE",
    ]
    assert rows[1:] == []
