# CNE ML Extractor (On-Prem, Offline)

Extrator **offline** baseado em **Machine Learning** para ler editais (AM/CM) e exportar CSV com:
`DTMNFR;ORGAO;TIPO;SIGLA;SIMBOLO;NOME_LISTA;NUM_ORDEM;NOME_CANDIDATO;PARTIDO_PROPONENTE;INDEPENDENTE`

Funciona 100% **on-prem** (sem internet), usando **PyMuPDF + OCR** e **Transformers** para:
- **Classificação de linhas** (`HEADER_LISTA`, `SECAO`, `CANDIDATO`, `OUTRO`)
- **NER** (etiquetagem do **NOME** do candidato) nas linhas `CANDIDATO`

## Instalação (Windows)

```powershell
python -m venv .venv
powershell -ExecutionPolicy Bypass -Command ". .\.venv\Scripts\Activate.ps1"
pip install -U pip
pip install -r requirements.txt
```

> **OCR**: Instala Tesseract e seleciona **Portuguese** na instalação.

## Estrutura

```
cne-ml-extractor/
  cne_ml_extractor/
    ml_infer.py
    pipeline_ml.py
    utils.py
  ml/
    build_dataset.py
    train_line_cls.py
    train_ner.py
  scripts/
    run_lote.ps1
    run_infer.ps1
  samples/
  models/
  data/
```

## Pipeline rápido

1) Coloca PDFs em `samples/<Municipio>/input/`  
2) Cria `samples/<Municipio>/ALL_context.yaml` (com `dtmnfr: "<codigo>"`)  
3) Corre:
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_lote.ps1 `
  -Municipio "Odivelas" `
  -Dtmnfr "111600" `
  -DocxPath ".\samples\Odivelas\input\edital.docx"
```

## Treinar (offline)

```powershell
python .\ml\build_dataset.py
python .\ml\train_line_cls.py
python .\ml\train_ner.py
```

## Inferência directa

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\run_infer.ps1 `
  -Pdf ".\samples\Odivelas\input\edital.pdf" `
  -Dtmnfr "111600" `
  -OutDir ".\samples\Odivelas\output"
```
