import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import h5py


CSV_PATH = Path(r"C:\Users\paola\Tesis\03_Resultados\Fenologia\tabla_maestra_fenologia_amenazas_espacial_v2_csv.csv")
H5_PATH = Path(r"C:\Users\paola\Tesis\CORRELA_TODOS\rice_correlacion_vectorizada.h5")
OUT_PATH = Path("work/rice_source_inspection.json")


def detect_encoding_and_dialect(path: Path):
    raw = path.open("rb").read(131072)
    encoding = None
    for candidate in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            pass
    if encoding is None:
        raise RuntimeError("No se pudo detectar una codificacion compatible")
    dialect = csv.Sniffer().sniff(text, delimiters=",;\t|")
    return encoding, dialect.delimiter


def inspect_csv(path: Path):
    encoding, delimiter = detect_encoding_and_dialect(path)
    total = 0
    rice_rows = 0
    crop_counts = Counter()
    nulls = Counter()
    unique_samples = defaultdict(list)
    columns = []
    crop_columns = []
    with path.open("r", encoding=encoding, newline="") as fh:
        reader = csv.DictReader(fh, delimiter=delimiter)
        columns = reader.fieldnames or []
        crop_columns = [c for c in columns if any(k in c.lower() for k in ("crop", "cultivo"))]
        candidate_interest = [
            c for c in columns
            if any(k in c.lower() for k in (
                "crop", "cultivo", "lat", "lon", "phase", "fase", "hazard", "amenaza",
                "threshold", "umbral", "date", "fecha", "doy", "unit", "unidad", "duration",
                "duracion", "variable", "operator", "operador", "source", "fuente", "pixel", "id"
            ))
        ]
        for row in reader:
            total += 1
            crop_values = [str(row.get(c, "")).strip() for c in crop_columns]
            for val in crop_values:
                if val:
                    crop_counts[val] += 1
            is_rice = any(v.lower() in {"rice", "arroz"} or "rice" in v.lower() or "arroz" in v.lower() for v in crop_values)
            if is_rice:
                rice_rows += 1
                for c in columns:
                    val = row.get(c)
                    if val is None or not str(val).strip() or str(val).strip().lower() in {"na", "nan", "null", "none"}:
                        nulls[c] += 1
                for c in candidate_interest:
                    val = str(row.get(c, "")).strip()
                    if val and val not in unique_samples[c] and len(unique_samples[c]) < 8:
                        unique_samples[c].append(val)
            if total % 1_000_000 == 0:
                print(f"CSV rows scanned: {total:,}", flush=True)
    return {
        "path": str(path), "encoding": encoding, "delimiter": delimiter,
        "columns": columns, "total_rows": total, "crop_columns": crop_columns,
        "crop_counts": crop_counts.most_common(30), "rice_rows": rice_rows,
        "rice_null_counts": dict(nulls), "rice_value_samples": dict(unique_samples),
    }


def inspect_h5(path: Path):
    items = []
    with h5py.File(path, "r") as h5:
        root_attrs = {k: repr(v)[:1000] for k, v in h5.attrs.items()}
        def visitor(name, obj):
            rec = {"name": name, "kind": "group" if isinstance(obj, h5py.Group) else "dataset"}
            if isinstance(obj, h5py.Dataset):
                rec.update({"shape": list(obj.shape), "dtype": str(obj.dtype), "chunks": obj.chunks, "compression": obj.compression})
                lname = name.lower()
                if obj.size <= 100_000 and any(k in lname for k in ("lat", "lon", "pixel", "coord", "index", "id")):
                    try:
                        vals = obj[...]
                        rec["sample_first"] = vals.reshape(-1)[:10].tolist()
                        rec["sample_last"] = vals.reshape(-1)[-10:].tolist()
                    except Exception as exc:
                        rec["sample_error"] = repr(exc)
            items.append(rec)
        h5.visititems(visitor)
    return {"path": str(path), "root_attrs": root_attrs, "items": items}


def main():
    result = {"csv": inspect_csv(CSV_PATH), "h5": inspect_h5(H5_PATH)}
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(result, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
