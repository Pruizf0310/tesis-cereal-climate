# Manuscrito de tesis

Archivo principal:

```text
main.tex
```

## Compilar PDF sin Overleaf

Este repositorio incluye un workflow de GitHub Actions llamado **Build manuscript PDF**.

Para generar el PDF:

1. En GitHub, entra a la pestaña **Actions**.
2. Abre **Build manuscript PDF**.
3. Ejecuta **Run workflow** o espera a que se active con un push a `manuscript/`.
4. Cuando termine, abre la ejecución.
5. Descarga el artifact llamado `tesis-manuscript-pdf`.

El PDF compilado se llama:

```text
main.pdf
```

## Compilar localmente

Los capítulos se escriben en `chapters/*.md`. Antes de compilar hay que convertirlos a LaTeX con pandoc; los `.tex` quedan en `chapters/tex/` y no se versionan.

Si tienes pandoc y MiKTeX o TeX Live instalados:

```powershell
cd manuscript
bash convertir_capitulos.sh
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```
