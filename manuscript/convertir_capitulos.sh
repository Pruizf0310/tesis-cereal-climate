#!/usr/bin/env bash
# Convierte los capítulos en Markdown (chapters/*.md) a LaTeX (chapters/tex/*.tex) para compilar main.tex.
# Los capítulos se escriben en Markdown; los .tex se generan y no se versionan.
# Quita la numeración escrita a mano en los títulos («# 4. Metodología», «## 4.1 Diseño…»),
# porque LaTeX ya numera capítulos y secciones.
# Uso, desde la carpeta manuscript:  bash convertir_capitulos.sh   (requiere pandoc)
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p chapters/tex
for f in chapters/*.md; do
  n=$(basename "$f" .md)
  sed -E 's/^(#{1,6}) [0-9]+(\.[0-9]+)*\.? /\1 /' "$f" \
    | pandoc -f markdown -t latex --top-level-division=chapter --biblatex -o "chapters/tex/$n.tex"
  echo "chapters/tex/$n.tex"
done
