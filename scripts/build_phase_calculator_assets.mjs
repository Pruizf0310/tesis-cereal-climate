import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const repo = path.resolve(path.dirname(__filename), "..");

const DEFAULT_PIXEL_INVENTORY =
  "C:\\Users\\paola\\Tesis\\03_Resultados\\Clima_phase\\all_h5_pixels_latlon.csv";
const DEFAULT_PHENOLOGY = path.join(repo, "web-v2", "public", "data", "phenology_typical.json");
const DEFAULT_OUT_DIR = path.join(repo, "web-v2", "public", "data");

const MONTH_START_DOY = [1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335];
const MONTH_END_DOY = [31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365];
const PHASES = ["F1", "F2", "F3"];
const PIXEL_COLUMNS = [
  "crop",
  "pixel_id_h5",
  "lat_idx",
  "lon_idx",
  "lat",
  "lon",
  "lon_ee",
  "lat_band",
  "pixel_lat_min",
  "pixel_lat_max",
  "pixel_lon_min_ee",
  "pixel_lon_max_ee"
];

function parseArgs(argv) {
  const args = {
    pixelInventory: DEFAULT_PIXEL_INVENTORY,
    phenology: DEFAULT_PHENOLOGY,
    outDir: DEFAULT_OUT_DIR
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    const value = argv[index + 1];
    if (arg === "--pixel-inventory" && value) {
      args.pixelInventory = value;
      index += 1;
    } else if (arg === "--phenology" && value) {
      args.phenology = value;
      index += 1;
    } else if (arg === "--out-dir" && value) {
      args.outDir = value;
      index += 1;
    } else if (arg === "--help") {
      console.log(`Usage: node scripts/build_phase_calculator_assets.mjs [options]

Options:
  --pixel-inventory <path>  Source all_h5_pixels_latlon.csv
  --phenology <path>        Source phenology_typical.json
  --out-dir <path>          Output public data directory`);
      process.exit(0);
    }
  }

  return args;
}

function parseCsv(text) {
  const lines = text.replace(/^\uFEFF/, "").trim().split(/\r?\n/);
  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).filter(Boolean).map((line) => {
    const values = splitCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

function splitCsvLine(line) {
  const values = [];
  let current = "";
  let quoted = false;

  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    const next = line[index + 1];
    if (char === '"' && quoted && next === '"') {
      current += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(current);
      current = "";
    } else {
      current += char;
    }
  }
  values.push(current);
  return values;
}

function csvEscape(value) {
  const text = value == null ? "" : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function copyPixelInventory(source, destination) {
  if (!fs.existsSync(source)) throw new Error(`Pixel inventory not found: ${source}`);
  const rows = parseCsv(fs.readFileSync(source, "utf8"));
  const missing = PIXEL_COLUMNS.filter((column) => !(column in (rows[0] ?? {})));
  if (missing.length) throw new Error(`Pixel inventory is missing columns: ${missing.join(", ")}`);

  const csv = [
    PIXEL_COLUMNS.join(","),
    ...rows.map((row) => PIXEL_COLUMNS.map((column) => csvEscape(row[column])).join(","))
  ].join("\n");
  fs.writeFileSync(destination, `${csv}\n`, "utf8");
  return rows.length;
}

function phaseGroups(months, monthPhase, phase) {
  const indexes = months.map((month, index) => (monthPhase[month] === phase ? index : -1)).filter((index) => index >= 0);
  if (!indexes.length) return [];

  const groups = [];
  let current = [indexes[0]];
  for (let index = 1; index < indexes.length; index += 1) {
    if (indexes[index] === indexes[index - 1] + 1) current.push(indexes[index]);
    else {
      groups.push(current);
      current = [indexes[index]];
    }
  }
  groups.push(current);

  if (groups.length > 1 && groups[0][0] === 0 && groups[groups.length - 1].at(-1) === 11) {
    const last = groups.pop();
    groups[0] = last.concat(groups[0]);
  }
  return groups;
}

function dominantPhaseWindow(months, band, phase) {
  const groups = phaseGroups(months, band.phases ?? {}, phase);
  if (!groups.length) return null;

  const group = groups.sort((a, b) => b.length - a.length)[0];
  const startMonth = group[0];
  const endMonth = group[group.length - 1];
  return {
    start_doy: MONTH_START_DOY[startMonth],
    end_doy: MONTH_END_DOY[endMonth],
    crosses_year: startMonth > endMonth,
    months: group.map((index) => months[index]),
    duration_days: band.phaseDurations?.[phase] ?? null
  };
}

function buildCalendarWindows(source, destination) {
  if (!fs.existsSync(source)) throw new Error(`Phenology JSON not found: ${source}`);
  const payload = JSON.parse(fs.readFileSync(source, "utf8"));
  const months = payload.months;
  const output = {
    source: "Derived from phenology_typical.json monthly dominant phases",
    resolution: "monthly-to-DOY approximation",
    phaseLegend: payload.phaseLegend ?? {},
    crops: {}
  };

  for (const crop of payload.crops ?? []) {
    output.crops[crop.id] = { label: crop.label ?? crop.id, seasons: {} };
    for (const season of crop.seasons ?? []) {
      const seasonOutput = { label: season.label ?? season.id, bands: {} };
      for (const band of season.bands ?? []) {
        const phases = {};
        for (const phase of PHASES) {
          const window = dominantPhaseWindow(months, band, phase);
          if (window) phases[phase] = window;
        }
        seasonOutput.bands[band.id] = {
          latMin: band.latMin,
          latMax: band.latMax,
          latBand: band.latBand,
          phases,
          matchPct: band.matchPct ?? 0,
          coveragePct: band.coveragePct ?? 0
        };
      }
      output.crops[crop.id].seasons[season.id] = seasonOutput;
    }
  }

  fs.writeFileSync(destination, JSON.stringify(output, null, 2), "utf8");
  return output;
}

const args = parseArgs(process.argv.slice(2));
fs.mkdirSync(args.outDir, { recursive: true });

const pixelOut = path.join(args.outDir, "phase_pixel_inventory.csv");
const calendarOut = path.join(args.outDir, "phase_calendar_windows.json");

const rows = copyPixelInventory(args.pixelInventory, pixelOut);
const windows = buildCalendarWindows(args.phenology, calendarOut);

console.log(`Wrote ${pixelOut} (${rows.toLocaleString("en-US")} pixels)`);
console.log(`Wrote ${calendarOut} (${Object.keys(windows.crops).length} crops)`);
console.log("No daily climate series were downloaded or stored.");
