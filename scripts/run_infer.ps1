param(
  [string]$Pdf   = ".\samples\Odivelas\input\edital.pdf",
  [string]$Dtmnfr= "111600",
  [string]$OutDir= ".\samples\Odivelas\output"
)

$ErrorActionPreference = "Stop"
New-Item -Force -ItemType Directory $OutDir | Out-Null

$CsvOut = Join-Path $OutDir "infer_AM_CM_final.csv"
python - <<PY
from cne_ml_extractor.pipeline_ml import process_pdf_to_csv
csv_path = process_pdf_to_csv(r"""$Pdf""", dtmnfr=r"""$Dtmnfr""", out_csv=r"""$CsvOut""")
print("CSV:", csv_path)
PY

Write-Host "✅ CSV em $CsvOut"
