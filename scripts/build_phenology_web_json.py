from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
SOURCE_XLSX = REPO / "outputs" / "calendarios_fenologicos_tipicos_web.xlsx"
OUT_JSON = REPO / "web-v2" / "public" / "data" / "phenology_typical.json"
GENERATOR = REPO / "scripts" / "calendarios_tipicos_final.py"

MONTHS = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]

PHASES = ["F1", "F2", "F3"]
CROP_LABELS = {
    "maiz": ("maize", "Maize"),
    "arroz": ("rice", "Rice"),
    "trigo": ("wheat", "Wheat"),
    "soya": ("soybean", "Soybean"),
}


def load_generator():
    spec = importlib.util.spec_from_file_location("calendarios_tipicos_final", GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import {GENERATOR}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fixed_band(lat: float):
    upper = math.ceil(lat / 10) * 10
    if lat == upper:
        upper += 10
    lower = upper - 10
    sort_key = -upper

    def part(value: int) -> str:
        if value == 0:
            return "0°"
        hemi = "N" if value > 0 else "S"
        return f"{abs(value)}°{hemi}"

    return {
        "id": f"{upper}_{lower}",
        "label": f"{part(upper)}–{part(lower)}",
        "latMin": lower,
        "latMax": upper,
        "sortKey": sort_key,
    }


def signature_to_phase_map(signature: str):
    values = [part.strip() for part in str(signature).split("|")]
    return {
        month: f"F{value}" if value in {"1", "2", "3"} else ""
        for month, value in zip(MONTHS, values)
    }


def phase_duration_stats(df: pd.DataFrame):
    return {
        phase: {
            "mean": round(float(df[f"dur_{phase.lower()}"].mean()), 1),
            "std": round(float(df[f"dur_{phase.lower()}"].std(ddof=0)), 1),
        }
        for phase in PHASES
    }


def pattern_payload(signature: str, df: pd.DataFrame, total: int):
    stats = phase_duration_stats(df)
    return {
        "signature": signature,
        "latMin": round(float(df["lat"].min()), 2),
        "latMax": round(float(df["lat"].max()), 2),
        "regions": int(len(df)),
        "coveragePct": round((len(df) / total) * 100, 1) if total else 0,
        "countries": ", ".join(sorted(set(df["pais"].dropna().astype(str)))[:8]),
        "examples": "; ".join((df["pais"].astype(str) + " | " + df["region"].astype(str)).head(6)),
        "phaseDurations": {phase: stats[phase]["mean"] for phase in PHASES},
        "phaseDurationStd": {phase: stats[phase]["std"] for phase in PHASES},
        "phases": signature_to_phase_map(signature),
    }


def build_payload(region_df: pd.DataFrame):
    payload = {
        "phaseLegend": {
            "F1": "Establishment / planting",
            "F2": "Vegetative and reproductive growth",
            "F3": "Maturation and harvest",
        },
        "months": MONTHS,
        "crops": [],
    }

    for source_crop, (crop_id, label) in CROP_LABELS.items():
        crop_rows = region_df[region_df["cultivo"].eq(source_crop)].copy()
        crop_payload = {"id": crop_id, "label": label, "sourceCrop": source_crop, "seasons": []}
        if crop_rows.empty:
            payload["crops"].append(crop_payload)
            continue

        for season, season_df in crop_rows.groupby("temporada", dropna=False):
            total = len(season_df)
            season_payload = {"id": str(season), "label": f"Temporada {season}", "bands": []}
            season_df = season_df.copy()
            season_df["band"] = season_df["lat"].map(fixed_band)
            season_df["band_id"] = season_df["band"].map(lambda x: x["id"])

            band_items = []
            for band_id, band_df in season_df.groupby("band_id", dropna=False):
                band_meta = band_df.iloc[0]["band"]
                pattern_groups = []
                for signature, sig_df in band_df.groupby("firma", dropna=False):
                    pattern_groups.append((len(sig_df), float(sig_df["lat"].max()), signature, sig_df.copy()))
                pattern_groups.sort(key=lambda x: (-x[0], -x[1], x[2]))
                dominant_signature = pattern_groups[0][2]
                dominant_df = pattern_groups[0][3]
                internal = [
                    pattern_payload(signature, sig_df, len(band_df))
                    for _, _, signature, sig_df in pattern_groups
                ]
                dominant = pattern_payload(dominant_signature, dominant_df, total)
                dominant.update(
                    {
                        "id": band_meta["id"],
                        "latBand": band_meta["label"],
                        "latMin": band_meta["latMin"],
                        "latMax": band_meta["latMax"],
                        "sortKey": band_meta["sortKey"],
                        "regions": int(len(band_df)),
                        "dominantRegions": int(len(dominant_df)),
                        "coveragePct": round((len(band_df) / total) * 100, 1) if total else 0,
                        "matchPct": round((len(dominant_df) / len(band_df)) * 100, 1),
                        "internalPatterns": internal,
                    }
                )
                band_items.append(dominant)

            band_items.sort(key=lambda x: x["sortKey"])
            season_payload["bands"] = band_items
            crop_payload["seasons"].append(season_payload)

        payload["crops"].append(crop_payload)

    return payload


def main():
    generator = load_generator()
    source_df = pd.read_excel(generator.INPUT, sheet_name="tabla_maestra", dtype=object)
    dictionary_df = generator.build_dictionary(source_df)
    region_df, _ = generator.build_region_calendars(source_df, dictionary_df)
    payload = build_payload(region_df)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(OUT_JSON)
    print([(crop["id"], [(season["id"], len(season["bands"])) for season in crop["seasons"]]) for crop in payload["crops"]])


if __name__ == "__main__":
    main()
