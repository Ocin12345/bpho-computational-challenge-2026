#!/usr/bin/env bash

set -euo pipefail

master_directory="$(cd "$(dirname "$0")" && pwd)"
temporary_directory="$(mktemp -d)"
trap 'rm -rf "$temporary_directory"' EXIT

soffice_command="${SOFFICE:-soffice}"
pdftoppm_command="${PDFTOPPM:-pdftoppm}"
stem="BPhO_Computational_Challenge_Tasks_1_to_10"

"$soffice_command" --headless --convert-to pdf \
  --outdir "$temporary_directory" \
  "$master_directory/$stem.pptx" >/dev/null

"$pdftoppm_command" -png -r 300 \
  "$temporary_directory/$stem.pdf" \
  "$temporary_directory/${stem}_preview"

mkdir -p "$master_directory/preview"
for page in "$temporary_directory"/${stem}_preview-*.png; do
  filename="$(basename "$page")"
  mv "$page" "$master_directory/preview/$filename"
  printf 'Created %s\n' "$master_directory/preview/$filename"
done

cp "$temporary_directory/$stem.pdf" "$master_directory/$stem.pdf"
printf 'Created %s\n' "$master_directory/$stem.pdf"
