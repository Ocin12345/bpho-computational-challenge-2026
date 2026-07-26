#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice_command="${SOFFICE:-soffice}"
pdftoppm_command="${PDFTOPPM:-pdftoppm}"

"$soffice_command" --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task08_Quantum_Mismatch_Calculator.pptx"

"$pdftoppm_command" -png -singlefile -r 300 \
  "$temporary_directory/Task08_Quantum_Mismatch_Calculator.pdf" \
  "$temporary_directory/Task08_Quantum_Mismatch_Calculator_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task08_Quantum_Mismatch_Calculator_preview.png" \
  "$presentation_directory/preview/Task08_Quantum_Mismatch_Calculator_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task08_Quantum_Mismatch_Calculator_preview.png"
