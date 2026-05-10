from __future__ import annotations

from pathlib import Path


THESIS_ROOT = Path(r"C:\Users\paola\Tesis")

THESIS_PATHS = {
    "workspace": THESIS_ROOT / "CORRELA_TODOS",
    "raw_data": THESIS_ROOT / "01_Data",
    "processed": THESIS_ROOT / "02_Procesados",
    "scripts": THESIS_ROOT / "02_Scripts",
    "documentation": THESIS_ROOT / "03_Documentation",
    "results": THESIS_ROOT / "03_Resultados",
    "bibliography": THESIS_ROOT / "04_Bibliography",
    "presentations": THESIS_ROOT / "05_Presentations",
    "geospatial": THESIS_ROOT / "Analisis Geoespacial",
}


def thesis_path(key: str, *parts: str) -> Path:
    base = THESIS_PATHS[key]
    return base.joinpath(*parts)
