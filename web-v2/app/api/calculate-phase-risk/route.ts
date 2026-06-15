import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { NextResponse } from "next/server";
import type {
  AnnualPhaseMetric,
  DailyPhaseValue,
  Phase,
  PhaseCalculationRequest,
  PhaseCalculationResponse,
  PhaseCalendarWindows,
  ThresholdOperator,
  PhaseVariable
} from "@/lib/phase-calculator";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
export const maxDuration = 300;

const require = createRequire(import.meta.url);
const ee = require("@google/earthengine");
const DATASET = "ECMWF/ERA5_LAND/DAILY_AGGR";
const CALENDAR_PATH = join(process.cwd(), "public", "data", "phase_calendar_windows.json");

let eeInitPromise: Promise<void> | null = null;
let calendarCache: PhaseCalendarWindows | null = null;

interface GeeDailyValue {
  date?: string;
  doy?: number;
  value?: number | null;
}

function jsonResponse(body: PhaseCalculationResponse, status = 200) {
  return NextResponse.json(body, { status });
}

function wrapLon180(lon: number) {
  return ((lon + 180) % 360 + 360) % 360 - 180;
}

function latBandId(lat: number) {
  let upper = Math.ceil(lat / 10) * 10;
  if (lat === upper) upper += 10;
  const lower = upper - 10;
  return `${upper}_${lower}`;
}

function doyToDate(year: number, doy: number) {
  const date = new Date(Date.UTC(year, 0, 1));
  date.setUTCDate(doy);
  return date;
}

function isoDate(date: Date) {
  return date.toISOString().slice(0, 10);
}

function percentile(values: number[], q: number) {
  if (!values.length) return null;
  const ordered = [...values].sort((a, b) => a - b);
  if (ordered.length === 1) return ordered[0];
  const position = (ordered.length - 1) * q;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return ordered[lower];
  return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower);
}

function maxConsecutive(flags: boolean[]) {
  let best = 0;
  let current = 0;
  for (const flag of flags) {
    if (flag) {
      current += 1;
      best = Math.max(best, current);
    } else {
      current = 0;
    }
  }
  return best;
}

function thresholdExceeded(value: number | null, threshold: number, operator: ThresholdOperator = ">") {
  if (value == null || !Number.isFinite(value)) return false;
  if (operator === "<") return value < threshold;
  if (operator === "<=") return value <= threshold;
  if (operator === ">=") return value >= threshold;
  return value > threshold;
}

function loadCalendar() {
  if (!calendarCache) {
    calendarCache = JSON.parse(readFileSync(CALENDAR_PATH, "utf8"));
  }
  return calendarCache as PhaseCalendarWindows;
}

function findPhaseWindow(crop: PhaseCalculationRequest["crop"], lat: number, phase: Phase) {
  const calendar = loadCalendar();
  const cropCalendar = calendar.crops[crop];
  const firstSeason = cropCalendar ? Object.values(cropCalendar.seasons)[0] : null;
  if (!firstSeason) {
    throw new Error(`No phenology calendar is available for ${crop}.`);
  }

  const bandId = latBandId(lat);
  const band =
    firstSeason.bands[bandId] ??
    Object.values(firstSeason.bands).find(
      (item) => lat >= Math.min(item.latMin, item.latMax) && lat < Math.max(item.latMin, item.latMax)
    );
  const window = band?.phases[phase];
  if (!band || !window) {
    throw new Error(`No ${phase} phenology window found for ${crop} at latitude ${lat}.`);
  }

  return { ...window, lat_band: band.latBand, lat_band_id: bandId };
}

function validatePayload(body: Partial<PhaseCalculationRequest>) {
  if (typeof body.lat !== "number" || !Number.isFinite(body.lat) || body.lat < -90 || body.lat > 90) {
    return "lat must be a number between -90 and 90.";
  }
  if (typeof body.lon !== "number" || !Number.isFinite(body.lon) || body.lon < -360 || body.lon > 360) {
    return "lon must be a number between -360 and 360.";
  }
  if (!body.crop) return "crop is required.";
  if (!body.phase) return "phase is required.";
  if (!body.variable) return "variable is required.";
  if (typeof body.threshold !== "number" || !Number.isFinite(body.threshold)) return "threshold must be numeric.";
  if (typeof body.start_year !== "number" || typeof body.end_year !== "number") {
    return "start_year and end_year are required.";
  }
  if (!Number.isInteger(body.start_year) || !Number.isInteger(body.end_year)) {
    return "start_year and end_year must be integers.";
  }
  if (body.start_year < 1981 || body.end_year > 2016 || body.start_year > body.end_year) {
    return "year range must be within 1981-2016.";
  }
  if (typeof body.min_days_event !== "number") {
    return "min_days_event is required.";
  }
  if (!Number.isInteger(body.min_days_event) || body.min_days_event < 1) {
    return "min_days_event must be an integer greater than or equal to 1.";
  }
  return null;
}

function ensureEeInitialized() {
  if (eeInitPromise) return eeInitPromise;

  const project = process.env.GOOGLE_CLOUD_PROJECT;
  const clientEmail = process.env.GEE_SERVICE_ACCOUNT_EMAIL;
  const privateKey = process.env.GEE_SERVICE_ACCOUNT_PRIVATE_KEY?.replace(/\\n/g, "\n");

  if (!project || !clientEmail || !privateKey) {
    throw new Error(
      "Backend GEE no configurado. Define GOOGLE_CLOUD_PROJECT, GEE_SERVICE_ACCOUNT_EMAIL y GEE_SERVICE_ACCOUNT_PRIVATE_KEY en Vercel."
    );
  }

  eeInitPromise = new Promise((resolve, reject) => {
    ee.data.authenticateViaPrivateKey(
      {
        client_email: clientEmail,
        private_key: privateKey,
        project_id: project
      },
      () => {
        ee.initialize(null, null, resolve, reject, null, project);
      },
      reject
    );
  });

  return eeInitPromise;
}

function variableImage(image: any, variable: PhaseVariable) {
  if (variable === "tmax_c") return image.select("temperature_2m_max").subtract(273.15).rename("value");
  if (variable === "tmean_c") return image.select("temperature_2m").subtract(273.15).rename("value");
  if (variable === "tmin_c") return image.select("temperature_2m_min").subtract(273.15).rename("value");
  if (variable === "precip_mm") return image.select("total_precipitation_sum").multiply(1000).rename("value");
  if (variable === "swvl1") return image.select("volumetric_soil_water_layer_1").rename("value");
  if (variable === "swvl2") return image.select("volumetric_soil_water_layer_2").rename("value");
  if (variable === "swvl3") return image.select("volumetric_soil_water_layer_3").rename("value");
  if (variable === "rootzone_sm") {
    return image
      .select("volumetric_soil_water_layer_1")
      .multiply(0.07)
      .add(image.select("volumetric_soil_water_layer_2").multiply(0.21))
      .add(image.select("volumetric_soil_water_layer_3").multiply(0.72))
      .rename("value");
  }
  throw new Error(`Unsupported variable: ${variable}`);
}

function getInfo<T>(value: any): Promise<T> {
  return new Promise((resolve, reject) => {
    value.getInfo((result: T, error: unknown) => {
      if (error) reject(error);
      else resolve(result);
    });
  });
}

async function queryDailyValues(geometry: any, start: Date, endExclusive: Date, variable: PhaseVariable) {
  const collection = ee.ImageCollection(DATASET).filterDate(isoDate(start), isoDate(endExclusive));
  const features = collection.map((image: any) => {
    const value = variableImage(image, variable)
      .reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry,
        scale: 11132,
        bestEffort: true,
        maxPixels: 1000000
      })
      .get("value");

    return ee.Feature(null, {
      date: image.date().format("YYYY-MM-dd"),
      doy: image.date().getRelative("day", "year").add(1),
      value
    });
  });

  const info = await getInfo<{ features: { properties: GeeDailyValue }[] }>(ee.FeatureCollection(features));
  return info.features.map((feature) => feature.properties);
}

function annualMetrics(
  year: number,
  daily: GeeDailyValue[],
  threshold: number,
  minDaysEvent: number,
  operator: ThresholdOperator = ">"
): AnnualPhaseMetric {
  const values = daily
    .map((item) => item.value)
    .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
  const flags: boolean[] = [];
  const dailyValues: DailyPhaseValue[] = daily.map((item) => {
    const value = typeof item.value === "number" && Number.isFinite(item.value) ? item.value : null;
    const exceeds = thresholdExceeded(value, threshold, operator);
    flags.push(exceeds);
    return {
      date: item.date ?? "",
      doy: Number(item.doy ?? 0),
      value,
      exceeds
    };
  });

  const nExceedanceDays = flags.filter(Boolean).length;
  return {
    year,
    n_days: values.length,
    n_exceedance_days: nExceedanceDays,
    max_value: values.length ? Math.max(...values) : null,
    mean_value: values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null,
    p95_value: percentile(values, 0.95),
    max_consecutive_exceedance_days: maxConsecutive(flags),
    event_occurred: nExceedanceDays >= minDaysEvent,
    daily_values: dailyValues
  };
}

export async function GET() {
  const configured = Boolean(
    process.env.GOOGLE_CLOUD_PROJECT &&
      process.env.GEE_SERVICE_ACCOUNT_EMAIL &&
      process.env.GEE_SERVICE_ACCOUNT_PRIVATE_KEY
  );
  return jsonResponse({
    ok: configured,
    configured,
    message: configured
      ? "Vercel GEE backend is configured."
      : "Backend GEE no configurado. Faltan variables de entorno del Service Account en Vercel."
  });
}

export async function POST(request: Request) {
  let payload: PhaseCalculationRequest;
  try {
    payload = await request.json();
  } catch {
    return jsonResponse({ ok: false, configured: false, message: "Request body must be valid JSON." }, 400);
  }

  const validationError = validatePayload(payload);
  if (validationError) {
    return jsonResponse({ ok: false, configured: false, request: payload, message: validationError }, 400);
  }

  try {
    await ensureEeInitialized();

    const lon = wrapLon180(payload.lon);
    const geometry = ee.Geometry.Rectangle([lon - 0.25, payload.lat - 0.25, lon + 0.25, payload.lat + 0.25], null, false);
    const phaseWindow = findPhaseWindow(payload.crop, payload.lat, payload.phase);

    const annual: AnnualPhaseMetric[] = [];
    for (let year = payload.start_year; year <= payload.end_year; year += 1) {
      const start = doyToDate(year, phaseWindow.start_doy);
      const endYear = phaseWindow.crosses_year ? year + 1 : year;
      const endExclusive = doyToDate(endYear, phaseWindow.end_doy + 1);
      const daily = await queryDailyValues(geometry, start, endExclusive, payload.variable);
      annual.push(annualMetrics(year, daily, payload.threshold, payload.min_days_event, payload.operator ?? ">"));
    }

    const validYears = annual.filter((item) => item.n_days > 0).length;
    const criticalYears = annual.filter((item) => item.n_days > 0 && item.event_occurred).map((item) => item.year);
    const eventYears = criticalYears.length;

    return jsonResponse({
      ok: true,
      configured: true,
      request: payload,
      result: {
        probability: validYears ? eventYears / validYears : 0,
        event_years: eventYears,
        valid_years: validYears,
        critical_years: criticalYears,
        years_critical: criticalYears,
        annual,
        daily: annual[annual.length - 1]?.daily_values ?? [],
        source: DATASET
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const configured = !message.startsWith("Backend GEE no configurado");
    return jsonResponse({ ok: false, configured, request: payload, message }, configured ? 502 : 200);
  }
}
