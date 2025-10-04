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


def test_process_pdf_to_csv_exports_candidates_with_generic_sigla(tmp_path, monkeypatch):
    pages = [[
        "XYZ - Lista de Cidadãos",
        "1 João Silva",
        "2 Maria Costa",
    ]]

    class DummyML:
        def __init__(self, *args, **kwargs):
            pass

        def classify_line(self, line):
            upper = line.upper()
            if "LISTA" in upper:
                return "HEADER_LISTA", 0.95
            if pipeline_ml.LINE_NUM.match(line):
                return "CANDIDATO", 0.95
            return "OUTRO", 0.1

        def extract_nome(self, line):
            return line.split(" ", 1)[1]

    monkeypatch.setattr(pipeline_ml, "pdf_to_lines", lambda path: pages)
    monkeypatch.setattr(pipeline_ml, "MLExtractor", DummyML)

    output_path = pipeline_ml.process_pdf_to_csv(
        "dummy.pdf", "DTMNFR", str(tmp_path / "results.csv")
    )

    with Path(output_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    assert rows[1][3] == "XYZ"
    assert rows[1][7] == "João Silva"
    assert rows[2][3] == "XYZ"
    assert rows[2][6] == "2"


def test_process_pdf_to_csv_fallback_sigla_without_hyphen(tmp_path, monkeypatch):
    pages = [[
        "MOVIMENTO LIVRE LISTA UNICA",
        "1 Ana Dias",
    ]]

    class DummyML:
        def __init__(self, *args, **kwargs):
            pass

        def classify_line(self, line):
            upper = line.upper()
            if "LISTA" in upper:
                return "HEADER_LISTA", 0.95
            if pipeline_ml.LINE_NUM.match(line):
                return "CANDIDATO", 0.95
            return "OUTRO", 0.1

        def extract_nome(self, line):
            return line.split(" ", 1)[1]

    monkeypatch.setattr(pipeline_ml, "pdf_to_lines", lambda path: pages)
    monkeypatch.setattr(pipeline_ml, "MLExtractor", DummyML)

    output_path = pipeline_ml.process_pdf_to_csv(
        "dummy.pdf", "DTMNFR", str(tmp_path / "results.csv")
    )

    with Path(output_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    # Fallback should still assign a sigla so the candidate is exported
    assert rows[1][3] == "MOVIMENTO"
    assert rows[1][7] == "Ana Dias"


def test_process_pdf_to_csv_handles_lista_single_letter(tmp_path, monkeypatch):
    pages = [[
        "Lista A",
        "1 João Silva",
        "2 Maria Costa",
    ]]

    class DummyML:
        def __init__(self, *args, **kwargs):
            pass

        def classify_line(self, line):
            upper = line.upper()
            if "LISTA" in upper:
                return "HEADER_LISTA", 0.95
            if pipeline_ml.LINE_NUM.match(line):
                return "CANDIDATO", 0.95
            return "OUTRO", 0.1

        def extract_nome(self, line):
            return line.split(" ", 1)[1]

    monkeypatch.setattr(pipeline_ml, "pdf_to_lines", lambda path: pages)
    monkeypatch.setattr(pipeline_ml, "MLExtractor", DummyML)

    output_path = pipeline_ml.process_pdf_to_csv(
        "dummy.pdf", "DTMNFR", str(tmp_path / "results.csv")
    )

    with Path(output_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    assert rows[1][3] == "A"
    assert rows[2][3] == "A"


def test_process_pdf_to_csv_handles_mixed_orgao_pages(tmp_path, monkeypatch):
    pages = [[
        "1. Assembleia Municipal",
        "LISTA AM - Partido X",
        "1 João Silva",
        "2 Maria Costa",
        "2. Câmara Municipal",
        "LISTA CM - Partido Y",
        "1 Carlos Gomes",
    ]]

    class DummyML:
        def __init__(self, *args, **kwargs):
            pass

        def classify_line(self, line):
            upper = line.upper()
            if "LISTA" in upper:
                return "HEADER_LISTA", 0.95
            if pipeline_ml.LINE_NUM.match(line):
                return "CANDIDATO", 0.95
            return "OUTRO", 0.1

        def extract_nome(self, line):
            return line.split(" ", 1)[1]

    monkeypatch.setattr(pipeline_ml, "pdf_to_lines", lambda path: pages)
    monkeypatch.setattr(pipeline_ml, "MLExtractor", DummyML)

    output_path = pipeline_ml.process_pdf_to_csv(
        "dummy.pdf", "DTMNFR", str(tmp_path / "results.csv")
    )

    with Path(output_path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = list(reader)

    assert rows[1][1] == "AM"
    assert rows[2][1] == "AM"
    assert rows[3][1] == "CM"
    assert rows[3][7] == "Carlos Gomes"
