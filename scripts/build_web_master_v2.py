import calendar
import csv
import json
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CAL = ROOT / "outputs" / "master_matrix" / "calendar_master_staging.csv"
PHASES = ROOT / "outputs" / "final_master" / "catalogo_fases_v1.csv"
RULES = ROOT / "outputs" / "final_master" / "reglas_amenaza_v1.csv"
WEB = ROOT / "tesis-cereal-climate" / "web-v2" / "public" / "data"

MONTHS = [calendar.month_abbr[i] for i in range(1, 13)]
MONTH_LENGTHS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
MONTH_BOUNDS = []
cursor = 1
for days in MONTH_LENGTHS:
    MONTH_BOUNDS.append((cursor, cursor + days - 1))
    cursor += days

CROP_LABELS = {"rice": "Rice", "maize": "Maize", "soybean": "Soybean", "wheat": "Wheat"}
SEASON_LABELS = {
    "maize": "Main maize season", "soybean": "Main soybean season",
    "rice_1": "Rice season 1", "rice_2": "Rice season 2",
    "spring_wheat": "Spring wheat", "winter_wheat": "Winter wheat",
}
PHASE_EN = {
    "BBCH_00_09": "Germination and emergence", "BBCH_10_19": "Seedling and early leaves",
    "BBCH_20_29": "Tillering", "BBCH_30_39": "Stem elongation and panicle initiation",
    "BBCH_40_59": "Booting and panicle emergence", "BBCH_60_69": "Flowering / anthesis",
    "BBCH_70_79": "Grain development and filling", "BBCH_80_99": "Ripening",
    "VE": "Germination and emergence", "V1_V6": "Early vegetative development",
    "V7_VT": "Late vegetative growth and tasseling", "R1": "Silking, pollination and seed set",
    "R2": "Blister stage", "maize:R3": "Milk stage", "R4_R5": "Dough to dent stage", "R6": "Physiological maturity",
    "VE_VC": "Emergence and cotyledons", "V1_VN": "Vegetative node development",
    "R1_R2": "Flowering", "soybean:R3": "Early pod formation", "R4": "Full pod",
    "R5": "Seed filling", "R6_R7": "Full seed to beginning maturity", "R8": "Full maturity",
    "Z00_09": "Germination and emergence", "Z10_29": "Leaf development and tillering",
    "Z30_39": "Stem elongation", "Z40_49": "Booting", "Z50_59": "Heading",
    "Z60_69": "Flowering / anthesis", "Z70_89": "Grain development and filling", "Z90_99": "Ripening",
}

def month_overlap(start_offset, end_offset):
    out = [0] * 12
    for absolute in range(start_offset, end_offset + 1):
        doy = absolute % 365 + 1
        for idx, (a, b) in enumerate(MONTH_BOUNDS):
            if a <= doy <= b:
                out[idx] += 1
                break
    return out

with PHASES.open(encoding="utf-8-sig", newline="") as f:
    phase_rows = list(csv.DictReader(f))
phase_by_crop = defaultdict(list)
for p in phase_rows:
    p["phase_order"] = int(p["phase_order"])
    p["fraction_start"] = float(p["fraction_start"])
    p["fraction_end"] = float(p["fraction_end"])
    p["phase_name_en"] = PHASE_EN.get(f"{p['crop']}:{p['phase_code']}", PHASE_EN[p["phase_code"]] if p["phase_code"] in PHASE_EN else p["phase_name"])
    phase_by_crop[p["crop"]].append(p)

agg_days = defaultdict(lambda: [0] * 12)
agg_duration = defaultdict(float)
calendars = defaultdict(set)

with CAL.open(encoding="utf-8-sig", newline="") as f:
    for row in csv.DictReader(f):
        crop = row["crop"]
        lat = float(row["lat"])
        band_min = math.floor(lat / 10) * 10
        band_max = band_min + 10
        band = f"{band_min:+d} to {band_max:+d}°"
        n = int(row["season_length_days"]) + 1
        planting0 = int(row["planting_doy"]) - 1
        group = (crop, row["season"], row["water_system"], band_min, band_max, band)
        calendars[group].add(row["calendar_id"])
        for p in phase_by_crop[crop]:
            start = round(n * p["fraction_start"])
            end = round(n * p["fraction_end"]) - 1
            if end < start:
                end = start
            key = group + (p["phase_code"],)
            overlaps = month_overlap(planting0 + start, planting0 + end)
            agg_days[key] = [a + b for a, b in zip(agg_days[key], overlaps)]
            agg_duration[key] += end - start + 1

crops_out = []
for crop in ("maize", "rice", "soybean", "wheat"):
    seasons_out = []
    groups = sorted([g for g in calendars if g[0] == crop], key=lambda g: (g[1], g[2], -g[4]))
    for group in groups:
        _, season, water, band_min, band_max, band = group
        count = len(calendars[group])
        phase_out = []
        for p in sorted(phase_by_crop[crop], key=lambda x: x["phase_order"]):
            key = group + (p["phase_code"],)
            days = agg_days[key]
            phase_out.append({
                "code": p["phase_code"], "name": p["phase_name_en"], "order": p["phase_order"],
                "average_duration_days": round(agg_duration[key] / count, 1),
                "average_days_by_month": [round(v / count, 1) for v in days],
            })
        seasons_out.append({
            "id": f"{season}_{water}_{band_min}_{band_max}", "season": season,
            "season_label": SEASON_LABELS.get(season, season.replace('_', ' ').title()),
            "water_system": water, "water_label": "Irrigated" if water == "ir" else "Rainfed",
            "latitude_band": band, "latitude_min": band_min, "latitude_max": band_max,
            "calendar_count": count, "phases": phase_out,
        })
    crops_out.append({"id": crop, "label": CROP_LABELS[crop], "bands": seasons_out})

calendar_payload = {
    "version": "v2.1.0-2026-08-05", "months": MONTHS,
    "source": "GGCMI Phase 3 planting and maturity endpoints; technical phases reconstructed from crop-specific normalized physiological templates",
    "warning": "Intermediate phase dates are operational estimates, not field observations.",
    "crops": crops_out,
}
(WEB / "phenology_technical_v2.json").write_text(json.dumps(calendar_payload, ensure_ascii=False, indent=2), encoding="utf-8")

with RULES.open(encoding="utf-8-sig", newline="") as f:
    rules = {r["threat_rule_id"]: r for r in csv.DictReader(f)}

RULE_PHASES = {
    "RICE_HEAT_MEAN_33": ["BBCH_30_39"], "RICE_DROUGHT_SM75": ["BBCH_40_59"],
    "RICE_COLD_MEAN20": ["BBCH_40_59", "BBCH_60_69"], "RICE_COLD_MEAN17": ["BBCH_70_79"],
    "RICE_RAIN25": ["BBCH_40_59", "BBCH_60_69", "BBCH_70_79"],
    "RICE_HEAT_DAY37_2": ["BBCH_60_69"], "RICE_HEAT_NIGHT31_2": ["BBCH_60_69"],
    "MAIZE_HEAT_DAY37_9": ["R1"], "MAIZE_HEAT_NIGHT27_3": ["R1"], "MAIZE_HEAT_FILL39_4_41_5": ["R4_R5"],
    "WHEAT_HEAT_DAY27_3": ["Z60_69"], "WHEAT_HEAT_NIGHT19_6": ["Z60_69"], "WHEAT_SEEDLING_HEAT42": ["Z00_09", "Z10_29"],
    "SOY_SEASONAL_HEAT30": ["VE_VC", "V1_VN", "R1_R2", "R3", "R4", "R5", "R6_R7", "R8"],
    "SOY_GERMINATION_TMAX46_92": ["VE_VC"],
}

IMPACTS = {
    "RICE_HEAT_MEAN_33": ("Heat-risk indicator during panicle initiation; the rule does not isolate a universal biological effect size.", "Not determined", "Regional indicator"),
    "RICE_DROUGHT_SM75": ("Sustained soil-moisture deficit can constrain reproductive development and seasonal rice performance.", "Not determined", "Regional indicator"),
    "RICE_COLD_MEAN20": ("Cold exposure around booting or flowering can impair reproductive development and seed set.", "Not determined", "Regional indicator"),
    "RICE_COLD_MEAN17": ("Cold exposure during grain filling can slow development and impair grain formation.", "Not determined", "Regional indicator"),
    "RICE_RAIN25": ("Heavy rainfall can disrupt panicle emergence or flowering and, during filling, reduce radiation and increase lodging or disease pressure.", "Not determined", "Regional indicator"),
    "RICE_HEAT_DAY37_2": ("Seed set is significantly reduced above the modeled daytime flowering threshold.", "Effect size varies among experiments", "Modeled threshold"),
    "RICE_HEAT_NIGHT31_2": ("Night heat during flowering is associated with significantly reduced seed set.", "Effect size varies among experiments", "Modeled threshold — provisional duration"),
    "MAIZE_HEAT_DAY37_9": ("Seed set is significantly reduced above the modeled daytime flowering threshold.", "Effect size varies among experiments", "Modeled threshold"),
    "MAIZE_HEAT_NIGHT27_3": ("Night heat around silking and pollination is associated with reduced seed set.", "Effect size varies among experiments", "Modeled threshold — provisional duration"),
    "MAIZE_HEAT_FILL39_4_41_5": ("Short-term heat during effective grain filling reduces photosynthesis, grain weight and yield.", "Yield −11.6% to −17.6%; 100-grain weight −5.1% to −10.1%", "Damaging experimental treatment"),
    "WHEAT_HEAT_DAY27_3": ("Seed set is significantly reduced above the modeled daytime anthesis threshold.", "Effect size varies among experiments", "Modeled threshold"),
    "WHEAT_HEAT_NIGHT19_6": ("Night heat during anthesis is associated with significantly reduced seed set.", "Effect size varies among experiments", "Modeled threshold — provisional duration"),
    "WHEAT_SEEDLING_HEAT42": ("The treatment elicited seedling heat and oxidative-stress responses; it is not an onset threshold.", "Not determined", "Secondary-source treatment"),
    "SOY_SEASONAL_HEAT30": ("Daily heat above 30 °C is associated with yield loss, particularly in rainfed US systems.", "Up to 6% yield loss per additional day above 30 °C", "Seasonal observational association"),
    "SOY_GERMINATION_TMAX46_92": ("Upper modeled cardinal temperature for germination rate; not a death threshold or field-alert trigger.", "Not applicable", "Modeled cardinal parameter"),
}

HAZARD_EN = {
    "Calor": "Heat", "Calor diurno": "Daytime heat", "Calor nocturno": "Nighttime heat",
    "Sequía": "Drought", "Frío": "Cold", "Lluvia intensa": "Heavy rainfall",
    "Temperatura cardinal": "Cardinal temperature",
}
VARIABLE_EN = {
    "Temperatura media diaria": "Daily mean temperature", "Humedad relativa del suelo": "Relative soil moisture",
    "Precipitación total diaria": "Daily total precipitation", "Temperatura diurna": "Daytime temperature",
    "Temperatura nocturna": "Nighttime temperature", "Tmax media del tratamiento": "Mean treatment Tmax",
    "Temperatura de tratamiento": "Treatment temperature", "Exposición diaria >30°C": "Daily exposure above 30 °C",
    "Temperatura máxima cardinal": "Maximum cardinal temperature",
}
DURATION_EN = {
    "día consecutivo": "consecutive day", "días consecutivos": "consecutive days",
    "más de una semana": "more than one week", "días, 08:00-18:00": "days, 08:00–18:00",
    "horas": "hours", "día": "day", "No determinada": "Not determined", "No aplica": "Not applicable",
}
EVIDENCE_EN = {
    "Indicador regional": "Regional indicator", "Umbral modelado": "Modeled threshold",
    "Umbral modelado provisional": "Provisional modeled threshold", "Tratamiento experimental": "Experimental treatment",
    "Fuente secundaria": "Secondary source", "Asociación observacional/modelos": "Observational/model association",
    "Parámetro modelado": "Modeled parameter",
}
SCOPE_EN = {
    "Sur de China; ciclo único": "Southern China; single rice",
    "Sur de China; arroz tardío": "Southern China; late rice",
    "Síntesis multiexperimento": "Multi-experiment synthesis",
    "Síntesis; evidencia nocturna limitada": "Synthesis; limited nighttime evidence",
    "Híbrido Xianyu335; China": "Xianyu335 hybrid; China",
    "Ambiente controlado": "Controlled environment",
    "Estados Unidos; más fuerte en secano": "United States; stronger under rainfed conditions",
    "Dos cultivares MG V; incubador": "Two maturity-group V cultivars; incubator",
}
LIMITATIONS_EN = {
    "RICE_HEAT_MEAN_33": "Duration was relaxed relative to the original standard; not a global threshold.",
    "RICE_DROUGHT_SM75": "The operational soil-moisture definition must be matched before transfer.",
    "RICE_COLD_MEAN20": "Relaxed duration and regional scope; not globally validated.",
    "RICE_COLD_MEAN17": "Relaxed duration and regional scope; not globally validated.",
    "RICE_RAIN25": "Based on a local Chengdu standard; rainfall is an exposure indicator, not a universal damage threshold.",
    "RICE_HEAT_DAY37_2": "SE 0.2 °C; significant seed-set reduction; exposure durations differ among experiments.",
    "RICE_HEAT_NIGHT31_2": "SE 0.2 °C; the reported duration is not a maximum tolerable duration.",
    "MAIZE_HEAT_DAY37_9": "SE 0.4 °C; modeled threshold for significant seed-set reduction.",
    "MAIZE_HEAT_NIGHT27_3": "SE 1.3 °C; the reported duration is not a maximum tolerable duration.",
    "MAIZE_HEAT_FILL39_4_41_5": "The 39.4–41.5 °C treatment caused damage but does not estimate damage onset.",
    "WHEAT_HEAT_DAY27_3": "SE 0.5 °C; modeled threshold for significant seed-set reduction.",
    "WHEAT_HEAT_NIGHT19_6": "SE 2.7 °C; the reported duration is not a maximum tolerable duration.",
    "WHEAT_SEEDLING_HEAT42": "Primary source still required; experimental treatment, not an alert threshold.",
    "SOY_SEASONAL_HEAT30": "Seasonal US association, not a phase-specific universal threshold.",
    "SOY_GERMINATION_TMAX46_92": "Do not use as a mortality threshold or automatic field alert.",
}

hazard_rows = []
for crop in ("maize", "rice", "soybean", "wheat"):
    assigned = defaultdict(list)
    for rid, phases in RULE_PHASES.items():
        if rules[rid]["crop"] == crop:
            for phase in phases:
                assigned[phase].append(rid)
    for p in sorted(phase_by_crop[crop], key=lambda x: x["phase_order"]):
        ids = assigned[p["phase_code"]]
        if not ids:
            hazard_rows.append({
                "crop": crop, "phase_code": p["phase_code"], "derived_stage": p["phase_name_en"],
                "hazard": "No verified quantitative hazard rule", "threshold": "Not available in the audited literature set",
                "qualitative_impact": "Evidence gap — no effect is inferred.", "quantitative_impact": "Not determined",
                "category": "Evidence gap", "details": {"phase_order": p["phase_order"], "rule_id": "NO_VERIFIED_THRESHOLD",
                "evidence_type": "No verified phase-specific rule", "spatial_scope": "Not applicable", "source": "Audited local bibliography",
                "link": "", "limitations": "Do not inherit a threshold from another phase."}
            })
            continue
        for rid in ids:
            r = rules[rid]
            qualitative, quantitative, category = IMPACTS[rid]
            duration = ""
            duration_label = DURATION_EN.get(r["duration_definition"], r["duration_definition"])
            if r["duration_value"]:
                duration = f" for {r['duration_value']} {duration_label}"
            elif r["duration_definition"] and r["duration_definition"] not in ("No determinada", "No aplica"):
                duration = f"; {duration_label}"
            threshold = f"{VARIABLE_EN.get(r['variable'], r['variable'])} {r['operator']} {r['threshold']} {r['unit']}{duration}"
            hazard_rows.append({
                "crop": crop, "phase_code": p["phase_code"], "derived_stage": p["phase_name_en"],
                "hazard": HAZARD_EN.get(r["hazard"], r["hazard"]), "threshold": threshold, "qualitative_impact": qualitative,
                "quantitative_impact": quantitative, "category": category,
                "details": {"phase_order": p["phase_order"], "rule_id": rid, "evidence_type": EVIDENCE_EN.get(r["evidence_type"], r["evidence_type"]),
                "spatial_scope": SCOPE_EN.get(r["spatial_scope"], r["spatial_scope"]), "source": r["source"], "link": r["doi_or_uri"], "limitations": LIMITATIONS_EN[rid]}
            })

(WEB / "hazard_impact_v2.json").write_text(json.dumps({
    "version": "v2.1.0-2026-08-05", "source": "Spatial master matrix v2 and audited threat-rule catalogue",
    "interpretation": "Rows are candidate rules assigned by crop and technical phase. They do not prove local occurrence.",
    "rows": hazard_rows,
}, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({
    "calendar_crop_count": len(crops_out), "calendar_band_groups": sum(len(c["bands"]) for c in crops_out),
    "hazard_rows": len(hazard_rows), "hazard_rows_by_crop": {c: sum(r["crop"] == c for r in hazard_rows) for c in CROP_LABELS},
}, indent=2))
