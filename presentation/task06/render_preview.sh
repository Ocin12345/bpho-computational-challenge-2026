#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice_command="${SOFFICE:-soffice}"
pdftoppm_command="${PDFTOPPM:-pdftoppm}"

"$soffice_command" --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task06_Electron_Diffraction.pptx"

"$pdftoppm_command" -png -singlefile -r 180 \
  "$temporary_directory/Task06_Electron_Diffraction.pdf" \
  "$temporary_directory/Task06_Electron_Diffraction_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task06_Electron_Diffraction_preview.png" \
  "$presentation_directory/preview/Task06_Electron_Diffraction_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task06_Electron_Diffraction_preview.png"
