import csv
import json
import math
import sys
from collections import Counter
from pathlib import Path

import h5py


MASTER = Path(r"C:\Users\paola\Tesis\03_Resultados\Fenologia\tabla_maestra_fenologia_amenazas_espacial_v2_csv.csv")
H5 = Path(r"C:\Users\paola\Tesis\CORRELA_TODOS\rice_correlacion_vectorizada.h5")
OUT_DIR = Path(r"C:\Users\paola\Tesis\03_Resultados\Hazard")


def wrap180(lon):
    return ((lon + 180.0) % 360.0) - 180.0


def key(lat, lon):
    return (round(float(lat), 6), round(wrap180(float(lon)), 6))


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    master_by_coord = {}
    counts = Counter()
    with MASTER.open("r", encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        for row_number, row in enumerate(reader, start=2):
            if row["crop"].strip().lower() != "rice":
                continue
            coord_key = key(row["latitude"], row["longitude"])
            counts[coord_key] += 1
            if coord_key not in master_by_coord:
                master_by_coord[coord_key] = {
                    "master_table_row_id": row["coordinate_id"],
                    "master_first_csv_row": row_number,
                    "master_lat": float(row["latitude"]),
                    "master_lon": float(row["longitude"]),
                }

    with h5py.File(H5, "r") as h5:
        lat_idx = h5["lat_idx"][...]
        lon_idx = h5["lon_idx"][...]

    rows = []
    matched_master = set()
    for idx, (ilat, ilon) in enumerate(zip(lat_idx, lon_idx)):
        # The GDHY/H5 grid uses 0.5-degree cell centers. Longitude is stored 0..360.
        h5_lat = -89.75 + 0.5 * int(ilat)
        h5_lon_0360 = 0.25 + 0.5 * int(ilon)
        h5_lon = wrap180(h5_lon_0360)
        coord_key = key(h5_lat, h5_lon)
        master = master_by_coord.get(coord_key)
        if master:
            matched_master.add(coord_key)
            distance = math.hypot(master["master_lat"] - h5_lat, wrap180(master["master_lon"] - h5_lon))
            quality = "EXACT" if distance < 1e-9 else "NEAR"
            method = "exact_0.5deg_grid_center"
        else:
            distance = ""
            quality = "UNMATCHED"
            method = "no_exact_match"
            master = {"master_table_row_id": "", "master_first_csv_row": "", "master_lat": "", "master_lon": ""}
        rows.append({
            "pixel_id": f"rice_{idx}",
            "rice_h5_pixel_index": idx,
            "master_table_row_id": master["master_table_row_id"],
            "master_first_csv_row": master["master_first_csv_row"],
            "master_lat": master["master_lat"],
            "master_lon": master["master_lon"],
            "h5_lat_idx": int(ilat),
            "h5_lon_idx": int(ilon),
            "h5_lat": h5_lat,
            "h5_lon": h5_lon,
            "h5_lon_0_360": h5_lon_0360,
            "gee_query_lat": h5_lat,
            "gee_query_lon": h5_lon,
            "match_distance_degrees": distance,
            "match_method": method,
            "match_quality": quality,
            "master_rows_for_coordinate": counts.get(coord_key, 0),
        })

    out_csv = OUT_DIR / "rice_pixel_crosswalk.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "master_unique_rice_coordinates": len(master_by_coord),
        "h5_pixels": len(rows),
        "h5_pixels_matched": sum(r["match_quality"] != "UNMATCHED" for r in rows),
        "h5_pixels_unmatched": sum(r["match_quality"] == "UNMATCHED" for r in rows),
        "master_coordinates_matched": len(matched_master),
        "master_coordinates_not_in_h5": len(set(master_by_coord) - matched_master),
        "match_method": "Exact equality after reconstructing 0.5-degree GDHY centers from H5 indices and wrapping longitude to [-180, 180).",
        "crosswalk_path": str(out_csv),
    }
    (OUT_DIR / "rice_crosswalk_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
