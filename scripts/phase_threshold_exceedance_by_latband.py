# %% [markdown]
# # Probabilidad histórica de superación de umbrales climáticos por fase fenológica y franja latitudinal
#
# Este script está diseñado para abrirse en JupyterLab como un archivo `.py` con celdas.
# Calcula, para cada cultivo, fase fenológica y franja latitudinal, la probabilidad
# histórica de que la variable climática crítica supere su umbral durante 1981-2016.
#
# **Idea central**
#
# - No descarga series globales.
# - No lanza exportaciones masivas.
# - Consulta Earth Engine bajo demanda por cultivo-fase-franja y por un subconjunto
#   controlado de píxeles.
# - Deja resultados auditables en Excel, JSON y HTML.
#
# **Salidas esperadas**
#
# - `phase_threshold_exceedance_by_latband.xlsx`
# - `phase_threshold_exceedance_by_latband.json`
# - `phase_threshold_exceedance_by_latband.html`
#
# Por seguridad, el script corre en modo prueba por defecto:
#
# ```python
# RUN_FULL = False
# ```
#
# Cuando verifiques que los resultados tienen sentido, cambia `RUN_FULL = True`.

# %%
from __future__ import annotations

import json
import math
import os
import re
import sys
import textwrap
import traceback
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import ee
except ImportError:
    ee = None


# %% [markdown]
# ## 1. Configuración general
#
# Rutas de entrada usadas por el script:
#
# - Tabla maestra GEOGLAM/CM4EW con fases, fechas DOY, variable crítica, umbral y fuente.
# - Calendario fenológico típico web, si existe.
# - Documento Markdown de calendarios de investigación.
# - Inventarios de píxeles reconstruidos desde H5 por cultivo.
#
# Si `calendarios_fenologicos_tipicos_web.xlsx` no existe, el script usa como fallback
# el archivo ya generado:
#
# `C:\Users\paola\Tesis\03_Resultados\Clima_phase\calendar_windows_by_crop_band_season.csv`
#
# Ese fallback queda registrado en `diagnostico_variables`.

# %%
BASE_TESIS = Path(r"C:\Users\paola\Tesis")
FENO_DIR = BASE_TESIS / "03_Resultados" / "Fenologia"
CLIMA_PHASE_DIR = BASE_TESIS / "03_Resultados" / "Clima_phase"

MASTER_TABLE_PATH = FENO_DIR / "geoglam_cm4ew_tabla_maestra.xlsx"
TYPICAL_CALENDAR_XLSX = FENO_DIR / "calendarios_fenologicos_tipicos_web.xlsx"
TYPICAL_CALENDAR_FALLBACK_CSV = CLIMA_PHASE_DIR / "calendar_windows_by_crop_band_season.csv"
CALENDAR_RESEARCH_MD = BASE_TESIS / "calendarios_fenologicos_investigacion.md"

PIXEL_FILES = {
    "maize": CLIMA_PHASE_DIR / "maize_h5_pixels_latlon.csv",
    "rice": CLIMA_PHASE_DIR / "rice_h5_pixels_latlon.csv",
    "wheat": CLIMA_PHASE_DIR / "wheat_h5_pixels_latlon.csv",
    "soybean": CLIMA_PHASE_DIR / "soybean_h5_pixels_latlon.csv",
}

OUTPUT_XLSX = CLIMA_PHASE_DIR / "phase_threshold_exceedance_by_latband.xlsx"
OUTPUT_JSON = CLIMA_PHASE_DIR / "phase_threshold_exceedance_by_latband.json"
OUTPUT_HTML = CLIMA_PHASE_DIR / "phase_threshold_exceedance_by_latband.html"

START_YEAR = 1981
END_YEAR = 2016

# Seguridad: por defecto solo corre una prueba pequeña.
RUN_FULL = False

TEST_CROP = "maize"
TEST_PHASE_MACRO_CONTAINS = "vegetativo"
TEST_LAT_BAND_LABEL = "40S-50S"
TEST_MAX_PIXELS = 1

# En modo completo puede limitarse por píxeles por combinación para evitar consultas enormes.
# Si quieres usar todos los píxeles, cambia este valor a None, pero conviene hacerlo por tandas.
FULL_MAX_PIXELS_PER_COMBINATION: Optional[int] = 25

ERA5_DATASET_ID = "ECMWF/ERA5_LAND/DAILY_AGGR"
ERA5_NATIVE_PIXEL_SIZE_M = 11132

print("Configuración cargada")
print(f"RUN_FULL = {RUN_FULL}")
print(f"Periodo = {START_YEAR}-{END_YEAR}")
print(f"Carpeta de salida = {CLIMA_PHASE_DIR}")


# %% [markdown]
# ## 2. Utilidades de normalización y diagnóstico
#
# Se normalizan:
#
# - nombres de cultivo a `maize`, `rice`, `wheat`, `soybean`;
# - fases originales a macrofases comparables;
# - franjas latitudinales de 10 grados;
# - variables críticas textuales a variables ERA5-Land consultables.
#
# El script no fuerza cálculos cuando la variable no puede representarse con ERA5-Land.
# En esos casos deja una advertencia en `diagnostico_variables`.

# %%
diagnostics: List[Dict[str, Any]] = []


def log_diag(level: str, context: str, message: str, **extra: Any) -> None:
    row = {"level": level, "context": context, "message": message}
    row.update(extra)
    diagnostics.append(row)
    print(f"[{level}] {context}: {message}")


def clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def strip_accents(value: str) -> str:
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ü": "u",
        "ñ": "n",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ó": "O",
        "Ú": "U",
        "Ü": "U",
        "Ñ": "N",
    }
    for src, dst in replacements.items():
        value = value.replace(src, dst)
    return value


def normalize_crop(value: Any) -> Optional[str]:
    text = strip_accents(clean_text(value).lower())
    mapping = {
        "maiz": "maize",
        "maize": "maize",
        "corn": "maize",
        "arroz": "rice",
        "rice": "rice",
        "trigo": "wheat",
        "wheat": "wheat",
        "soya": "soybean",
        "soy": "soybean",
        "soybean": "soybean",
        "soybeans": "soybean",
    }
    return mapping.get(text)


def normalize_macro_phase(fase_original: Any, fase_estandar: Any = "", phase_name: Any = "") -> str:
    text = " ".join(
        strip_accents(clean_text(v).lower())
        for v in [fase_original, fase_estandar, phase_name]
        if clean_text(v)
    )
    if any(k in text for k in ["germin", "emerg", "siembra", "establecimiento", "seedling"]):
        return "germinacion/emergencia"
    if any(k in text for k in ["vegetativa", "vegetativo", "tillering", "macoll"]):
        if any(k in text for k in ["reproductiva", "reproductivo", "flor", "antesis"]):
            return "floracion/reproductivo"
        return "vegetativo"
    if any(k in text for k in ["flor", "antesis", "reproductiva", "reproductivo"]):
        return "floracion/reproductivo"
    if any(k in text for k in ["llenado", "grain", "grano", "terminal"]):
        return "llenado de grano"
    if any(k in text for k in ["maduracion", "madurez", "cosecha", "harvest"]):
        return "madurez/cosecha"
    if "fuera" in text or "outofseason" in text:
        return "fuera de temporada"
    if "fin" in text:
        return "fin de temporada"
    return "sin_clasificar"


LAT_BANDS = [
    (40, 50, "50N-40N"),
    (30, 40, "40N-30N"),
    (20, 30, "30N-20N"),
    (10, 20, "20N-10N"),
    (0, 10, "10N-0"),
    (-10, 0, "0-10S"),
    (-20, -10, "10S-20S"),
    (-30, -20, "20S-30S"),
    (-40, -30, "30S-40S"),
    (-50, -40, "40S-50S"),
]


def lat_to_band_label(lat: float) -> Optional[str]:
    for lower, upper, label in LAT_BANDS:
        if lower <= lat < upper:
            return label
    if math.isclose(lat, 50):
        return "50N-40N"
    if math.isclose(lat, -50):
        return "40S-50S"
    return None


def h5_band_to_label(value: Any) -> Optional[str]:
    text = clean_text(value)
    match = re.match(r"(-?\d+)_to_(-?\d+)", text)
    if not match:
        return None
    a, b = int(match.group(1)), int(match.group(2))
    center = (a + b) / 2
    return lat_to_band_label(center)


def parse_first_number(text: Any) -> Optional[float]:
    raw = clean_text(text)
    if not raw:
        return None
    normalized = (
        raw.replace("−", "-")
        .replace("–", "-")
        .replace("—", "-")
        .replace(",", ".")
    )
    # Evita capturar años de referencias si hay valores con unidades antes.
    matches = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", normalized)
    if not matches:
        return None
    values = [float(m) for m in matches]
    # Para rangos térmicos tipo 35/25 o 38/28 suele interesar el umbral diurno/máximo.
    return values[0]


@dataclass
class VariableSpec:
    variable_gee: Optional[str]
    reducer: str
    unit: str
    operator: str
    threshold: Optional[float]
    source_band: Optional[str]
    observation: str


def infer_variable_spec(variable_text: Any, threshold_text: Any, stress_text: Any) -> VariableSpec:
    variable = strip_accents(clean_text(variable_text).lower())
    threshold_raw = clean_text(threshold_text)
    stress = strip_accents(clean_text(stress_text).lower())
    threshold = parse_first_number(threshold_raw)
    operator = ">"
    observation = ""

    if any(token in threshold_raw for token in ["<", "menor", "por debajo"]) or "deficit" in variable:
        operator = "<"
    if any(token in threshold_raw for token in ["≥", ">=", ">"]):
        operator = ">"

    if "maxima" in variable or "tmax" in variable:
        return VariableSpec("tmax_c", "max", "degC", operator, threshold, "temperature_2m_max", observation)
    if "minima" in variable or "tmin" in variable:
        return VariableSpec("tmin_c", "min", "degC", operator, threshold, "temperature_2m_min", observation)
    if "temperatura" in variable or "aire" in variable:
        # Si el texto habla de llenado con Tmax media, se usa tmax_c/max; si no, tmean_c/mean.
        if "tmax" in threshold_raw.lower() or "max" in variable:
            return VariableSpec("tmax_c", "max", "degC", operator, threshold, "temperature_2m_max", observation)
        return VariableSpec("tmean_c", "mean", "degC", operator, threshold, "temperature_2m", observation)
    if "precipit" in variable or "lluvia" in variable:
        return VariableSpec("precip_mm", "sum", "mm", operator, threshold, "total_precipitation_sum", observation)
    if "deficit" in variable:
        return VariableSpec("precip_mm", "sum", "mm", "<", threshold, "total_precipitation_sum", "Proxy: déficit hídrico operacionalizado como precipitación acumulada baja.")
    if "humedad del suelo" in variable or "zona radicular" in variable:
        return VariableSpec("rootzone_sm", "mean", "m3/m3", "<", threshold, "rootzone_sm", "rootzone_sm = swvl1*0.07 + swvl2*0.21 + swvl3*0.72.")
    if "potencial hidrico" in variable:
        return VariableSpec(
            None,
            "mean",
            "MPa",
            "<",
            threshold,
            None,
            "No calculado: ERA5-Land no entrega potencial hídrico de suelo/solución directamente. Requiere pedotransferencia o proxy externo.",
        )
    if "radiacion" in variable or "solar" in variable:
        return VariableSpec(
            "solar_radiation",
            "sum",
            "J/m2",
            operator,
            threshold,
            "surface_solar_radiation_downwards_sum",
            "Se consulta solo si la banda existe en ERA5-Land Daily Aggregated.",
        )

    return VariableSpec(None, "mean", "", operator, threshold, None, "Variable crítica no mapeada a ERA5-Land.")


def compare_threshold(value: Optional[float], threshold: Optional[float], operator: str) -> Optional[bool]:
    if value is None or threshold is None or pd.isna(value) or pd.isna(threshold):
        return None
    if operator == "<":
        return bool(value < threshold)
    if operator == "<=":
        return bool(value <= threshold)
    if operator == ">=":
        return bool(value >= threshold)
    return bool(value > threshold)


def max_consecutive_true(flags: Iterable[bool]) -> int:
    best = 0
    current = 0
    for flag in flags:
        if flag:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


# %% [markdown]
# ## 3. Lectura de insumos
#
# Esta celda carga:
#
# - tabla maestra;
# - calendario típico/fallback;
# - inventarios de píxeles H5;
# - texto Markdown de calendarios de investigación.
#
# También crea la columna `franja_latitudinal` de 10 grados para cada píxel.

# %%
def require_file(path: Path, label: str) -> None:
    if not path.exists():
        raise FileNotFoundError(f"No se encontró {label}: {path}")


require_file(MASTER_TABLE_PATH, "tabla maestra")

master = pd.read_excel(MASTER_TABLE_PATH, sheet_name="tabla_maestra")
master["cultivo_norm"] = master["cultivo"].map(normalize_crop)
master["fase_macro"] = master.apply(
    lambda r: normalize_macro_phase(
        r.get("fase_original", ""),
        r.get("fase_estandar", ""),
        r.get("phase_name", ""),
    ),
    axis=1,
)

calendar_source = ""
if TYPICAL_CALENDAR_XLSX.exists():
    typical_calendar = pd.read_excel(TYPICAL_CALENDAR_XLSX)
    calendar_source = str(TYPICAL_CALENDAR_XLSX)
else:
    typical_calendar = pd.read_csv(TYPICAL_CALENDAR_FALLBACK_CSV)
    calendar_source = str(TYPICAL_CALENDAR_FALLBACK_CSV)
    log_diag(
        "WARN",
        "calendario",
        "No existe calendarios_fenologicos_tipicos_web.xlsx; se usa fallback CSV generado.",
        path=calendar_source,
    )

research_md = ""
if CALENDAR_RESEARCH_MD.exists():
    research_md = CALENDAR_RESEARCH_MD.read_text(encoding="utf-8", errors="replace")
else:
    log_diag("WARN", "calendario_md", "No se encontró el Markdown de calendarios de investigación.", path=str(CALENDAR_RESEARCH_MD))

pixel_frames = []
for crop, path in PIXEL_FILES.items():
    if not path.exists():
        log_diag("WARN", "pixeles", "No se encontró CSV de píxeles.", crop=crop, path=str(path))
        continue
    df = pd.read_csv(path)
    df["cultivo"] = crop
    if "lon_ee" not in df.columns and "lon" in df.columns:
        df["lon_ee"] = ((df["lon"] + 180) % 360) - 180
    df["franja_latitudinal"] = df.get("lat_band", pd.Series([None] * len(df))).map(h5_band_to_label)
    missing_band = df["franja_latitudinal"].isna()
    df.loc[missing_band, "franja_latitudinal"] = df.loc[missing_band, "lat"].map(lat_to_band_label)
    pixel_frames.append(df)

pixels = pd.concat(pixel_frames, ignore_index=True) if pixel_frames else pd.DataFrame()

print("Tabla maestra:", master.shape)
print("Calendario típico:", typical_calendar.shape, "fuente:", calendar_source)
print("Píxeles:", pixels.shape)
print("Cultivos con umbral en tabla maestra:", sorted(master["cultivo_norm"].dropna().unique()))
print("Cultivos con píxeles:", sorted(pixels["cultivo"].dropna().unique()) if not pixels.empty else [])


# %% [markdown]
# ## 4. Preparación de combinaciones cultivo-fase-franja
#
# Para cada cultivo y fase se selecciona una fila fuente de la tabla maestra con:
#
# - variable crítica;
# - umbral;
# - operador de comparación;
# - fuente bibliográfica;
# - DOY inicio/fin.
#
# Después se cruza con las franjas latitudinales donde existen píxeles H5 para ese cultivo.
#
# En modo prueba, se conserva solo una combinación y máximo 5 píxeles.

# %%
TARGET_CROPS = ["maize", "rice", "wheat", "soybean"]
EXCLUDED_PHASES = {"fuera de temporada", "fin de temporada", "sin_clasificar"}


def select_master_phase_rows(master_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    usable = master_df[
        master_df["cultivo_norm"].isin(TARGET_CROPS)
        & master_df["fase_macro"].notna()
        & ~master_df["fase_macro"].isin(EXCLUDED_PHASES)
    ].copy()
    usable = usable[usable["variable_critica"].notna() & usable["umbral"].notna()]

    group_cols = ["cultivo_norm", "fase_macro", "fase_original", "fase_estandar", "phase_name"]
    for _, group in usable.groupby(group_cols, dropna=False):
        # Preferir filas completas con DOY y fuente.
        group = group.sort_values(
            by=["data_completeness", "phase_duration"],
            ascending=[False, False],
            na_position="last",
        )
        rows.append(group.iloc[0])
    return pd.DataFrame(rows).reset_index(drop=True) if rows else pd.DataFrame()


phase_rows = select_master_phase_rows(master)

if "soybean" not in set(phase_rows.get("cultivo_norm", [])):
    log_diag(
        "WARN",
        "soybean",
        "Hay píxeles de soybean, pero no se encontró tabla maestra con variable crítica y umbral para soybean.",
    )

combination_rows = []
for _, phase in phase_rows.iterrows():
    crop = phase["cultivo_norm"]
    crop_pixels = pixels[pixels["cultivo"] == crop].copy()
    if crop_pixels.empty:
        log_diag("WARN", "combinaciones", "No hay píxeles para cultivo.", crop=crop)
        continue
    for band_label, band_pixels in crop_pixels.groupby("franja_latitudinal", dropna=True):
        spec = infer_variable_spec(
            phase.get("variable_critica"),
            phase.get("umbral"),
            phase.get("tipo_estres"),
        )
        combination_rows.append(
            {
                "cultivo": crop,
                "fase_macro": phase.get("fase_macro"),
                "fase_original": phase.get("fase_original"),
                "fase_estandar": phase.get("fase_estandar"),
                "phase_name": phase.get("phase_name"),
                "franja_latitudinal": band_label,
                "phase_start_doy": int(phase.get("phase_start_doy")),
                "phase_end_doy": int(phase.get("phase_end_doy")),
                "variable_critica": phase.get("variable_critica"),
                "umbral_texto": phase.get("umbral"),
                "umbral": spec.threshold,
                "unidad": spec.unit,
                "operador": spec.operator,
                "variable_gee": spec.variable_gee,
                "reducer": spec.reducer,
                "source_band": spec.source_band,
                "fuente_umbral": phase.get("fuente"),
                "enlace": phase.get("enlace"),
                "observaciones": spec.observation,
                "n_pixeles_disponibles": len(band_pixels),
            }
        )

combinations = pd.DataFrame(combination_rows)

if not RUN_FULL and not combinations.empty:
    test_mask = (
        (combinations["cultivo"] == TEST_CROP)
        & (combinations["fase_macro"].str.contains(TEST_PHASE_MACRO_CONTAINS, case=False, na=False))
        & (combinations["franja_latitudinal"] == TEST_LAT_BAND_LABEL)
    )
    if test_mask.any():
        combinations_to_run = combinations[test_mask].head(1).copy()
    else:
        combinations_to_run = combinations.head(1).copy()
        log_diag("WARN", "modo_prueba", "No se encontró la combinación de prueba exacta; se usará la primera disponible.")
else:
    combinations_to_run = combinations.copy()

print("Combinaciones potenciales:", len(combinations))
print("Combinaciones a ejecutar:", len(combinations_to_run))
display_cols = [
    "cultivo",
    "fase_macro",
    "franja_latitudinal",
    "variable_gee",
    "umbral",
    "operador",
    "n_pixeles_disponibles",
]
print(combinations_to_run[display_cols].to_string(index=False) if len(combinations_to_run) else "Sin combinaciones.")


# %% [markdown]
# ## 5. Inicialización de Google Earth Engine
#
# El script intenta inicializar Earth Engine así:
#
# 1. Si existen variables de entorno de Service Account:
#    - `GOOGLE_CLOUD_PROJECT`
#    - `GEE_SERVICE_ACCOUNT_EMAIL`
#    - `GEE_SERVICE_ACCOUNT_PRIVATE_KEY`
#
#    usa credenciales de Service Account.
#
# 2. Si no existen, intenta `ee.Initialize()` con credenciales locales ya autenticadas.
#
# No llama `ee.Authenticate()` automáticamente para evitar una pausa opaca en ejecuciones
# reproducibles. Si no hay credenciales, lo reporta y se detiene antes de consultar ERA5-Land.

# %%
def initialize_earth_engine() -> bool:
    if ee is None:
        log_diag("ERROR", "earth_engine", "El paquete earthengine-api no está instalado en este entorno.")
        return False

    project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("EE_PROJECT")
    service_account = os.getenv("GEE_SERVICE_ACCOUNT_EMAIL")
    private_key = os.getenv("GEE_SERVICE_ACCOUNT_PRIVATE_KEY")

    try:
        if service_account and private_key:
            key_data = {
                "type": "service_account",
                "project_id": project,
                "client_email": service_account,
                "private_key": private_key.replace("\\n", "\n"),
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            credentials = ee.ServiceAccountCredentials(service_account, key_data=json.dumps(key_data))
            ee.Initialize(credentials, project=project)
            log_diag("INFO", "earth_engine", "Earth Engine inicializado con Service Account.", project=project)
        else:
            ee.Initialize(project=project)
            log_diag("INFO", "earth_engine", "Earth Engine inicializado con credenciales locales.", project=project)
        return True
    except Exception as exc:
        log_diag(
            "ERROR",
            "earth_engine",
            "No se pudo inicializar Earth Engine. Verifica credenciales locales o variables de entorno.",
            error=str(exc),
        )
        return False


EE_READY = initialize_earth_engine()


# %% [markdown]
# ## 6. Funciones de consulta ERA5-Land
#
# Para cada píxel se consulta un polígono de 0.5°:
#
# - latitud centro ± 0.25°
# - longitud centro ± 0.25°
# - longitud en convención Earth Engine: -180 a 180
#
# Variables calculadas:
#
# - `tmax_c = temperature_2m_max - 273.15`
# - `tmean_c = temperature_2m - 273.15`
# - `tmin_c = temperature_2m_min - 273.15`
# - `precip_mm = total_precipitation_sum * 1000`
# - `swvl1`, `swvl2`, `swvl3`
# - `rootzone_sm = swvl1*0.07 + swvl2*0.21 + swvl3*0.72`
#
# La agregación por fase se hace por año y por píxel; después se promedia entre
# píxeles de la combinación cultivo-fase-franja.

# %%
def lon_to_ee(lon: float) -> float:
    return ((float(lon) + 180) % 360) - 180


def doy_to_date(year: int, doy: int) -> date:
    return date(year, 1, 1) + timedelta(days=int(doy) - 1)


def phase_date_window(year: int, start_doy: int, end_doy: int) -> Tuple[str, str]:
    start = doy_to_date(year, start_doy)
    if start_doy <= end_doy:
        end = doy_to_date(year, end_doy)
    else:
        end = doy_to_date(year + 1, end_doy)
    # EE filterDate usa fin exclusivo; sumamos un día.
    return start.isoformat(), (end + timedelta(days=1)).isoformat()


def build_era5_image(image: Any) -> Any:
    tmax = image.select("temperature_2m_max").subtract(273.15).rename("tmax_c")
    tmean = image.select("temperature_2m").subtract(273.15).rename("tmean_c")
    tmin = image.select("temperature_2m_min").subtract(273.15).rename("tmin_c")
    precip = image.select("total_precipitation_sum").multiply(1000).rename("precip_mm")
    swvl1 = image.select("volumetric_soil_water_layer_1").rename("swvl1")
    swvl2 = image.select("volumetric_soil_water_layer_2").rename("swvl2")
    swvl3 = image.select("volumetric_soil_water_layer_3").rename("swvl3")
    rootzone = (
        swvl1.multiply(0.07)
        .add(swvl2.multiply(0.21))
        .add(swvl3.multiply(0.72))
        .rename("rootzone_sm")
    )
    return image.addBands([tmax, tmean, tmin, precip, swvl1, swvl2, swvl3, rootzone], overwrite=True)


def get_reducer(reducer_name: str) -> Any:
    if reducer_name == "sum":
        return ee.Reducer.sum()
    if reducer_name == "min":
        return ee.Reducer.min()
    if reducer_name == "max":
        return ee.Reducer.max()
    return ee.Reducer.mean()


def query_pixel_year_phase(
    *,
    lat: float,
    lon_ee: float,
    year: int,
    start_doy: int,
    end_doy: int,
    variable_gee: str,
    reducer_name: str,
    include_daily: bool = False,
) -> Dict[str, Any]:
    if not EE_READY or ee is None:
        raise RuntimeError("Earth Engine no está inicializado.")

    lon_center = lon_to_ee(lon_ee)
    geom = ee.Geometry.Rectangle(
        [lon_center - 0.25, float(lat) - 0.25, lon_center + 0.25, float(lat) + 0.25],
        proj="EPSG:4326",
        geodesic=False,
    )
    start_date, end_date = phase_date_window(year, start_doy, end_doy)
    collection = (
        ee.ImageCollection(ERA5_DATASET_ID)
        .filterDate(start_date, end_date)
        .map(build_era5_image)
        .select(variable_gee)
    )

    reducer = get_reducer(reducer_name)
    if reducer_name == "sum":
        phase_image = collection.sum()
    elif reducer_name == "min":
        phase_image = collection.min()
    elif reducer_name == "max":
        phase_image = collection.max()
    else:
        phase_image = collection.mean()

    reduced = phase_image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geom,
        scale=ERA5_NATIVE_PIXEL_SIZE_M,
        bestEffort=True,
        maxPixels=100000,
    ).getInfo()

    clean_daily = []
    if include_daily:
        daily_fc = collection.map(
            lambda img: ee.Feature(
                None,
                {
                    "date": img.date().format("YYYY-MM-dd"),
                    "value": img.reduceRegion(
                        reducer=ee.Reducer.mean(),
                        geometry=geom,
                        scale=ERA5_NATIVE_PIXEL_SIZE_M,
                        bestEffort=True,
                        maxPixels=100000,
                    ).get(variable_gee),
                },
            )
        )

        daily_values = daily_fc.getInfo().get("features", [])
        clean_daily = [
            {
                "date": item.get("properties", {}).get("date"),
                "value": item.get("properties", {}).get("value"),
            }
            for item in daily_values
            if item.get("properties", {}).get("value") is not None
        ]

    return {
        "year": year,
        "value_phase": reduced.get(variable_gee),
        "daily": clean_daily,
        "n_days": len(clean_daily),
        "start_date": start_date,
        "end_date_exclusive": end_date,
    }


# %% [markdown]
# ## 7. Ejecución del cálculo
#
# Esta celda produce tres tablas internas:
#
# - `summary_rows`: resumen de probabilidades por combinación.
# - `annual_rows`: serie anual 1981-2016 por combinación.
# - `critical_year_rows`: años donde se supera el umbral.
#
# En modo prueba se consulta una sola combinación y máximo 5 píxeles.

# %%
summary_rows: List[Dict[str, Any]] = []
annual_rows: List[Dict[str, Any]] = []
critical_year_rows: List[Dict[str, Any]] = []
daily_exceedance_rows: List[Dict[str, Any]] = []
threshold_source_rows: List[Dict[str, Any]] = []


def choose_pixels_for_combination(crop: str, band_label: str, max_pixels: Optional[int]) -> pd.DataFrame:
    subset = pixels[
        (pixels["cultivo"] == crop)
        & (pixels["franja_latitudinal"] == band_label)
    ].copy()
    subset = subset.sort_values(["lat", "lon_ee" if "lon_ee" in subset.columns else "lon"]).reset_index(drop=True)
    if max_pixels is not None:
        subset = subset.head(max_pixels)
    return subset


def run_combination(combo: pd.Series) -> None:
    crop = combo["cultivo"]
    band = combo["franja_latitudinal"]
    phase_macro = combo["fase_macro"]
    variable_gee = combo["variable_gee"]
    threshold = combo["umbral"]
    operator = combo["operador"]

    threshold_source_rows.append(
        {
            "cultivo": crop,
            "fase_macro": phase_macro,
            "fase_original": combo["fase_original"],
            "variable_critica": combo["variable_critica"],
            "umbral_texto": combo["umbral_texto"],
            "umbral_extraido": threshold,
            "unidad": combo["unidad"],
            "operador": operator,
            "fuente_umbral": combo["fuente_umbral"],
            "enlace": combo["enlace"],
            "observaciones": combo["observaciones"],
        }
    )

    if not variable_gee:
        log_diag("WARN", "variable", "Variable no disponible/mapeada en ERA5-Land; se omite cálculo.", crop=crop, fase=phase_macro, variable=combo["variable_critica"])
        return
    if threshold is None:
        log_diag("WARN", "umbral", "No se pudo extraer umbral numérico; se omite cálculo.", crop=crop, fase=phase_macro, umbral=combo["umbral_texto"])
        return
    if not EE_READY:
        log_diag("ERROR", "earth_engine", "Earth Engine no está listo; no se ejecutan consultas.")
        return

    max_pixels = None
    if RUN_FULL:
        max_pixels = FULL_MAX_PIXELS_PER_COMBINATION
    else:
        max_pixels = TEST_MAX_PIXELS

    combo_pixels = choose_pixels_for_combination(crop, band, max_pixels)
    if combo_pixels.empty:
        log_diag("WARN", "pixeles", "No hay píxeles para la combinación.", crop=crop, franja=band)
        return

    years = range(START_YEAR, END_YEAR + 1)
    by_year_values: Dict[int, List[float]] = {year: [] for year in years}
    by_year_daily_exceedances: Dict[int, List[bool]] = {year: [] for year in years}

    print("\nEjecutando combinación")
    print(combo[["cultivo", "fase_macro", "franja_latitudinal", "variable_gee", "umbral", "operador"]].to_string())
    print(f"Píxeles usados: {len(combo_pixels)} de {combo['n_pixeles_disponibles']}")

    for pixel_index, pixel in combo_pixels.iterrows():
        lat = float(pixel["lat"])
        lon_ee = float(pixel["lon_ee"])
        pixel_id = pixel.get("pixel_id_h5", pixel_index)
        for year in years:
            try:
                result = query_pixel_year_phase(
                    lat=lat,
                    lon_ee=lon_ee,
                    year=year,
                    start_doy=int(combo["phase_start_doy"]),
                    end_doy=int(combo["phase_end_doy"]),
                    variable_gee=variable_gee,
                    reducer_name=combo["reducer"],
                    include_daily=False,
                )
                value = result["value_phase"]
                if value is not None:
                    by_year_values[year].append(float(value))
            except Exception as exc:
                log_diag(
                    "ERROR",
                    "consulta_gee",
                    "Falló consulta para píxel-año; se continúa.",
                    crop=crop,
                    fase=phase_macro,
                    franja=band,
                    pixel_id=str(pixel_id),
                    year=year,
                    error=str(exc),
                )

    candidate_critical_years = []
    for year in years:
        values = by_year_values[year]
        if values:
            annual_value = float(np.nanmean(values))
            if compare_threshold(annual_value, threshold, operator):
                candidate_critical_years.append(year)

    if candidate_critical_years:
        print(f"Años críticos preliminares para zoom diario: {candidate_critical_years}")
    for pixel_index, pixel in combo_pixels.iterrows():
        lat = float(pixel["lat"])
        lon_ee = float(pixel["lon_ee"])
        pixel_id = pixel.get("pixel_id_h5", pixel_index)
        for year in candidate_critical_years:
            try:
                result = query_pixel_year_phase(
                    lat=lat,
                    lon_ee=lon_ee,
                    year=year,
                    start_doy=int(combo["phase_start_doy"]),
                    end_doy=int(combo["phase_end_doy"]),
                    variable_gee=variable_gee,
                    reducer_name=combo["reducer"],
                    include_daily=True,
                )
                for daily in result["daily"]:
                    flag = compare_threshold(daily["value"], threshold, operator)
                    daily_exceedance_rows.append(
                        {
                            "cultivo": crop,
                            "fase_macro": phase_macro,
                            "franja_latitudinal": band,
                            "pixel_id_h5": pixel_id,
                            "lat": lat,
                            "lon_ee": lon_ee,
                            "variable_critica": combo["variable_critica"],
                            "variable_gee": variable_gee,
                            "umbral": threshold,
                            "operador": operator,
                            "anio": year,
                            "fecha": daily["date"],
                            "valor_diario": daily["value"],
                            "supera_umbral_diario": flag,
                        }
                    )
                    if flag is not None:
                        by_year_daily_exceedances[year].append(bool(flag))
            except Exception as exc:
                log_diag(
                    "ERROR",
                    "consulta_gee_diaria",
                    "Falló consulta diaria para año crítico; se conserva resumen anual.",
                    crop=crop,
                    fase=phase_macro,
                    franja=band,
                    pixel_id=str(pixel_id),
                    year=year,
                    error=str(exc),
                )

    critical_years = []
    valid_years = 0
    exceed_years = 0

    for year in years:
        values = by_year_values[year]
        daily_flags = by_year_daily_exceedances[year]
        if not values:
            annual_value = None
            event = None
        else:
            annual_value = float(np.nanmean(values))
            event = compare_threshold(annual_value, threshold, operator)
            valid_years += 1
            if event:
                exceed_years += 1
                critical_years.append(year)

        annual_rows.append(
            {
                "cultivo": crop,
                "fase_macro": phase_macro,
                "fase_original": combo["fase_original"],
                "franja_latitudinal": band,
                "variable_critica": combo["variable_critica"],
                "variable_gee": variable_gee,
                "umbral": threshold,
                "unidad": combo["unidad"],
                "operador": operator,
                "anio": year,
                "valor_fase": annual_value,
                "supera_umbral": event,
                "n_pixeles_usados": len(combo_pixels),
                "n_pixeles_con_dato": len(values),
                "n_dias_superacion": int(sum(daily_flags)) if daily_flags else 0,
                "max_consecutive_exceedance_days": max_consecutive_true(daily_flags),
            }
        )

        if event:
            critical_year_rows.append(
                {
                    "cultivo": crop,
                    "fase_macro": phase_macro,
                    "fase_original": combo["fase_original"],
                    "franja_latitudinal": band,
                    "variable_critica": combo["variable_critica"],
                    "umbral": threshold,
                    "operador": operator,
                    "anio": year,
                    "valor_fase": annual_value,
                    "n_pixeles_usados": len(combo_pixels),
                }
            )

    probability = exceed_years / valid_years if valid_years else None
    summary_rows.append(
        {
            "cultivo": crop,
            "fase_macro": phase_macro,
            "fase_original": combo["fase_original"],
            "franja_latitudinal": band,
            "variable_critica": combo["variable_critica"],
            "umbral": threshold,
            "unidad": combo["unidad"],
            "operador": operator,
            "n_pixeles": len(combo_pixels),
            "n_pixeles_disponibles": combo["n_pixeles_disponibles"],
            "n_anios_total": valid_years,
            "n_anios_supera": exceed_years,
            "probabilidad_superacion": probability,
            "anios_criticos": ", ".join(map(str, critical_years)),
            "fuente_umbral": combo["fuente_umbral"],
            "observaciones": combo["observaciones"],
        }
    )


if combinations_to_run.empty:
    log_diag("ERROR", "combinaciones", "No hay combinaciones para ejecutar.")
elif not EE_READY:
    log_diag("ERROR", "earth_engine", "Se omite ejecución porque Earth Engine no inicializó.")
else:
    for _, combo_row in combinations_to_run.iterrows():
        run_combination(combo_row)

summary_df = pd.DataFrame(summary_rows)
annual_df = pd.DataFrame(annual_rows)
critical_years_df = pd.DataFrame(critical_year_rows)
daily_df = pd.DataFrame(daily_exceedance_rows)
diagnostics_df = pd.DataFrame(diagnostics)
threshold_sources_df = pd.DataFrame(threshold_source_rows)

print("Resumen:", summary_df.shape)
print("Series anuales:", annual_df.shape)
print("Años críticos:", critical_years_df.shape)
print("Diagnóstico:", diagnostics_df.shape)


# %% [markdown]
# ## 8. Resultados rápidos en pantalla
#
# Esta celda muestra una vista rápida para verificar si el cálculo tiene sentido.
# En JupyterLab, `display(...)` mostrará las tablas con formato.

# %%
try:
    display(summary_df.head(20))
    display(annual_df.head(20))
    display(diagnostics_df.tail(20))
except NameError:
    print(summary_df.head(20).to_string(index=False) if not summary_df.empty else "summary_df vacío")
    print(annual_df.head(20).to_string(index=False) if not annual_df.empty else "annual_df vacío")
    print(diagnostics_df.tail(20).to_string(index=False) if not diagnostics_df.empty else "diagnostics_df vacío")


# %% [markdown]
# ## 9. Exportación a Excel, JSON y HTML
#
# El Excel contiene como mínimo:
#
# - `resumen_probabilidades`
# - `series_anuales`
# - `anios_criticos`
# - `diagnostico_variables`
# - `fuentes_umbral`
#
# El JSON queda listo para alimentar una página web.
# El HTML incluye metodología, tablas y gráficos simples en SVG embebido.

# %%
def ensure_minimum_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    out = df.copy()
    for col in columns:
        if col not in out.columns:
            out[col] = pd.Series(dtype="object")
    return out[columns + [c for c in out.columns if c not in columns]]


SUMMARY_COLUMNS = [
    "cultivo",
    "fase_macro",
    "fase_original",
    "franja_latitudinal",
    "variable_critica",
    "umbral",
    "unidad",
    "operador",
    "n_pixeles",
    "n_anios_total",
    "n_anios_supera",
    "probabilidad_superacion",
    "anios_criticos",
    "fuente_umbral",
    "observaciones",
]

ANNUAL_COLUMNS = [
    "cultivo",
    "fase_macro",
    "franja_latitudinal",
    "variable_critica",
    "umbral",
    "anio",
    "valor_fase",
    "supera_umbral",
    "n_pixeles_usados",
]

summary_df = ensure_minimum_columns(summary_df, SUMMARY_COLUMNS)
annual_df = ensure_minimum_columns(annual_df, ANNUAL_COLUMNS)


def write_excel() -> None:
    CLIMA_PHASE_DIR.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="resumen_probabilidades", index=False)
        annual_df.to_excel(writer, sheet_name="series_anuales", index=False)
        critical_years_df.to_excel(writer, sheet_name="anios_criticos", index=False)
        diagnostics_df.to_excel(writer, sheet_name="diagnostico_variables", index=False)
        threshold_sources_df.to_excel(writer, sheet_name="fuentes_umbral", index=False)
        if not daily_df.empty:
            # Hoja opcional útil para auditoría, puede crecer si RUN_FULL=True.
            daily_df.head(50000).to_excel(writer, sheet_name="series_diarias_muestra", index=False)


def df_to_records(df: pd.DataFrame) -> List[Dict[str, Any]]:
    cleaned = df.replace({np.nan: None})
    return cleaned.to_dict(orient="records")


def write_json() -> None:
    payload = {
        "metadata": {
            "created_by": "phase_threshold_exceedance_by_latband.py",
            "period": {"start_year": START_YEAR, "end_year": END_YEAR},
            "run_full": RUN_FULL,
            "era5_dataset": ERA5_DATASET_ID,
            "era5_native_pixel_size_m": ERA5_NATIVE_PIXEL_SIZE_M,
            "calendar_source": calendar_source,
            "notes": [
                "Consulta ERA5-Land bajo demanda por pixel/fase/franja.",
                "No contiene descargas globales ni exportaciones masivas.",
                "El modo prueba limita la ejecución a una combinación y pocos píxeles.",
            ],
        },
        "resumen_probabilidades": df_to_records(summary_df),
        "series_anuales": df_to_records(annual_df),
        "anios_criticos": df_to_records(critical_years_df),
        "diagnostico_variables": df_to_records(diagnostics_df),
        "fuentes_umbral": df_to_records(threshold_sources_df),
    }
    OUTPUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def svg_bar_chart(df: pd.DataFrame, category_col: str, value_col: str, title: str, width: int = 900, height: int = 320) -> str:
    if df.empty or category_col not in df.columns or value_col not in df.columns:
        return "<p>No hay datos suficientes para graficar.</p>"
    plot_df = df[[category_col, value_col]].dropna().copy()
    if plot_df.empty:
        return "<p>No hay datos suficientes para graficar.</p>"
    plot_df[value_col] = pd.to_numeric(plot_df[value_col], errors="coerce")
    plot_df = plot_df.dropna()
    if plot_df.empty:
        return "<p>No hay datos numéricos para graficar.</p>"
    max_val = max(float(plot_df[value_col].max()), 1e-9)
    margin_left = 60
    margin_bottom = 55
    chart_w = width - margin_left - 20
    chart_h = height - 70 - margin_bottom
    bar_w = chart_w / max(len(plot_df), 1)
    bars = []
    labels = []
    for i, row in plot_df.reset_index(drop=True).iterrows():
        val = float(row[value_col])
        bar_h = (val / max_val) * chart_h
        x = margin_left + i * bar_w + 2
        y = 50 + chart_h - bar_h
        bars.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{max(bar_w - 4, 1):.1f}" height="{bar_h:.1f}" fill="#3b82f6" />')
        if len(plot_df) <= 40 or i % max(1, len(plot_df) // 20) == 0:
            labels.append(f'<text x="{x + bar_w/2:.1f}" y="{height - 25}" font-size="10" text-anchor="middle" transform="rotate(45 {x + bar_w/2:.1f},{height - 25})">{row[category_col]}</text>')
    return f"""
    <svg width="{width}" height="{height}" role="img" aria-label="{title}">
      <style>text {{ font-family: Arial, sans-serif; }}</style>
      <text x="20" y="26" font-size="18" font-weight="700">{title}</text>
      <line x1="{margin_left}" y1="50" x2="{margin_left}" y2="{50 + chart_h}" stroke="#334155" />
      <line x1="{margin_left}" y1="{50 + chart_h}" x2="{width - 20}" y2="{50 + chart_h}" stroke="#334155" />
      <text x="15" y="58" font-size="11">{max_val:.2f}</text>
      {''.join(bars)}
      {''.join(labels)}
    </svg>
    """


def write_html() -> None:
    methodology = f"""
    <h1>Probabilidad histórica de superación de umbrales climáticos por fase</h1>
    <p><strong>Periodo:</strong> {START_YEAR}-{END_YEAR}. <strong>Dataset climático:</strong> {ERA5_DATASET_ID}.</p>
    <p>ERA5-Land Daily Aggregated se consulta desde Google Earth Engine por píxel H5, cultivo, fase fenológica y franja latitudinal. No se descargan series globales ni se lanzan exportaciones masivas.</p>
    <p>Resolución nativa aproximada del producto: {ERA5_NATIVE_PIXEL_SIZE_M:,} m. Cada píxel agrícola se consulta como polígono de 0.5° usando lat/lon ±0.25°.</p>
    <p>Variables derivadas: temperaturas en °C desde Kelvin; precipitación en mm desde metros; humedad de zona radicular como <code>swvl1*0.07 + swvl2*0.21 + swvl3*0.72</code>.</p>
    <p><strong>Modo completo:</strong> {RUN_FULL}. <strong>Fuente calendario:</strong> {calendar_source}</p>
    """

    chart_summary = svg_bar_chart(
        summary_df.assign(combo=summary_df.get("cultivo", "").astype(str) + " | " + summary_df.get("fase_macro", "").astype(str) + " | " + summary_df.get("franja_latitudinal", "").astype(str)),
        "combo",
        "probabilidad_superacion",
        "Probabilidad de superación por combinación",
    )
    chart_annual = svg_bar_chart(annual_df, "anio", "valor_fase", "Serie anual de valor de fase")

    html = f"""
    <!doctype html>
    <html lang="es">
    <head>
      <meta charset="utf-8" />
      <title>Reporte de umbrales climáticos por fase</title>
      <style>
        body {{ font-family: Arial, sans-serif; color: #0f172a; margin: 32px; line-height: 1.5; }}
        h1, h2 {{ color: #111827; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin: 16px 0 32px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 6px 8px; vertical-align: top; }}
        th {{ background: #e2e8f0; text-align: left; }}
        code {{ background: #f1f5f9; padding: 2px 4px; border-radius: 4px; }}
        .note {{ background: #fff7ed; border-left: 4px solid #f97316; padding: 12px 16px; }}
      </style>
    </head>
    <body>
      {methodology}
      <div class="note">Revisar la hoja <strong>diagnostico_variables</strong> para variables no mapeadas, umbrales no numéricos o fallas de consulta.</div>
      <h2>Gráficos</h2>
      {chart_summary}
      {chart_annual}
      <h2>Resumen de probabilidades</h2>
      {summary_df.head(200).to_html(index=False, escape=False)}
      <h2>Series anuales</h2>
      {annual_df.head(500).to_html(index=False, escape=False)}
      <h2>Años críticos</h2>
      {critical_years_df.head(500).to_html(index=False, escape=False)}
      <h2>Diagnóstico</h2>
      {diagnostics_df.to_html(index=False, escape=False) if not diagnostics_df.empty else "<p>Sin advertencias registradas.</p>"}
      <h2>Fuentes de umbral</h2>
      {threshold_sources_df.head(200).to_html(index=False, escape=False)}
    </body>
    </html>
    """
    OUTPUT_HTML.write_text(textwrap.dedent(html), encoding="utf-8")


write_excel()
write_json()
write_html()

print("Archivos guardados:")
print(OUTPUT_XLSX)
print(OUTPUT_JSON)
print(OUTPUT_HTML)


# %% [markdown]
# ## 10. Cómo interpretar los resultados
#
# En `resumen_probabilidades`:
#
# - `n_anios_total`: años con datos válidos en 1981-2016.
# - `n_anios_supera`: años donde el valor agregado de fase supera el umbral.
# - `probabilidad_superacion`: `n_anios_supera / n_anios_total`.
# - `anios_criticos`: años que activaron el evento.
#
# En `series_anuales`:
#
# - `valor_fase`: valor agregado de la variable durante la ventana DOY de la fase.
# - `supera_umbral`: resultado de comparar `valor_fase` contra el umbral.
# - `n_dias_superacion`: número de días que superaron el umbral diario en los píxeles usados.
# - `max_consecutive_exceedance_days`: máximo de días consecutivos con superación diaria.
#
# En `diagnostico_variables`:
#
# - revisar variables que no existen directamente en ERA5-Land;
# - revisar umbrales que no pudieron extraerse como número;
# - revisar fallas por permisos, autenticación o disponibilidad del dataset.
#
# **Nota metodológica**
#
# Cuando una variable fisiológica no existe directamente en ERA5-Land, por ejemplo
# potencial hídrico del suelo/solución en MPa, este script no inventa una conversión.
# La deja como no calculada y documenta el motivo. Para usarla haría falta una
# pedotransferencia o una variable proxy validada.
