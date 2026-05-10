from __future__ import annotations

import argparse
import struct
import textwrap
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


COMPONENT_LABELS = {
    ".shp": "geometries",
    ".shx": "geometry index",
    ".dbf": "attribute table",
    ".prj": "coordinate reference system",
    ".cpg": "text encoding",
    ".xml": "metadata",
    ".sbn": "spatial index",
    ".sbx": "spatial index companion",
}

SHAPE_TYPES = {
    0: "Null Shape",
    1: "Point",
    3: "Polyline",
    5: "Polygon",
    8: "MultiPoint",
    11: "PointZ",
    13: "PolylineZ",
    15: "PolygonZ",
    18: "MultiPointZ",
    21: "PointM",
    23: "PolylineM",
    25: "PolygonM",
    28: "MultiPointM",
    31: "MultiPatch",
}


@dataclass
class DbfField:
    name: str
    field_type: str
    length: int
    decimals: int


@dataclass
class DbfInfo:
    version: int
    updated_on: str
    num_records: int
    header_length: int
    record_length: int
    fields: list[DbfField]


@dataclass
class GeometryRecord:
    record_number: int
    shape_type: int
    bbox: tuple[float, float, float, float] | None
    num_parts: int
    num_points: int
    centroid_x: float | None
    centroid_y: float | None


def resolve_base_path(user_path: str) -> Path:
    path = Path(user_path).expanduser()
    if path.is_dir():
        shp_files = sorted(path.glob("*.shp"))
        if len(shp_files) == 1:
            return Path(str(shp_files[0])[:-4])
        if not shp_files:
            raise FileNotFoundError(f"No encontré archivos .shp dentro de: {path}")
        raise ValueError(
            f"Encontré varios .shp en {path}. Pásame uno en específico para evitar ambigüedad."
        )

    suffix = path.suffix.lower()
    if suffix in COMPONENT_LABELS:
        return Path(str(path)[: -len(suffix)])
    return path


def component_paths(base_path: Path) -> dict[str, Path]:
    return {ext: Path(f"{base_path}{ext}") for ext in COMPONENT_LABELS}


def read_text_if_exists(path: Path, default_encoding: str = "utf-8") -> str | None:
    if not path.exists():
        return None

    encodings = [default_encoding, "utf-8-sig", "cp1252", "latin-1"]
    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def parse_shp_header(path: Path) -> dict[str, object]:
    with path.open("rb") as fh:
        header = fh.read(100)

    if len(header) < 100:
        raise ValueError(f"El archivo {path} no tiene un encabezado SHP válido.")

    file_code = struct.unpack(">i", header[0:4])[0]
    file_length_bytes = struct.unpack(">i", header[24:28])[0] * 2
    version = struct.unpack("<i", header[28:32])[0]
    shape_type = struct.unpack("<i", header[32:36])[0]
    xmin, ymin, xmax, ymax = struct.unpack("<4d", header[36:68])

    return {
        "file_code": file_code,
        "file_length_bytes": file_length_bytes,
        "version": version,
        "shape_type": shape_type,
        "shape_name": SHAPE_TYPES.get(shape_type, f"Unknown ({shape_type})"),
        "bbox": (xmin, ymin, xmax, ymax),
    }


def count_records_from_shx(path: Path) -> int | None:
    if not path.exists():
        return None
    size = path.stat().st_size
    if size < 100:
        return None
    return (size - 100) // 8


def _closed_ring(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    if not points:
        return points
    if points[0] == points[-1]:
        return points
    return [*points, points[0]]


def _ring_area_centroid(points: list[tuple[float, float]]) -> tuple[float, float, float] | None:
    ring = _closed_ring(points)
    if len(ring) < 4:
        return None

    doubled_area = 0.0
    centroid_x_num = 0.0
    centroid_y_num = 0.0

    for idx in range(len(ring) - 1):
        x1, y1 = ring[idx]
        x2, y2 = ring[idx + 1]
        cross = (x1 * y2) - (x2 * y1)
        doubled_area += cross
        centroid_x_num += (x1 + x2) * cross
        centroid_y_num += (y1 + y2) * cross

    if abs(doubled_area) < 1e-12:
        return None

    centroid_x = centroid_x_num / (3.0 * doubled_area)
    centroid_y = centroid_y_num / (3.0 * doubled_area)
    return doubled_area / 2.0, centroid_x, centroid_y


def polygon_centroid(parts: list[list[tuple[float, float]]]) -> tuple[float | None, float | None]:
    total_signed_area = 0.0
    centroid_x_num = 0.0
    centroid_y_num = 0.0
    all_points: list[tuple[float, float]] = []

    for points in parts:
        all_points.extend(points)
        ring_summary = _ring_area_centroid(points)
        if ring_summary is None:
            continue

        signed_area, centroid_x, centroid_y = ring_summary
        total_signed_area += signed_area
        centroid_x_num += centroid_x * signed_area
        centroid_y_num += centroid_y * signed_area

    if abs(total_signed_area) >= 1e-12:
        return centroid_x_num / total_signed_area, centroid_y_num / total_signed_area

    if all_points:
        xs = [point[0] for point in all_points]
        ys = [point[1] for point in all_points]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    return None, None


def iter_shp_polygon_records(path: Path) -> Iterator[GeometryRecord]:
    with path.open("rb") as fh:
        header = fh.read(100)
        if len(header) < 100:
            raise ValueError(f"El archivo {path} no tiene un encabezado SHP válido.")

        while True:
            record_header = fh.read(8)
            if not record_header:
                break
            if len(record_header) < 8:
                raise ValueError(f"Registro SHP incompleto en {path}.")

            record_number, content_length_words = struct.unpack(">2i", record_header)
            content = fh.read(content_length_words * 2)
            if len(content) < 4:
                break

            shape_type = struct.unpack("<i", content[0:4])[0]
            if shape_type == 0:
                yield GeometryRecord(
                    record_number=record_number,
                    shape_type=shape_type,
                    bbox=None,
                    num_parts=0,
                    num_points=0,
                    centroid_x=None,
                    centroid_y=None,
                )
                continue

            if shape_type not in {5, 15, 25}:
                raise NotImplementedError(
                    f"Solo implementé lectura de Polygon/PolygonZ/PolygonM y encontré shape type {shape_type}."
                )

            xmin, ymin, xmax, ymax = struct.unpack("<4d", content[4:36])
            num_parts = struct.unpack("<i", content[36:40])[0]
            num_points = struct.unpack("<i", content[40:44])[0]

            parts_index_start = 44
            parts_index_end = parts_index_start + (num_parts * 4)
            part_starts = list(struct.unpack(f"<{num_parts}i", content[parts_index_start:parts_index_end]))

            points_start = parts_index_end
            points_end = points_start + (num_points * 16)
            raw_points = struct.unpack(f"<{num_points * 2}d", content[points_start:points_end])
            points = list(zip(raw_points[0::2], raw_points[1::2]))

            parts: list[list[tuple[float, float]]] = []
            for idx, start in enumerate(part_starts):
                end = part_starts[idx + 1] if idx + 1 < num_parts else num_points
                parts.append(points[start:end])

            centroid_x, centroid_y = polygon_centroid(parts)
            yield GeometryRecord(
                record_number=record_number,
                shape_type=shape_type,
                bbox=(xmin, ymin, xmax, ymax),
                num_parts=num_parts,
                num_points=num_points,
                centroid_x=centroid_x,
                centroid_y=centroid_y,
            )


def parse_dbf_header(path: Path) -> DbfInfo:
    with path.open("rb") as fh:
        header = fh.read(32)
        if len(header) < 32:
            raise ValueError(f"El archivo {path} no tiene un encabezado DBF válido.")

        version = header[0]
        year = 1900 + header[1]
        month = header[2]
        day = header[3]
        num_records = struct.unpack("<I", header[4:8])[0]
        header_length = struct.unpack("<H", header[8:10])[0]
        record_length = struct.unpack("<H", header[10:12])[0]

        fields: list[DbfField] = []
        while True:
            descriptor = fh.read(32)
            if not descriptor or descriptor[0] == 0x0D:
                break

            name = descriptor[:11].split(b"\x00", 1)[0].decode("ascii", "ignore")
            field_type = chr(descriptor[11])
            length = descriptor[16]
            decimals = descriptor[17]
            fields.append(DbfField(name, field_type, length, decimals))

    return DbfInfo(
        version=version,
        updated_on=f"{year:04d}-{month:02d}-{day:02d}",
        num_records=num_records,
        header_length=header_length,
        record_length=record_length,
        fields=fields,
    )


def dbf_encoding(cpg_path: Path) -> str:
    text = read_text_if_exists(cpg_path)
    if not text:
        return "utf-8"
    return text.strip() or "utf-8"


def parse_dbf_value(raw: bytes, field: DbfField, encoding: str) -> object:
    text = raw.decode(encoding, errors="replace").strip()
    if not text:
        return None

    if field.field_type in {"N", "F"}:
        if field.decimals:
            try:
                return float(text)
            except ValueError:
                return text
        try:
            return int(text)
        except ValueError:
            try:
                return float(text)
            except ValueError:
                return text

    if field.field_type == "L":
        return text.upper() in {"Y", "T"}

    if field.field_type == "D" and len(text) == 8:
        return f"{text[:4]}-{text[4:6]}-{text[6:]}"

    return text


def iter_dbf_records(path: Path, info: DbfInfo, encoding: str) -> Iterator[dict[str, object]]:
    with path.open("rb") as fh:
        fh.seek(info.header_length)
        for _ in range(info.num_records):
            record = fh.read(info.record_length)
            if not record:
                break
            if record[0:1] == b"*":
                continue

            values: dict[str, object] = {}
            position = 1
            for field in info.fields:
                raw = record[position : position + field.length]
                values[field.name] = parse_dbf_value(raw, field, encoding)
                position += field.length
            yield values


def summarize_dbf(path: Path, info: DbfInfo, encoding: str) -> dict[str, object]:
    sample_rows: list[dict[str, object]] = []
    countries: set[str] = set()
    country_region_pairs: set[tuple[str, str]] = set()
    crops: set[str] = set()
    nonzero_counters: Counter[str] = Counter()
    minimalproduction: Counter[object] = Counter()
    valid_records = 0

    field_names = {field.name for field in info.fields}
    stage_columns = ["planting", "vegetative", "harvest", "endofseaso", "outofseaso"]

    for row in iter_dbf_records(path, info, encoding):
        valid_records += 1
        if len(sample_rows) < 5:
            sample_rows.append(row)

        country = row.get("country")
        region = row.get("region")
        crop = row.get("crop")

        if isinstance(country, str) and country:
            countries.add(country)
        if isinstance(country, str) and isinstance(region, str) and country and region:
            country_region_pairs.add((country, region))
        if isinstance(crop, str) and crop:
            crops.add(crop)

        if "minimalpro" in field_names:
            minimalproduction[row.get("minimalpro")] += 1

        for column in stage_columns:
            if column in field_names:
                value = row.get(column)
                if isinstance(value, (int, float)) and value != 0:
                    nonzero_counters[column] += 1

    return {
        "valid_records": valid_records,
        "sample_rows": sample_rows,
        "countries": countries,
        "country_region_pairs": country_region_pairs,
        "crops": crops,
        "nonzero_counters": nonzero_counters,
        "minimalproduction": minimalproduction,
    }


def parse_xml_summary(path: Path) -> dict[str, str]:
    tree = ET.parse(path)
    root = tree.getroot()

    def find_text(tag_name: str) -> str | None:
        for element in root.iter():
            if element.tag.split("}", 1)[-1] == tag_name and element.text:
                return element.text.strip()
        return None

    summary: dict[str, str] = {}
    create_date = find_text("CreaDate")
    create_time = find_text("CreaTime")
    if create_date:
        summary["xml_creation_date"] = create_date
    if create_time:
        summary["xml_creation_time"] = create_time
    return summary


def print_section(title: str) -> None:
    print(f"\n{title}")
    print("-" * len(title))


def format_row(row: dict[str, object]) -> str:
    parts = [f"{key}={value}" for key, value in row.items()]
    return ", ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspecciona un shapefile y sus archivos auxiliares sin depender de geopandas."
    )
    parser.add_argument(
        "path",
        help="Ruta al .shp, a cualquier archivo del conjunto o al directorio que lo contiene.",
    )
    args = parser.parse_args()

    base_path = resolve_base_path(args.path)
    components = component_paths(base_path)

    print_section("Conjunto detectado")
    print(f"Base: {base_path}")
    print(f"Directorio: {base_path.parent}")

    print_section("Archivos encontrados")
    for ext, label in COMPONENT_LABELS.items():
        path = components[ext]
        status = "OK" if path.exists() else "NO"
        print(f"{ext:>4}  {status:>2}  {label}  {path}")

    txt_files = sorted(base_path.parent.glob("*.txt"))
    if txt_files:
        print("\nTXT adicionales")
        for txt_path in txt_files:
            print(f"     {txt_path}")

    shp_path = components[".shp"]
    shx_path = components[".shx"]
    dbf_path = components[".dbf"]
    prj_path = components[".prj"]
    cpg_path = components[".cpg"]
    xml_path = components[".xml"]

    if shp_path.exists():
        shp_info = parse_shp_header(shp_path)
        print_section("Resumen espacial")
        print(f"Tipo de geometria: {shp_info['shape_name']}")
        print(f"Codigo shapefile: {shp_info['file_code']}")
        print(f"Version: {shp_info['version']}")
        print(f"BBox (xmin, ymin, xmax, ymax): {shp_info['bbox']}")
        print(f"Tamanio declarado en SHP: {shp_info['file_length_bytes']:,} bytes")
        print(f"Tamanio real del archivo: {shp_path.stat().st_size:,} bytes")

        shx_count = count_records_from_shx(shx_path)
        if shx_count is not None:
            print(f"Registros segun .shx: {shx_count:,}")

    encoding = dbf_encoding(cpg_path)
    if dbf_path.exists():
        dbf_info = parse_dbf_header(dbf_path)
        dbf_summary = summarize_dbf(dbf_path, dbf_info, encoding)

        print_section("Tabla de atributos")
        print(f"Version DBF: {dbf_info.version}")
        print(f"Actualizado: {dbf_info.updated_on}")
        print(f"Codificacion: {encoding}")
        print(f"Registros declarados: {dbf_info.num_records:,}")
        print(f"Registros validos leidos: {dbf_summary['valid_records']:,}")
        print(f"Longitud encabezado: {dbf_info.header_length} bytes")
        print(f"Longitud por registro: {dbf_info.record_length} bytes")

        print("\nCampos")
        for field in dbf_info.fields:
            print(
                f"  - {field.name} | tipo={field.field_type} | largo={field.length} | decimales={field.decimals}"
            )

        countries = dbf_summary["countries"]
        regions = dbf_summary["country_region_pairs"]
        crops = dbf_summary["crops"]
        print("\nResumen tematico")
        print(f"  - Paises distintos: {len(countries):,}")
        print(f"  - Regiones subnacionales distintas: {len(regions):,}")
        print(f"  - Tipos de cultivo/campania distintos: {len(crops):,}")
        if crops:
            print(f"  - Cultivos detectados: {', '.join(sorted(crops))}")

        minimalproduction = dbf_summary["minimalproduction"]
        if minimalproduction:
            print(
                f"  - minimalpro: {dict(sorted(minimalproduction.items(), key=lambda item: str(item[0])))}"
            )

        nonzero = dbf_summary["nonzero_counters"]
        if nonzero:
            print(f"  - Fechas no cero por etapa: {dict(nonzero)}")

        print("\nMuestras de registros")
        for idx, row in enumerate(dbf_summary["sample_rows"], start=1):
            print(f"  {idx}. {format_row(row)}")

    prj_text = read_text_if_exists(prj_path)
    if prj_text:
        print_section("Sistema de coordenadas")
        print(prj_text.strip())

    if xml_path.exists():
        print_section("Metadata XML")
        try:
            xml_summary = parse_xml_summary(xml_path)
            if xml_summary:
                for key, value in xml_summary.items():
                    print(f"{key}: {value}")
            else:
                print("XML presente, pero no encontré campos resumibles simples.")
        except ET.ParseError as exc:
            print(f"No pude parsear el XML: {exc}")

    if txt_files:
        print_section("Vista previa del README/TXT")
        for txt_path in txt_files:
            print(f"\nArchivo: {txt_path.name}")
            text = read_text_if_exists(txt_path)
            if not text:
                print("  No pude leer el contenido.")
                continue
            preview = "\n".join(text.splitlines()[:25])
            print(textwrap.shorten(preview.replace("\n", " | "), width=1000, placeholder=" ..."))


if __name__ == "__main__":
    main()
