from __future__ import annotations

import argparse
import csv
import json
from itertools import zip_longest
from pathlib import Path

from inspect_geoglam_shapefile import (
    component_paths,
    count_records_from_shx,
    dbf_encoding,
    iter_dbf_records,
    iter_shp_polygon_records,
    parse_dbf_header,
    parse_shp_header,
    parse_xml_summary,
    read_text_if_exists,
    resolve_base_path,
    summarize_dbf,
)
from thesis_paths import thesis_path


FENOLOGIA_COLUMNS = [
    "culti",
    "temporada",
    "lat",
    "lon",
    "planting",
    "vegetative",
    "harvest",
    "endofseason",
    "duration_vegetative",
    "duration_hasta_cosecha",
    "duration_total",
    "outofseason",
    "minimalpro",
]

DATA_COLUMNS = [
    "record_id",
    *FENOLOGIA_COLUMNS,
    "num_fases",
    "fases_disponibles",
    "country",
    "region",
    "crop_original",
]

PHASE_COLUMNS = [
    "record_id",
    "phase_id",
    "phase_order",
    "phase_code",
    "phase_name",
    "phase_start_label",
    "phase_end_label",
    "phase_start_doy",
    "phase_end_doy",
    "phase_duration",
    "wraps_year",
    "culti",
    "temporada",
    "lat",
    "lon",
    "country",
    "region",
    "crop_original",
]

PHASE_SUMMARY_COLUMNS = [
    "phase_order",
    "phase_code",
    "phase_name",
    "start_marker",
    "end_marker",
    "records_with_phase",
    "records_without_phase",
    "percent_with_phase",
]

PHASE_DEFINITIONS = [
    {
        "phase_order": 1,
        "phase_code": "phase_1_planting_to_vegetative",
        "phase_name": "Siembra a vegetativa temprana",
        "start_field": "planting",
        "end_field": "vegetative",
        "start_label": "planting",
        "end_label": "vegetative - 1",
    },
    {
        "phase_order": 2,
        "phase_code": "phase_2_vegetative_to_reproductive",
        "phase_name": "Vegetativa a reproductiva",
        "start_field": "vegetative",
        "end_field": "harvest",
        "start_label": "vegetative",
        "end_label": "harvest - 1",
    },
    {
        "phase_order": 3,
        "phase_code": "phase_3_ripening_to_harvest",
        "phase_name": "Maduracion a cosecha",
        "start_field": "harvest",
        "end_field": "endofseason",
        "start_label": "harvest",
        "end_label": "endofseason - 1",
    },
    {
        "phase_order": 4,
        "phase_code": "phase_4_end_of_season",
        "phase_name": "Fin de temporada",
        "start_field": "endofseason",
        "end_field": "outofseason",
        "start_label": "endofseason",
        "end_label": "outofseason - 1",
    },
    {
        "phase_order": 5,
        "phase_code": "phase_5_out_of_season",
        "phase_name": "Fuera de temporada",
        "start_field": "outofseason",
        "end_field": "planting",
        "start_label": "outofseason",
        "end_label": "planting - 1",
    },
]


def split_crop_season(crop_value: object) -> tuple[str, str]:
    if crop_value is None:
        return "", ""

    crop_text = str(crop_value).strip()
    if not crop_text:
        return "", ""

    special_cases = {
        "Spring Wheat": ("wheat", "spring"),
        "Winter Wheat": ("wheat", "winter"),
    }
    if crop_text in special_cases:
        return special_cases[crop_text]

    parts = crop_text.split()
    if len(parts) >= 2 and parts[-1].isdigit():
        return " ".join(parts[:-1]).lower(), parts[-1]

    return crop_text.lower(), ""


def as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    return 0


def cycle_duration(start_day: object, end_day: object) -> int:
    start = as_int(start_day)
    end = as_int(end_day)
    if start <= 0 or end <= 0:
        return 0

    delta = end - start
    if delta < 0:
        delta += 365
    return delta


def previous_doy(day: object) -> int:
    value = as_int(day)
    if value <= 0:
        return 0
    return 365 if value == 1 else value - 1


def wraps_year(start_day: object, end_day: object) -> int:
    start = as_int(start_day)
    end = as_int(end_day)
    if start <= 0 or end <= 0:
        return 0
    return 1 if end <= start else 0


def rounded_coord(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 8)


def build_phase_rows_for_record(base_row: dict[str, object]) -> list[dict[str, object]]:
    phase_rows: list[dict[str, object]] = []

    for phase in PHASE_DEFINITIONS:
        start_doy = as_int(base_row.get(phase["start_field"]))
        next_phase_start = as_int(base_row.get(phase["end_field"]))
        duration = cycle_duration(start_doy, next_phase_start)
        if start_doy <= 0 or next_phase_start <= 0 or duration <= 0:
            continue

        phase_id = f"{base_row['record_id']}_{phase['phase_order']}"
        phase_rows.append(
            {
                "record_id": base_row["record_id"],
                "phase_id": phase_id,
                "phase_order": phase["phase_order"],
                "phase_code": phase["phase_code"],
                "phase_name": phase["phase_name"],
                "phase_start_label": phase["start_label"],
                "phase_end_label": phase["end_label"],
                "phase_start_doy": start_doy,
                "phase_end_doy": previous_doy(next_phase_start),
                "phase_duration": duration,
                "wraps_year": wraps_year(start_doy, next_phase_start),
                "culti": base_row["culti"],
                "temporada": base_row["temporada"],
                "lat": base_row["lat"],
                "lon": base_row["lon"],
                "country": base_row["country"],
                "region": base_row["region"],
                "crop_original": base_row["crop_original"],
            }
        )

    return phase_rows


def build_enriched_rows(base_path: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    components = component_paths(base_path)
    dbf_path = components[".dbf"]
    shp_path = components[".shp"]
    cpg_path = components[".cpg"]

    dbf_info = parse_dbf_header(dbf_path)
    encoding = dbf_encoding(cpg_path)

    rows: list[dict[str, object]] = []
    phase_rows: list[dict[str, object]] = []
    dbf_iter = iter_dbf_records(dbf_path, dbf_info, encoding)
    shp_iter = iter_shp_polygon_records(shp_path)

    for record_idx, (dbf_row, geometry) in enumerate(zip_longest(dbf_iter, shp_iter), start=1):
        if dbf_row is None or geometry is None:
            raise ValueError("El número de registros de atributos y geometrías no coincide.")

        culti, temporada = split_crop_season(dbf_row.get("crop"))
        planting = as_int(dbf_row.get("planting"))
        vegetative = as_int(dbf_row.get("vegetative"))
        harvest = as_int(dbf_row.get("harvest"))
        endofseason = as_int(dbf_row.get("endofseaso"))
        outofseason = as_int(dbf_row.get("outofseaso"))
        minimalpro = as_int(dbf_row.get("minimalpro"))

        base_row = {
            "record_id": record_idx,
            "culti": culti,
            "temporada": temporada,
            "lat": rounded_coord(geometry.centroid_y),
            "lon": rounded_coord(geometry.centroid_x),
            "planting": planting,
            "vegetative": vegetative,
            "harvest": harvest,
            "endofseason": endofseason,
            "duration_vegetative": cycle_duration(planting, vegetative),
            "duration_hasta_cosecha": cycle_duration(planting, harvest),
            "duration_total": cycle_duration(planting, endofseason),
            "outofseason": outofseason,
            "minimalpro": minimalpro,
            "country": dbf_row.get("country") or "",
            "region": dbf_row.get("region") or "",
            "crop_original": dbf_row.get("crop") or "",
        }

        record_phase_rows = build_phase_rows_for_record(base_row)
        base_row["num_fases"] = len(record_phase_rows)
        base_row["fases_disponibles"] = " | ".join(
            phase_row["phase_name"] for phase_row in record_phase_rows
        )

        rows.append(base_row)
        phase_rows.extend(record_phase_rows)

    return rows, phase_rows


def build_phase_summary_rows(
    data_rows: list[dict[str, object]],
    phase_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    total_records = len(data_rows)
    counts_by_code: dict[str, int] = {}
    for phase_row in phase_rows:
        phase_code = str(phase_row["phase_code"])
        counts_by_code[phase_code] = counts_by_code.get(phase_code, 0) + 1

    summary_rows: list[dict[str, object]] = []
    for phase in PHASE_DEFINITIONS:
        with_phase = counts_by_code.get(phase["phase_code"], 0)
        without_phase = total_records - with_phase
        percent = round((with_phase / total_records) * 100, 2) if total_records else 0.0
        summary_rows.append(
            {
                "phase_order": phase["phase_order"],
                "phase_code": phase["phase_code"],
                "phase_name": phase["phase_name"],
                "start_marker": phase["start_field"],
                "end_marker": phase["end_field"],
                "records_with_phase": with_phase,
                "records_without_phase": without_phase,
                "percent_with_phase": percent,
            }
        )

    return summary_rows


def build_metadata(
    base_path: Path,
    data_rows: list[dict[str, object]],
    phase_rows: list[dict[str, object]],
    phase_summary_rows: list[dict[str, object]],
) -> dict[str, object]:
    components = component_paths(base_path)

    shp_path = components[".shp"]
    shx_path = components[".shx"]
    dbf_path = components[".dbf"]
    prj_path = components[".prj"]
    cpg_path = components[".cpg"]
    xml_path = components[".xml"]

    shp_info = parse_shp_header(shp_path)
    dbf_info = parse_dbf_header(dbf_path)
    encoding = dbf_encoding(cpg_path)
    dbf_summary = summarize_dbf(dbf_path, dbf_info, encoding)

    txt_files = sorted(base_path.parent.glob("*.txt"))
    txt_previews = {}
    for txt_path in txt_files:
        text = read_text_if_exists(txt_path)
        if text:
            txt_previews[txt_path.name] = text.splitlines()

    metadata: dict[str, object] = {
        "base_path": str(base_path),
        "directory": str(base_path.parent),
        "components": [
            {
                "extension": ext,
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
            for ext, path in components.items()
        ],
        "spatial": {
            "shape_type": shp_info["shape_name"],
            "shape_type_code": shp_info["shape_type"],
            "bbox": shp_info["bbox"],
            "shp_size_bytes": shp_info["file_length_bytes"],
            "records_from_shx": count_records_from_shx(shx_path),
            "crs_wkt": read_text_if_exists(prj_path) or "",
            "location_representation": "Centroides derivados de poligonos del shapefile",
            "coordinate_order": "lat = y, lon = x",
        },
        "dbf": {
            "encoding": encoding,
            "updated_on": dbf_info.updated_on,
            "num_records": dbf_info.num_records,
            "header_length": dbf_info.header_length,
            "record_length": dbf_info.record_length,
            "fields": [
                {
                    "name": field.name,
                    "type": field.field_type,
                    "length": field.length,
                    "decimals": field.decimals,
                }
                for field in dbf_info.fields
            ],
        },
        "thematic": {
            "valid_records": dbf_summary["valid_records"],
            "distinct_countries": len(dbf_summary["countries"]),
            "distinct_country_regions": len(dbf_summary["country_region_pairs"]),
            "distinct_crops": len(dbf_summary["crops"]),
            "crop_values": sorted(dbf_summary["crops"]),
            "minimalpro_counts": {
                str(key): value
                for key, value in sorted(
                    dbf_summary["minimalproduction"].items(), key=lambda item: str(item[0])
                )
            },
            "nonzero_stage_counts": dict(dbf_summary["nonzero_counters"]),
        },
        "phases": {
            "definitions": PHASE_DEFINITIONS,
            "records_with_any_phase": sum(1 for row in data_rows if int(row["num_fases"]) > 0),
            "phase_row_count": len(phase_rows),
        },
        "export": {
            "data_columns": DATA_COLUMNS,
            "fenologia_columns": FENOLOGIA_COLUMNS,
            "fenologia_rows": [[row[column] for column in FENOLOGIA_COLUMNS] for row in data_rows],
            "phase_columns": PHASE_COLUMNS,
            "phase_rows": [[row[column] for column in PHASE_COLUMNS] for row in phase_rows],
            "phase_summary_columns": PHASE_SUMMARY_COLUMNS,
            "phase_summary_rows": [
                [row[column] for column in PHASE_SUMMARY_COLUMNS] for row in phase_summary_rows
            ],
            "preview_rows": [[row[column] for column in DATA_COLUMNS] for row in data_rows[:10]],
        },
        "xml": parse_xml_summary(xml_path) if xml_path.exists() else {},
        "readme_files": txt_previews,
    }
    return metadata


def export_csv(csv_path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara CSV y metadata JSON para exportar un shapefile a Excel."
    )
    parser.add_argument(
        "path",
        help="Ruta al .shp, a cualquier archivo del conjunto o al directorio que lo contiene.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(thesis_path("processed", "geoglam_cm4ew_calendars")),
        help="Directorio donde se guardaran el CSV y el JSON.",
    )
    args = parser.parse_args()

    base_path = resolve_base_path(args.path)
    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    data_rows, phase_rows = build_enriched_rows(base_path)
    phase_summary_rows = build_phase_summary_rows(data_rows, phase_rows)
    metadata = build_metadata(base_path, data_rows, phase_rows, phase_summary_rows)

    data_csv_path = output_dir / "geoglam_data.csv"
    phases_csv_path = output_dir / "geoglam_fases.csv"
    phase_summary_csv_path = output_dir / "geoglam_resumen_fases.csv"
    json_path = output_dir / "geoglam_metadata.json"

    export_csv(data_csv_path, DATA_COLUMNS, data_rows)
    export_csv(phases_csv_path, PHASE_COLUMNS, phase_rows)
    export_csv(phase_summary_csv_path, PHASE_SUMMARY_COLUMNS, phase_summary_rows)
    json_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(data_csv_path)
    print(phases_csv_path)
    print(phase_summary_csv_path)
    print(json_path)


if __name__ == "__main__":
    main()
