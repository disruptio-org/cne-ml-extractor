param(
  [string]$Pdf   = ".\samples\editais\input\1116_Odivelas_AM e CM 28637.pdf",
  [string]$Dtmnfr= "111600",
  [string]$OutDir= ".\samples\editais\output"
)

$ErrorActionPreference = "Stop"
New-Item -Force -ItemType Directory $OutDir | Out-Null

$CsvOut = Join-Path $OutDir "infer_AM_CM_final.csv"
$script = @'
import sys
from cne_ml_extractor.pipeline_ml import process_pdf_to_csv

pdf, dtmnfr, csv_out = sys.argv[1:4]
csv_path = process_pdf_to_csv(pdf, dtmnfr=dtmnfr, out_csv=csv_out)
print('CSV:', csv_path)
'@

python -c $script -- "$Pdf" "$Dtmnfr" "$CsvOut"

if ($LASTEXITCODE -ne 0) {
  throw "Python retornou o código de saída $LASTEXITCODE"
}

Write-Host "✅ CSV em $CsvOut"
