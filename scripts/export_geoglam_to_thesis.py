from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from thesis_paths import thesis_path


DEFAULT_NODE = Path(
    r"C:\Users\paola\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
)
DEFAULT_NODE_MODULES = Path(
    r"C:\Users\paola\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules"
)


def resolve_node_executable(user_value: str | None) -> str:
    if user_value:
        return user_value
    if DEFAULT_NODE.exists():
        return str(DEFAULT_NODE)
    fallback = shutil.which("node")
    if fallback:
        return fallback
    raise FileNotFoundError(
        "No encontré Node.js. Pasa --node con la ruta al ejecutable de node."
    )


def ensure_local_node_modules(script_dir: Path) -> None:
    local_node_modules = script_dir / "node_modules"
    if local_node_modules.exists():
        return
    if not DEFAULT_NODE_MODULES.exists():
        raise FileNotFoundError(
            "No encontré el paquete @oai/artifact-tool ni un node_modules local."
        )
    subprocess.run(
        [
            "cmd",
            "/c",
            "mklink",
            "/J",
            str(local_node_modules),
            str(DEFAULT_NODE_MODULES),
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Exporta el shapefile GEOGLAM a CSV/JSON/XLSX usando la estructura de carpetas de tesis."
    )
    parser.add_argument("path", help="Ruta al .shp o a cualquier archivo del conjunto shapefile.")
    parser.add_argument(
        "--node",
        help="Ruta opcional al ejecutable de Node.js. Si no se especifica, intento usar uno disponible.",
    )
    parser.add_argument(
        "--processed-dir",
        default=str(thesis_path("processed", "geoglam_cm4ew_calendars")),
        help="Directorio para CSV y JSON procesados.",
    )
    parser.add_argument(
        "--xlsx",
        default=str(thesis_path("results", "geoglam_cm4ew_calendars.xlsx")),
        help="Ruta del Excel final.",
    )
    args = parser.parse_args()

    script_dir = Path(__file__).resolve().parent
    prepare_script = script_dir / "prepare_shapefile_excel_export.py"
    build_script = script_dir / "build_geoglam_excel.mjs"
    ensure_local_node_modules(script_dir)

    processed_dir = Path(args.processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    metadata_path = processed_dir / "geoglam_metadata.json"
    csv_path = processed_dir / "geoglam_data.csv"
    xlsx_path = Path(args.xlsx)
    xlsx_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            str(prepare_script),
            args.path,
            "--output-dir",
            str(processed_dir),
        ],
        check=True,
    )

    node_executable = resolve_node_executable(args.node)
    completed = subprocess.run(
        [
            node_executable,
            str(build_script),
            str(metadata_path),
            str(csv_path),
            str(xlsx_path),
        ],
        cwd=script_dir,
    )
    if completed.returncode != 0 and not xlsx_path.exists():
        raise subprocess.CalledProcessError(
            completed.returncode,
            completed.args,
        )

    print(f"CSV: {csv_path}")
    print(f"JSON: {metadata_path}")
    print(f"XLSX: {xlsx_path}")


if __name__ == "__main__":
    main()
