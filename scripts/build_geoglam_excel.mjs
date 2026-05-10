import fs from "node:fs/promises";
import path from "node:path";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

function columnLabel(columnNumber) {
  let n = columnNumber;
  let label = "";
  while (n > 0) {
    const remainder = (n - 1) % 26;
    label = String.fromCharCode(65 + remainder) + label;
    n = Math.floor((n - 1) / 26);
  }
  return label;
}

function addMatrix(sheet, startRow, startCol, rows) {
  if (!rows.length || !rows[0].length) {
    return null;
  }
  const rowCount = rows.length;
  const colCount = rows[0].length;
  const startCell = `${columnLabel(startCol)}${startRow}`;
  const endCell = `${columnLabel(startCol + colCount - 1)}${startRow + rowCount - 1}`;
  const range = sheet.getRange(`${startCell}:${endCell}`);
  range.values = rows;
  return range;
}

function styleHeader(range, fillColor = "#DCEAF7") {
  range.format.font.bold = true;
  range.format.fill.color = fillColor;
}

function buildMetadataRows(metadata) {
  const bbox = metadata.spatial.bbox;
  const cropValues = metadata.thematic.crop_values.join(", ");

  return [
    ["Campo", "Valor"],
    ["Base path", metadata.base_path],
    ["Directorio", metadata.directory],
    ["Tipo de geometria", metadata.spatial.shape_type],
    ["Codigo de tipo", metadata.spatial.shape_type_code],
    ["Registros segun .shx", metadata.spatial.records_from_shx],
    ["Registros en DBF", metadata.dbf.num_records],
    ["Registros validos leidos", metadata.thematic.valid_records],
    ["Codificacion", metadata.dbf.encoding],
    ["Actualizado", metadata.dbf.updated_on],
    ["CRS / .prj", metadata.spatial.crs_wkt],
    ["Ubicacion derivada", metadata.spatial.location_representation],
    ["Orden coordenadas", metadata.spatial.coordinate_order],
    ["Registros con alguna fase", metadata.phases.records_with_any_phase],
    ["Filas totales en tabla Fases", metadata.phases.phase_row_count],
    ["BBox xmin", bbox[0]],
    ["BBox ymin", bbox[1]],
    ["BBox xmax", bbox[2]],
    ["BBox ymax", bbox[3]],
    ["Paises distintos", metadata.thematic.distinct_countries],
    ["Regiones distintas", metadata.thematic.distinct_country_regions],
    ["Cultivos/campanas distintos", metadata.thematic.distinct_crops],
    ["Cultivos detectados", cropValues],
    ["minimalpro (conteo)", JSON.stringify(metadata.thematic.minimalpro_counts)],
    ["Etapas con fecha no cero", JSON.stringify(metadata.thematic.nonzero_stage_counts)],
    ["XML creation date", metadata.xml.xml_creation_date ?? ""],
    ["XML creation time", metadata.xml.xml_creation_time ?? ""],
  ];
}

function buildFieldsRows(metadata) {
  const rows = [["Campo", "Tipo", "Longitud", "Decimales"]];
  for (const field of metadata.dbf.fields) {
    rows.push([field.name, field.type, field.length, field.decimals]);
  }
  return rows;
}

function buildFilesRows(metadata) {
  const rows = [["Extension", "Existe", "Tamano (bytes)", "Ruta"]];
  for (const component of metadata.components) {
    rows.push([
      component.extension,
      component.exists ? "Si" : "No",
      component.size_bytes ?? "",
      component.path,
    ]);
  }
  return rows;
}

function buildReadmeRows(metadata) {
  const entries = Object.entries(metadata.readme_files);
  const rows = [["Archivo", "Linea", "Contenido"]];
  for (const [fileName, lines] of entries) {
    for (let idx = 0; idx < lines.length; idx += 1) {
      rows.push([fileName, idx + 1, lines[idx]]);
    }
    rows.push(["", "", ""]);
  }
  return rows;
}

function buildSheetRows(columns, rows) {
  return [columns, ...rows];
}

async function main() {
  const metadataPath = process.argv[2];
  const csvPath = process.argv[3];
  const outputPath = process.argv[4];

  if (!metadataPath || !csvPath || !outputPath) {
    throw new Error(
      "Uso: node build_geoglam_excel.mjs <metadata.json> <data.csv> <output.xlsx>",
    );
  }

  const metadata = JSON.parse(await fs.readFile(metadataPath, "utf8"));
  const csvText = await fs.readFile(csvPath, "utf8");

  const workbook = await Workbook.fromCSV(csvText, { sheetName: "Datos" });
  const dataSheet = workbook.worksheets.getItem("Datos");
  const dataColumnCount = metadata.export.data_columns.length;
  styleHeader(dataSheet.getRange(`A1:${columnLabel(dataColumnCount)}1`), "#CFE8D8");
  dataSheet.freezePanes.freezeRows = 1;
  dataSheet.showGridLines = true;
  dataSheet.getUsedRange().format.autofitColumns();
  dataSheet.getRange(`A:${columnLabel(dataColumnCount)}`).format.columnWidthPx = 130;
  dataSheet.getRange("R:S").format.columnWidthPx = 220;

  const fenologiaSheet = workbook.worksheets.add("Fenologia");
  const fenologiaRows = buildSheetRows(
    metadata.export.fenologia_columns,
    metadata.export.fenologia_rows,
  );
  const fenologiaRange = addMatrix(fenologiaSheet, 1, 1, fenologiaRows);
  styleHeader(
    fenologiaSheet.getRange(`A1:${columnLabel(metadata.export.fenologia_columns.length)}1`),
    "#D7E8FA",
  );
  fenologiaSheet.freezePanes.freezeRows = 1;
  fenologiaRange.format.autofitColumns();
  fenologiaSheet.getRange("A:M").format.columnWidthPx = 130;

  const phasesSheet = workbook.worksheets.add("Fases");
  const phaseRows = buildSheetRows(metadata.export.phase_columns, metadata.export.phase_rows);
  const phasesRange = addMatrix(phasesSheet, 1, 1, phaseRows);
  styleHeader(
    phasesSheet.getRange(`A1:${columnLabel(metadata.export.phase_columns.length)}1`),
    "#FADFC8",
  );
  phasesSheet.freezePanes.freezeRows = 1;
  phasesRange.format.autofitColumns();
  phasesSheet.getRange("A:R").format.columnWidthPx = 130;
  phasesSheet.getRange("D:E").format.columnWidthPx = 190;

  const summarySheet = workbook.worksheets.add("Resumen_Fases");
  const phaseSummaryRows = buildSheetRows(
    metadata.export.phase_summary_columns,
    metadata.export.phase_summary_rows,
  );
  const summaryRange = addMatrix(summarySheet, 1, 1, phaseSummaryRows);
  styleHeader(
    summarySheet.getRange(
      `A1:${columnLabel(metadata.export.phase_summary_columns.length)}1`,
    ),
    "#F5E6A7",
  );
  summarySheet.freezePanes.freezeRows = 1;
  summaryRange.format.autofitColumns();
  summarySheet.getRange("A:H").format.columnWidthPx = 150;

  const metadataSheet = workbook.worksheets.add("Metadata");
  const metadataRows = buildMetadataRows(metadata);
  addMatrix(metadataSheet, 1, 1, metadataRows);
  styleHeader(metadataSheet.getRange("A1:B1"));
  metadataSheet.freezePanes.freezeRows = 1;
  metadataSheet.getRange("A:A").format.font.bold = true;
  metadataSheet.getRange("B:B").format.wrapText = true;
  metadataSheet.getRange("A:A").format.columnWidthPx = 220;
  metadataSheet.getRange("B:B").format.columnWidthPx = 520;

  const fieldsSheet = workbook.worksheets.add("Campos");
  const fieldsRows = buildFieldsRows(metadata);
  const fieldsRange = addMatrix(fieldsSheet, 1, 1, fieldsRows);
  styleHeader(fieldsSheet.getRange("A1:D1"), "#F8E7C9");
  fieldsSheet.freezePanes.freezeRows = 1;
  fieldsRange.format.autofitColumns();

  const filesSheet = workbook.worksheets.add("Archivos");
  const filesRows = buildFilesRows(metadata);
  const filesRange = addMatrix(filesSheet, 1, 1, filesRows);
  styleHeader(filesSheet.getRange("A1:D1"), "#E6D7F5");
  filesSheet.freezePanes.freezeRows = 1;
  filesSheet.getRange("D:D").format.wrapText = true;
  filesRange.format.autofitColumns();
  filesSheet.getRange("D:D").format.columnWidthPx = 520;

  const readmeSheet = workbook.worksheets.add("README");
  const readmeRows = buildReadmeRows(metadata);
  const readmeRange = addMatrix(readmeSheet, 1, 1, readmeRows);
  styleHeader(readmeSheet.getRange("A1:C1"), "#F6E9B9");
  readmeSheet.freezePanes.freezeRows = 1;
  readmeSheet.getRange("C:C").format.wrapText = true;
  readmeRange.format.autofitColumns();
  readmeSheet.getRange("C:C").format.columnWidthPx = 700;

  const dataCheck = await workbook.inspect({
    kind: "table",
    range: "Datos!A1:S10",
    include: "values",
    tableMaxRows: 10,
    tableMaxCols: 19,
  });
  console.log(dataCheck.ndjson);

  const fenologiaCheck = await workbook.inspect({
    kind: "table",
    range: "Fenologia!A1:M10",
    include: "values",
    tableMaxRows: 10,
    tableMaxCols: 13,
  });
  console.log(fenologiaCheck.ndjson);

  const phasesCheck = await workbook.inspect({
    kind: "table",
    range: "Fases!A1:R10",
    include: "values",
    tableMaxRows: 10,
    tableMaxCols: 18,
  });
  console.log(phasesCheck.ndjson);

  const summaryCheck = await workbook.inspect({
    kind: "table",
    range: "Resumen_Fases!A1:H10",
    include: "values",
    tableMaxRows: 10,
    tableMaxCols: 8,
  });
  console.log(summaryCheck.ndjson);

  const metadataCheck = await workbook.inspect({
    kind: "table",
    range: "Metadata!A1:B20",
    include: "values",
    tableMaxRows: 20,
    tableMaxCols: 2,
  });
  console.log(metadataCheck.ndjson);

  const errors = await workbook.inspect({
    kind: "match",
    searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
    options: { useRegex: true, maxResults: 50 },
    summary: "formula error scan",
  });
  console.log(errors.ndjson);

  await workbook.render({ sheetName: "Datos", range: "A1:S20", scale: 1.4 });
  await workbook.render({ sheetName: "Fenologia", range: "A1:M20", scale: 1.4 });
  await workbook.render({ sheetName: "Fases", range: "A1:R20", scale: 1.4 });
  await workbook.render({ sheetName: "Resumen_Fases", range: "A1:H10", scale: 1.4 });
  await workbook.render({ sheetName: "Metadata", range: "A1:B24", scale: 1.4 });

  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  const output = await SpreadsheetFile.exportXlsx(workbook);
  await output.save(outputPath);
  console.log(outputPath);
  process.exit(0);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
