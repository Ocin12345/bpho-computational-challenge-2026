#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice_command="${SOFFICE:-soffice}"
pdftoppm_command="${PDFTOPPM:-pdftoppm}"

"$soffice_command" --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task07_Particle_In_A_Box.pptx"

"$pdftoppm_command" -png -singlefile -r 300 \
  "$temporary_directory/Task07_Particle_In_A_Box.pdf" \
  "$temporary_directory/Task07_Particle_In_A_Box_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task07_Particle_In_A_Box_preview.png" \
  "$presentation_directory/preview/Task07_Particle_In_A_Box_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task07_Particle_In_A_Box_preview.png"
