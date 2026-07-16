#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task04_Photoelectric_Effect.pptx"

pdftoppm -png -singlefile -r 180 \
  "$temporary_directory/Task04_Photoelectric_Effect.pdf" \
  "$temporary_directory/Task04_Photoelectric_Effect_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task04_Photoelectric_Effect_preview.png" \
  "$presentation_directory/preview/Task04_Photoelectric_Effect_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task04_Photoelectric_Effect_preview.png"
