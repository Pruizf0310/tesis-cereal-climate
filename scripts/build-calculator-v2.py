"""Build compact calculator metadata from the spatial master matrix and audited rules."""
from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
MASTER = WORK / "outputs" / "final_master" / "tabla_maestra_fenologia_global_v1.csv"
RULES = WORK / "outputs" / "final_master" / "reglas_amenaza_v1.csv"
HAZARDS = ROOT / "web-v2" / "public" / "data" / "hazard_impact_v2.json"
TECHNICAL = ROOT / "web-v2" / "public" / "data" / "phenology_technical_v2.json"
OUT = ROOT / "web-v2" / "public" / "data"

_technical = json.loads(TECHNICAL.read_text(encoding="utf-8"))
PHASE_NAMES = {
    (crop["id"], phase["code"]): phase["name"]
    for crop in _technical["crops"]
    for band in crop["bands"][:1]
    for phase in band["phases"]
}

UNIT_EN = {"mm/día": "mm/day", "días": "days", "°C día": "°C daytime", "% de reducción": "% reduction"}


def source_link(value: str) -> str:
    if not value:
        return ""
    if value.startswith("http"):
        return value
    if value.startswith("10."):
        return f"https://doi.org/{value}"
    return value


def clean_threshold(value: str) -> str:
    return (value.replace("for 7.0 more than one week", "for more than 7 consecutive days")
                 .replace(" °C día", " °C daytime")
                 .replace(" mm/día", " mm/day")
                 .replace(" días", " days"))


def band_key(lat: float) -> str:
    upper = math.ceil(lat / 10) * 10
    if lat == upper:
        upper += 10
    return f"{upper}_{upper - 10}"


def circular_mean(values: list[int]) -> int:
    angles = [2 * math.pi * (v - 1) / 365 for v in values]
    angle = math.atan2(sum(math.sin(a) for a in angles), sum(math.cos(a) for a in angles))
    if angle < 0:
        angle += 2 * math.pi
    return max(1, min(365, round(angle * 365 / (2 * math.pi) + 1)))


def build_calendar() -> dict:
    grouped: dict[tuple[str, str, str, str, str], dict[str, list]] = defaultdict(
        lambda: {"start": [], "end": [], "duration": [], "name": [], "order": [], "lats": []}
    )
    with MASTER.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = (row["crop"], row["season"], row["water_system"], band_key(float(row["latitude"])), row["phase_code"])
            item = grouped[key]
            item["start"].append(int(float(row["phase_start_doy"])))
            item["end"].append(int(float(row["phase_end_doy"])))
            item["duration"].append(float(row["phase_duration_days"]))
            item["name"].append(row["phase_name"])
            item["order"].append(int(row["phase_order"]))
            item["lats"].append(float(row["latitude"]))

    crops: dict[str, dict] = {}
    for (crop, season, water, band, phase), item in grouped.items():
        crop_obj = crops.setdefault(crop, {"label": crop.title(), "seasons": {}})
        season_id = f"{season}__{water}"
        season_obj = crop_obj["seasons"].setdefault(
            season_id,
            {"label": season.replace("_", " ").title(), "season": season, "water_system": water,
             "water_label": "Irrigated" if water == "ir" else "Rainfed", "bands": {}},
        )
        upper, lower = (int(x) for x in band.split("_"))
        band_obj = season_obj["bands"].setdefault(
            band,
            {"latMin": min(upper, lower), "latMax": max(upper, lower), "latBand": band, "phases": {}, "calendarCount": 0},
        )
        start = circular_mean(item["start"])
        duration = max(1, round(sum(item["duration"]) / len(item["duration"])))
        end = ((start - 1 + duration - 1) % 365) + 1
        band_obj["phases"][phase] = {
            "phase_code": phase, "phase_label": PHASE_NAMES.get((crop, phase), item["name"][0]), "phase_order": item["order"][0],
            "start_doy": start, "end_doy": end, "crosses_year": end < start, "duration_days": duration,
        }
        band_obj["calendarCount"] = max(band_obj["calendarCount"], len(item["start"]))

    return {
        "version": "v2.2.0-2026-08-05", "source": "Spatial master matrix v2.2 derived from GGCMI Phase 3 endpoints",
        "warning": "Phase dates are coordinate-informed latitude-band averages; intermediate dates are operational estimates.",
        "crops": crops,
    }


CALCULABLE = {
    "RICE_HEAT_MEAN_33": ("tmean_c", "daily", 1, 1),
    "RICE_COLD_MEAN20": ("tmean_c", "daily", 1, 1),
    "RICE_COLD_MEAN17": ("tmean_c", "daily", 1, 1),
    "RICE_RAIN25": ("precip_mm", "daily", 1, 1),
    "RICE_HEAT_DAY37_2": ("tmax_c", "daily", 1, 1),
    "RICE_HEAT_NIGHT31_2": ("tmin_c", "daily", 1, 7),
    "RICE_RIPENING_HEAT_MEAN28": ("tmean_c", "daily", 1, 1),
    "MAIZE_HEAT_DAY37_9": ("tmax_c", "daily", 1, 1),
    "MAIZE_HEAT_NIGHT27_3": ("tmin_c", "daily", 1, 7),
    "MAIZE_HEAT_FILL39_4_41_5": ("tmax_c", "rolling_mean", 6, 1),
    "WHEAT_HEAT_DAY27_3": ("tmax_c", "daily", 1, 1),
    "WHEAT_HEAT_NIGHT19_6": ("tmin_c", "daily", 1, 7),
    "WHEAT_FROST_POSTHEADING_CANOPY_MINUS3_5": ("tmin_c", "daily", 1, 1),
    "SOY_SEASONAL_HEAT30": ("tmax_c", "daily", 1, 1),
}

PHASE_EXPANSION = {
    ("rice", "BBCH_40_69"): ["BBCH_40_59", "BBCH_60_69"],
    ("rice", "BBCH_40_79"): ["BBCH_40_59", "BBCH_60_69", "BBCH_70_79"],
    ("wheat", "Z00_29"): ["Z00_09", "Z10_29"],
}


def build_thresholds() -> dict:
    public = json.loads(HAZARDS.read_text(encoding="utf-8"))["rows"]
    public_by_rule = {}
    for row in public:
        if row["details"]["rule_id"] != "NO_VERIFIED_THRESHOLD":
            public_by_rule[row["details"]["rule_id"]] = row
    crop_phases: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    with RULES.open(encoding="utf-8-sig", newline="") as handle:
        for rule in csv.DictReader(handle):
            rid = rule["threat_rule_id"]
            display = public_by_rule.get(rid, {})
            threshold_text = clean_threshold(display.get("threshold", ""))
            config = CALCULABLE.get(rid)
            raw_phases = rule["applicable_phase"].split(";")
            phases = []
            for raw_phase in raw_phases:
                phases.extend(PHASE_EXPANSION.get((rule["crop"], raw_phase), ["ALL" if raw_phase == "Ciclo completo" else raw_phase]))
            for phase in phases:
                variable, aggregation, window, minimum = config if config else (None, "daily", 1, 1)
                crop_phases[rule["crop"]][phase].append({
                    "rule_id": rid, "phase": phase, "phase_label": display.get("derived_stage", phase),
                    "hazard": display.get("hazard", rule["hazard"]), "variable": variable,
                    "variable_label": threshold_text or rule["variable"],
                    "threshold": float(rule["threshold"]) if rule["threshold"] else None,
                    "threshold_text": threshold_text, "unit": UNIT_EN.get(rule["unit"], rule["unit"]), "operator": rule["operator"],
                    "aggregation": aggregation, "window_days": window, "min_days_event": minimum,
                    "calculation_status": "provisional" if config else "unavailable",
                    "evidence_type": display.get("details", {}).get("evidence_type", rule["evidence_type"]),
                    "stress_type": display.get("hazard", rule["hazard"]), "source": rule["source"], "link": source_link(rule["doi_or_uri"]),
                    "note": display.get("details", {}).get("limitations", rule["limitations"]),
                    "qualitative_impact": display.get("qualitative_impact", ""),
                    "quantitative_impact": display.get("quantitative_impact", ""),
                    "rule_status": rule["rule_status"],
                })
    return {"version": "v2.2.0-2026-08-05", "source": "Audited threat-rule catalogue v2.2", "crops": crop_phases}


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "calculator_calendar_v2.json").write_text(json.dumps(build_calendar(), ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "calculator_thresholds_v2.json").write_text(json.dumps(build_thresholds(), ensure_ascii=False, indent=2), encoding="utf-8")
    print("calculator_calendar_v2.json and calculator_thresholds_v2.json generated")
