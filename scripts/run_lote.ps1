param(
  [string]$Municipio = "Odivelas",
  [string]$Dtmnfr    = "111600",
  [string]$DocxPath  = ".\samples\$Municipio\input\edital.docx"
)

$ErrorActionPreference = "Stop"
$base   = ".\samples\$Municipio"
$inDir  = Join-Path $base "input"
$outDir = Join-Path $base "output"
New-Item -Force -ItemType Directory $inDir,$outDir | Out-Null

# DOCX -> PDF (opcional)
if (Test-Path $DocxPath) {
  pip show docx2pdf | Out-Null 2>$null; if ($LASTEXITCODE -ne 0) { pip install -U docx2pdf }
  $PdfPath = Join-Path $inDir "$Municipio.pdf"
  python - <<PY
from docx2pdf import convert
convert(r"""$DocxPath""", r"""$PdfPath""")
PY
}

# Contexto (referência DTMNFR)
@"
dtmnfr: "$Dtmnfr"
orgao: null
sigla_expected: null
simbolo: null
nome_lista: null
"@ | Set-Content -Encoding UTF8 (Join-Path $base "ALL_context.yaml")

# Inferência ML
$PdfToUse = (Get-ChildItem $inDir -Filter *.pdf | Select-Object -First 1).FullName
if (-not $PdfToUse) { throw "Nenhum PDF encontrado em $inDir" }

$CsvOut = Join-Path $outDir "$Municipio" + "_AM_CM_final.csv"
python - <<PY
from cne_ml_extractor.pipeline_ml import process_pdf_to_csv
csv_path = process_pdf_to_csv(r"""$PdfToUse""", dtmnfr=r"""$Dtmnfr""", out_csv=r"""$CsvOut""")
print("CSV:", csv_path)
PY

Write-Host "✅ CSV em $CsvOut"
