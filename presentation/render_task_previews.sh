#!/usr/bin/env bash

set -euo pipefail

presentation_root="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice_command="${SOFFICE:-soffice}"
pdftoppm_command="${PDFTOPPM:-pdftoppm}"

presentations=(
  "task01/Task01_Random_Walk.pptx"
  "task02/Task02_Brownian_Motion.pptx"
  "task03/Task03_Planck_Einstein.pptx"
  "task04/Task04_Photoelectric_Effect.pptx"
  "task05/Task05_Hydrogen_Spectrum.pptx"
  "task06/Task06_Electron_Diffraction.pptx"
)

for relative_path in "${presentations[@]}"; do
  task_directory="${relative_path%%/*}"
  filename="${relative_path##*/}"
  stem="${filename%.pptx}"
  task_temporary_directory="$temporary_directory/$task_directory"
  mkdir -p "$task_temporary_directory"
  "$soffice_command" --headless --convert-to pdf \
    --outdir "$task_temporary_directory" \
    "$presentation_root/$relative_path" >/dev/null
  "$pdftoppm_command" -png -singlefile -r 300 \
    "$task_temporary_directory/$stem.pdf" \
    "$task_temporary_directory/${stem}_preview"
  mkdir -p "$presentation_root/$task_directory/preview"
  mv "$task_temporary_directory/${stem}_preview.png" \
    "$presentation_root/$task_directory/preview/${stem}_preview.png"
  printf 'Created %s\n' \
    "$presentation_root/$task_directory/preview/${stem}_preview.png"
done
