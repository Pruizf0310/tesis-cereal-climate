"""Build lightweight rice agroclimatic web assets.

This script processes the local HDF5 correlation cube once and exports:
  - web-v2/public/data/rice_map.geojson
  - web-v2/public/data/rice_detail.json

The frontend must not read the H5 directly.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import h5py
import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_H5_PATH = Path(r"C:\Users\paola\Tesis\CORRELA_TODOS\rice_correlacion_vectorizada.h5")
DEFAULT_OUT_DIR = REPO_ROOT / "web-v2" / "public" / "data"

ONI_NPY_PATH = Path(r"C:\Users\paola\Tesis\CORRELA_TODOS\oni_monthly_1982_2016.npy")
MJO_PHASE_NPY_PATH = Path(r"C:\Users\paola\Tesis\CORRELA_TODOS\mjo_phase_monthly.npy")
MJO_AMP_NPY_PATH = Path(r"C:\Users\paola\Tesis\CORRELA_TODOS\mjo_amp_monthly.npy")

ONI_YIELD_CSV = Path(
    r"C:\Users\paola\Tesis\CORRELA_TODOS\rice_trigger_analysis\oni_yield_pixel_year_merged.csv"
)
FENOLOGY_CSV = Path(
    r"C:\Users\paola\Tesis\CORRELA_TODOS\rice_fenologia_join_full\rice_pixels_with_union_critical_months_FULL.csv"
)
RMM_TEXT_PATH = Path(r"C:\Users\paola\Tesis\01_Data\RMM\romi.cpcolr.1x-RMM.txt")

SST_SHAPE = (360, 720)
RICE_GRID_RES = 0.5
SST_GRID_RES = 0.5

REGION_BOXES = {
    "nino34": (-5, 5, 190, 240),
    "nino4": (-5, 5, 160, 210),
    "indian_w": (-10, 10, 50, 80),
    "maritime": (-10, 10, 95, 150),
    "pacific_w": (-10, 10, 150, 180),
    "pacific_c": (-10, 10, 180, 220),
}

REGION_SUPPRESSION_PHASES = {
    "indian_w": {1, 8},
    "maritime": {2, 3},
    "pacific_w": {4, 5},
    "pacific_c": {5, 6, 7},
    "nino4": {6, 7},
    "nino34": {7, 8},
}


def wrap_lon(lon: float) -> float:
    return ((lon + 180.0) % 360.0) - 180.0


def grid_lat_from_idx(idx: int, res: float = RICE_GRID_RES) -> float:
    return round((idx + 0.5) * res - 90.0, 4)


def grid_lon_from_idx(idx: int, res: float = RICE_GRID_RES) -> float:
    return round((idx + 0.5) * res, 4)


def pixel_id(lat: float, lon: float) -> str:
    return f"{lat:.2f}_{wrap_lon(lon):.2f}"


def month_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    out: list[int] = []
    for part in str(raw).replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            m = int(part)
            if 1 <= m <= 12:
                out.append(m)
    return sorted(set(out))


def phenology_by_lat(lat: float) -> dict[str, list[int]]:
    if lat > 25:
        return {"planting": [5, 6], "flowering": [7, 8], "grain_filling": [8, 9]}
    if lat < -15:
        return {"planting": [11, 12], "flowering": [1, 2], "grain_filling": [2, 3]}
    return {"planting": [3, 4], "flowering": [5, 6], "grain_filling": [6, 7]}


def sensitive_phase(peak_month: int, calendar: dict[str, list[int]]) -> str:
    if peak_month in calendar["flowering"]:
        return "flowering"
    if peak_month in calendar["grain_filling"]:
        return "grain_filling"
    if peak_month in calendar["planting"]:
        return "planting"
    return "vegetative"


def short_phase(phase: str) -> str:
    return {"flowering": "flo", "grain_filling": "gf", "planting": "pla"}.get(phase, "veg")


def confidence_level(oni_r: float, coherent: bool, risk_phase_count: int, has_mjo: bool) -> str:
    score = 0
    if abs(oni_r) >= 0.35:
        score += 2
    elif abs(oni_r) >= 0.2:
        score += 1
    if coherent:
        score += 1
    if 1 <= risk_phase_count <= 3:
        score += 1
    if not has_mjo:
        score -= 1
    if score >= 3:
        return "high"
    if score >= 1:
        return "moderate"
    return "low"


def confidence_code(confidence: str) -> str:
    return {"high": "h", "moderate": "m", "low": "l"}[confidence]


def safe_float(value: Any, digits: int = 4) -> float | None:
    try:
        x = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(x):
        return None
    return round(x, digits)


def corrcoef(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 3:
        return float("nan")
    return float(np.corrcoef(x[mask], y[mask])[0, 1])


def build_sst_vectors() -> tuple[np.ndarray, np.ndarray]:
    lat = (np.arange(SST_SHAPE[0]) + 0.5) * SST_GRID_RES - 90.0
    lon = (np.arange(SST_SHAPE[1]) + 0.5) * SST_GRID_RES
    lat2, lon2 = np.meshgrid(lat, lon, indexing="ij")
    return lat2.reshape(-1), lon2.reshape(-1)


def region_masks() -> dict[str, np.ndarray]:
    sst_lat, sst_lon = build_sst_vectors()
    masks: dict[str, np.ndarray] = {}
    for name, (lat_min, lat_max, lon_min, lon_max) in REGION_BOXES.items():
        masks[name] = np.where(
            (sst_lat >= lat_min) & (sst_lat <= lat_max) & (sst_lon >= lon_min) & (sst_lon <= lon_max)
        )[0]
    return masks


def load_fenology(path: Path) -> dict[int, list[int]]:
    if not path.exists():
        print(f"[warn] Fenology CSV not found: {path}. Falling back to latitude-based calendar.")
        return {}
    out: dict[int, list[int]] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                pid = int(row["pixel_id"])
            except (KeyError, TypeError, ValueError):
                continue
            out[pid] = month_list(row.get("critical_months_union"))
    return out


def load_oni_yield(path: Path) -> dict[int, list[tuple[int, float, float]]]:
    if not path.exists():
        print(f"[warn] ONI/yield CSV not found: {path}. ENSO bins will use empty values.")
        return {}
    out: dict[int, list[tuple[int, float, float]]] = defaultdict(list)
    with path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            try:
                pid = int(row["pixel_id"])
                year = int(row["Year"])
                oni = float(row["oni_critical_top2"])
                y = float(row["yield_anomaly"])
            except (KeyError, TypeError, ValueError):
                continue
            out[pid].append((year, oni, y))
    return dict(out)


def load_monthly_mjo(phase_path: Path, amp_path: Path) -> tuple[np.ndarray | None, np.ndarray | None]:
    if phase_path.exists() and amp_path.exists():
        print(f"[info] Loading MJO arrays: {phase_path.name}, {amp_path.name}")
        return np.load(phase_path), np.load(amp_path)
    print(
        "[warn] MJO .npy files not found. Configure MJO_PHASE_NPY_PATH and MJO_AMP_NPY_PATH "
        "near the top of this script to enable real MJO phase diagnostics."
    )
    if RMM_TEXT_PATH.exists():
        print(f"[info] RMM daily text is available at {RMM_TEXT_PATH}, but this build expects monthly .npy arrays.")
    return None, None


def validate_oni_array(path: Path) -> np.ndarray | None:
    if path.exists():
        print(f"[info] Loading ONI array: {path}")
        return np.load(path)
    print(
        "[warn] oni_monthly_1982_2016.npy not found. The build will use "
        f"pixel-year ONI values from {ONI_YIELD_CSV}."
    )
    return None


def oni_bins(records: list[tuple[int, float, float]]) -> dict[str, float | None]:
    bins = {"sn": [], "n": [], "neu": [], "el": [], "sel": []}
    for _, oni, y in records:
        if oni <= -1.5:
            bins["sn"].append(y)
        elif oni <= -0.5:
            bins["n"].append(y)
        elif oni < 0.5:
            bins["neu"].append(y)
        elif oni < 1.5:
            bins["el"].append(y)
        else:
            bins["sel"].append(y)
    return {k: safe_float(np.mean(v), 4) if v else None for k, v in bins.items()}


def mjo_phase_yield(
    records: list[tuple[int, float, float]],
    peak_month: int,
    phase_monthly: np.ndarray | None,
    amp_monthly: np.ndarray | None,
) -> tuple[dict[str, float | None], list[int], int | None]:
    phase_yield: dict[str, list[float]] = {str(p): [] for p in range(1, 9)}
    if phase_monthly is not None and amp_monthly is not None:
        for year, _, y in records:
            year_idx = year - 1982
            month_idx = peak_month - 1
            try:
                phase = int(phase_monthly[year_idx, month_idx])
                amp = float(amp_monthly[year_idx, month_idx])
            except Exception:
                continue
            if 1 <= phase <= 8 and amp > 1.0:
                phase_yield[str(phase)].append(y)

    means = {p: safe_float(np.mean(vals), 4) if vals else None for p, vals in phase_yield.items()}
    valid = {int(p): v for p, v in means.items() if v is not None}
    if not valid:
        return means, [], None
    worst_phase = min(valid, key=lambda p: valid[p])
    threshold = float(np.nanpercentile(list(valid.values()), 35))
    risk_phases = sorted([p for p, value in valid.items() if value <= threshold])
    return means, risk_phases, worst_phase


def process(args: argparse.Namespace) -> None:
    if not args.h5.exists():
        raise FileNotFoundError(f"H5 file not found: {args.h5}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    map_path = args.out_dir / "rice_map.geojson"
    detail_path = args.out_dir / "rice_detail.json"

    masks = region_masks()
    validate_oni_array(args.oni_npy)
    fenology = load_fenology(args.fenology_csv)
    yield_by_pixel = load_oni_yield(args.oni_yield_csv)
    phase_monthly, amp_monthly = load_monthly_mjo(args.mjo_phase_npy, args.mjo_amp_npy)
    has_mjo = phase_monthly is not None and amp_monthly is not None

    features: list[dict[str, Any]] = []
    detail: dict[str, Any] = {}

    with h5py.File(args.h5, "r") as h5:
        corr_ds = h5["correlacion"]
        lat_idx = h5["lat_idx"][:]
        lon_idx = h5["lon_idx"][:]
        n_pixels = corr_ds.shape[0]
        print(f"[info] Processing {n_pixels:,} rice pixels from {args.h5}")

        for start in range(0, n_pixels, args.batch_size):
            stop = min(start + args.batch_size, n_pixels)
            cube = corr_ds[start:stop].astype(np.float32)
            month_strength = np.nanmean(np.abs(cube), axis=2)

            for local_i, pixel_cube in enumerate(cube):
                i = start + local_i
                lat = grid_lat_from_idx(int(lat_idx[i]))
                lon0360 = grid_lon_from_idx(int(lon_idx[i]))
                lon = wrap_lon(lon0360)
                pid = pixel_id(lat, lon)

                strengths = month_strength[local_i]
                peak_month = int(np.nanargmax(strengths) + 1) if np.isfinite(strengths).any() else 1
                records = yield_by_pixel.get(i, [])

                region_r: dict[str, float] = {}
                for region, idx in masks.items():
                    vals = np.nanmean(pixel_cube[:, idx], axis=1)
                    region_r[region] = float(np.nanmean(vals)) if np.isfinite(vals).any() else 0.0

                olr_region = max(region_r, key=lambda r: abs(region_r[r]) if math.isfinite(region_r[r]) else -1)
                olr_r = region_r[olr_region]
                oni_r = region_r["nino34"]
                bins = oni_bins(records)
                y_sigma = safe_float(np.nanstd([r[2] for r in records]), 4) if records else None

                phase_calendar = phenology_by_lat(lat)
                critical_months = fenology.get(i) or phase_calendar["flowering"] + phase_calendar["grain_filling"]
                sp = sensitive_phase(peak_month, phase_calendar)

                mjo_yield, mjo_risk, mjo_worst = mjo_phase_yield(records, peak_month, phase_monthly, amp_monthly)
                expected = REGION_SUPPRESSION_PHASES.get(olr_region, set())
                coherent = bool(expected.intersection(mjo_risk)) if mjo_risk else False
                conf = confidence_level(oni_r, coherent, len(mjo_risk), has_mjo)

                dr = bins["el"]
                if dr is None:
                    dr = safe_float(oni_r, 4) or 0.0

                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "id": pid,
                            "dr": safe_float(dr, 4),
                            "conf": confidence_code(conf),
                            "sp": short_phase(sp),
                            "rph": critical_months[:4],
                            "olr": olr_region,
                            "mw": peak_month,
                        },
                    }
                )

                detail[pid] = {
                    "lat": lat,
                    "lon": lon,
                    "crop": "rice",
                    "oni_r": safe_float(oni_r, 4),
                    "oni_bins": bins,
                    "peak_month": peak_month,
                    "olr_region": olr_region,
                    "olr_r": safe_float(olr_r, 4),
                    "mjo_phase_yield": mjo_yield,
                    "mjo_risk_phases": mjo_risk,
                    "mjo_worst_phase": mjo_worst,
                    "mjo_olr_coherent": coherent,
                    "sensitive_phase": sp,
                    "critical_months": critical_months,
                    "yield_sigma": y_sigma,
                    "confidence": conf,
                }

            print(f"[info] processed {stop:,}/{n_pixels:,}")

    with map_path.open("w", encoding="utf-8") as fh:
        json.dump({"type": "FeatureCollection", "features": features}, fh, separators=(",", ":"))
    with detail_path.open("w", encoding="utf-8") as fh:
        json.dump(detail, fh, separators=(",", ":"))

    for path in (map_path, detail_path):
        raw = path.stat().st_size
        gz = len(gzip.compress(path.read_bytes(), compresslevel=9))
        print(f"[done] {path}: {raw / 1024:.1f} KB; gzip estimate {gz / 1024:.1f} KB")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h5", type=Path, default=DEFAULT_H5_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--oni-npy", type=Path, default=ONI_NPY_PATH)
    parser.add_argument("--mjo-phase-npy", type=Path, default=MJO_PHASE_NPY_PATH)
    parser.add_argument("--mjo-amp-npy", type=Path, default=MJO_AMP_NPY_PATH)
    parser.add_argument("--oni-yield-csv", type=Path, default=ONI_YIELD_CSV)
    parser.add_argument("--fenology-csv", type=Path, default=FENOLOGY_CSV)
    parser.add_argument("--batch-size", type=int, default=24)
    return parser.parse_args()


if __name__ == "__main__":
    process(parse_args())
