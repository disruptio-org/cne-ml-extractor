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
  $docxScript = @'
import sys
from docx2pdf import convert

convert(sys.argv[1], sys.argv[2])
'@
  python -c $docxScript -- "$DocxPath" "$PdfPath"
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
$mlScript = @'
import sys
from cne_ml_extractor.pipeline_ml import process_pdf_to_csv

pdf_path, dtmnfr, csv_out = sys.argv[1:4]
csv_path = process_pdf_to_csv(pdf_path, dtmnfr=dtmnfr, out_csv=csv_out)
print("CSV:", csv_path)
'@
python -c $mlScript -- "$PdfToUse" "$Dtmnfr" "$CsvOut"

Write-Host "✅ CSV em $CsvOut"
