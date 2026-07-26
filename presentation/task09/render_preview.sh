#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice_command="${SOFFICE:-soffice}"
pdftoppm_command="${PDFTOPPM:-pdftoppm}"

"$soffice_command" --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task09_Compton_Scattering.pptx"

"$pdftoppm_command" -png -singlefile -r 300 \
  "$temporary_directory/Task09_Compton_Scattering.pdf" \
  "$temporary_directory/Task09_Compton_Scattering_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task09_Compton_Scattering_preview.png" \
  "$presentation_directory/preview/Task09_Compton_Scattering_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task09_Compton_Scattering_preview.png"
