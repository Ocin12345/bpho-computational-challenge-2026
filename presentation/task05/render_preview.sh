#!/usr/bin/env bash

set -euo pipefail

presentation_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$presentation_directory/Task05_Hydrogen_Spectrum.pptx"

pdftoppm -png -singlefile -r 180 \
  "$temporary_directory/Task05_Hydrogen_Spectrum.pdf" \
  "$temporary_directory/Task05_Hydrogen_Spectrum_preview"

mkdir -p "$presentation_directory/preview"
mv \
  "$temporary_directory/Task05_Hydrogen_Spectrum_preview.png" \
  "$presentation_directory/preview/Task05_Hydrogen_Spectrum_preview.png"

printf 'Created %s\n' \
  "$presentation_directory/preview/Task05_Hydrogen_Spectrum_preview.png"
