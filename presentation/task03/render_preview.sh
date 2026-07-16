#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task03_Planck_Einstein.pptx"

pdftoppm -png -singlefile -r 180 \
  "$temporary_directory/Task03_Planck_Einstein.pdf" \
  "$temporary_directory/Task03_Planck_Einstein_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task03_Planck_Einstein_preview.png" \
  "$presentation_directory/preview/Task03_Planck_Einstein_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task03_Planck_Einstein_preview.png"
