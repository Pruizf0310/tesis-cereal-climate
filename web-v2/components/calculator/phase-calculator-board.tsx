"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Calculator, Download, Loader2, MapPin, Play, Table2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Crop } from "@/lib/types";
import { CROPS } from "@/lib/types";
import {
  MIN_DAYS_EVENT_OPTIONS,
  PHASE_VARIABLES,
  csvEscape,
  gridCenter05,
  latBandKeyFromInventory,
  wrapLon180,
  type AnnualPhaseMetric,
  type CalendarBandWindow,
  type Phase,
  type PhaseCalculationRequest,
  type PhaseCalculationResponse,
  type PhaseCalendarWindows,
  type PhaseWindow,
  type PhaseVariable,
  type PixelInventoryRow
} from "@/lib/phase-calculator";

const PHASES: Phase[] = ["F1", "F2", "F3"];

type ApiState = "idle" | "loading" | "success" | "error";

interface DerivedContext {
  lat: number;
  lon: number;
  latGrid: number;
  lonGrid: number;
  pixel: PixelInventoryRow | null;
  isExactCell: boolean;
  seasonId: string | null;
  seasonLabel: string | null;
  band: CalendarBandWindow | null;
  phaseWindow: PhaseWindow | null;
}

interface FormState {
  lat: string;
  lon: string;
  crop: Crop;
  phase: Phase;
  variable: PhaseVariable;
  threshold: string;
  minDaysEvent: string;
  startYear: string;
  endYear: string;
}

const INITIAL_FORM: FormState = {
  lat: "4.75",
  lon: "-74.25",
  crop: "maize",
  phase: "F2",
  variable: "tmax_c",
  threshold: "35",
  minDaysEvent: "3",
  startYear: "1981",
  endYear: "2016"
};

export function PhaseCalculatorBoard() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [pixels, setPixels] = useState<PixelInventoryRow[]>([]);
  const [calendar, setCalendar] = useState<PhaseCalendarWindows | null>(null);
  const [apiState, setApiState] = useState<ApiState>("idle");
  const [apiResponse, setApiResponse] = useState<PhaseCalculationResponse | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(2016);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      fetch("/data/phase_pixel_inventory.csv").then((res) => res.text()),
      fetch("/data/phase_calendar_windows.json").then((res) => res.json())
    ])
      .then(([csv, calendarData]) => {
        setPixels(parsePixelInventory(csv));
        setCalendar(calendarData);
      })
      .catch(() => setLoadError("Could not load public calculator metadata."));
  }, []);

  const derived = useMemo(() => {
    const lat = Number(form.lat);
    const lon = Number(form.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;

    const latGrid = gridCenter05(lat);
    const lonGrid = gridCenter05(wrapLon180(lon));
    const cropPixels = pixels.filter((pixel) => pixel.crop === form.crop);
    const exact = cropPixels.find(
      (pixel) =>
        latGrid >= Math.min(pixel.pixel_lat_min, pixel.pixel_lat_max) &&
        latGrid < Math.max(pixel.pixel_lat_min, pixel.pixel_lat_max) &&
        lonGrid >= Math.min(pixel.pixel_lon_min_ee, pixel.pixel_lon_max_ee) &&
        lonGrid < Math.max(pixel.pixel_lon_min_ee, pixel.pixel_lon_max_ee)
    );
    const nearest = exact ?? nearestPixel(cropPixels, latGrid, lonGrid);

    const cropCalendar = calendar?.crops[form.crop];
    const firstSeason = cropCalendar ? Object.entries(cropCalendar.seasons)[0] : null;
    const bandId = nearest ? latBandKeyFromInventory(nearest.lat_band) : null;
    const band =
      firstSeason && bandId
        ? firstSeason[1].bands[bandId] ??
          Object.values(firstSeason[1].bands).find(
            (item) => latGrid >= Math.min(item.latMin, item.latMax) && latGrid < Math.max(item.latMin, item.latMax)
          )
        : null;
    const phaseWindow = band?.phases[form.phase] ?? null;

    return {
      lat: Number(form.lat),
      lon: wrapLon180(Number(form.lon)),
      latGrid,
      lonGrid,
      pixel: nearest,
      isExactCell: Boolean(exact),
      seasonId: firstSeason?.[0] ?? null,
      seasonLabel: firstSeason?.[1].label ?? null,
      band,
      phaseWindow
    };
  }, [calendar, form.crop, form.lat, form.lon, form.phase, pixels]);

  const result = apiResponse?.result ?? null;
  const annual = result?.annual ?? [];
  const dailySeries = useMemo(() => {
    if (!result) return [];
    if (result.daily?.length) return result.daily;
    return annual.find((item) => item.year === selectedYear)?.daily_values ?? [];
  }, [annual, result, selectedYear]);

  useEffect(() => {
    if (annual.length) {
      setSelectedYear(annual[annual.length - 1].year);
    }
  }, [annual]);

  async function submit() {
    if (!derived?.pixel || !derived.phaseWindow) {
      setApiResponse({
        ok: false,
        configured: false,
        message: "No compatible pixel or phenology window was found for this crop and coordinate."
      });
      setApiState("error");
      return;
    }

    const request: PhaseCalculationRequest = {
      lat: derived.lat,
      lon: derived.lon,
      crop: form.crop,
      phase: form.phase,
      variable: form.variable,
      threshold: Number(form.threshold),
      min_days_event: Number(form.minDaysEvent),
      start_year: Number(form.startYear),
      end_year: Number(form.endYear)
    };

    setApiState("loading");
    setApiResponse(null);
    try {
      const response = await fetch("/api/calculate-phase-risk", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request)
      });
      const data: PhaseCalculationResponse = await response.json();
      const normalized = normalizeResponse(data, request);
      setApiResponse(normalized);
      setApiState(data.ok ? "success" : "error");
    } catch {
      setApiResponse({
        ok: false,
        configured: true,
        message: "No se pudo contactar el backend GEE de Vercel."
      });
      setApiState("error");
    }
  }

  function exportCsv() {
    if (!annual.length) return;
    const header = [
      "year",
      "n_days",
      "n_exceedance_days",
      "max_value",
      "mean_value",
      "p95_value",
      "max_consecutive_exceedance_days",
      "event_occurred"
    ];
    const rows = annual.map((item) => header.map((key) => csvEscape(item[key as keyof AnnualPhaseMetric])).join(","));
    const blob = new Blob([[header.join(","), ...rows].join("\n")], { type: "text/csv;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `phase-calculator-${form.crop}-${form.phase}-${form.variable}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (loadError) {
    return <StatusPanel tone="error" title="Metadata unavailable" message={loadError} />;
  }

  return (
    <div className="mt-12 grid gap-6 lg:grid-cols-[420px_minmax(0,1fr)]">
      <section className="glass top-edge relative rounded-sm border border-line p-4 animate-fade-up">
        <div className="mb-5 flex items-start justify-between gap-3">
          <div>
            <p className="kicker">Query setup</p>
            <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
              One pixel, one phase
            </h2>
          </div>
          <Calculator className="h-5 w-5 text-cool" />
        </div>

        <div className="grid gap-4">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Latitude">
              <input value={form.lat} onChange={(event) => update("lat", event.target.value)} className={inputClass()} />
            </Field>
            <Field label="Longitude">
              <input value={form.lon} onChange={(event) => update("lon", event.target.value)} className={inputClass()} />
            </Field>
          </div>

          <Field label="Crop">
            <Segmented
              options={CROPS}
              value={form.crop}
              onChange={(value) => update("crop", value as Crop)}
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Phase">
              <select value={form.phase} onChange={(event) => update("phase", event.target.value as Phase)} className={inputClass()}>
                {PHASES.map((phase) => (
                  <option key={phase} value={phase}>
                    {phase}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Variable">
              <select
                value={form.variable}
                onChange={(event) => update("variable", event.target.value as PhaseVariable)}
                className={inputClass()}
              >
                {PHASE_VARIABLES.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Threshold">
              <input
                value={form.threshold}
                onChange={(event) => update("threshold", event.target.value)}
                className={inputClass()}
              />
            </Field>
            <Field label="Event minimum">
              <select
                value={form.minDaysEvent}
                onChange={(event) => update("minDaysEvent", event.target.value)}
                className={inputClass()}
              >
                {MIN_DAYS_EVENT_OPTIONS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <Field label="Start year">
              <input
                value={form.startYear}
                onChange={(event) => update("startYear", event.target.value)}
                className={inputClass()}
              />
            </Field>
            <Field label="End year">
              <input
                value={form.endYear}
                onChange={(event) => update("endYear", event.target.value)}
                className={inputClass()}
              />
            </Field>
          </div>

          <button
            type="button"
            onClick={submit}
            disabled={apiState === "loading" || !pixels.length || !calendar}
            className="mt-1 flex h-10 items-center justify-center gap-2 rounded-sm border border-cool/35 bg-cool/[0.1] px-4 text-[12.5px] font-semibold text-ink transition-colors hover:bg-cool/[0.16] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {apiState === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
            Calculate historical probability
          </button>
        </div>

        <PixelSummary derived={derived} />
        <PixelGuide
          crop={form.crop}
          pixels={pixels}
          derived={derived}
          onUsePixel={(pixel) => {
            update("lat", String(pixel.lat));
            update("lon", String(pixel.lon_ee));
          }}
        />
      </section>

      <section className="space-y-6">
        {apiResponse && !apiResponse.ok ? (
          <StatusPanel
            tone={apiResponse.configured ? "error" : "warn"}
            title={apiResponse.configured ? "GEE request failed" : "Backend GEE no configurado"}
            message={apiResponse.message ?? "No calculation result was returned."}
          />
        ) : null}

        <ProbabilityPanel result={result} variable={form.variable} />
        <AnnualChart annual={annual} selectedYear={selectedYear} onSelectYear={setSelectedYear} />
        <DailyChart
          annual={annual}
          daily={dailySeries}
          selectedYear={selectedYear}
          onYearChange={setSelectedYear}
          variable={form.variable}
          threshold={Number(form.threshold)}
        />
        <AnnualTable annual={annual} onExport={exportCsv} />
        <SourcePanel />
      </section>
    </div>
  );

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }
}

function PixelSummary({ derived }: { derived: DerivedContext | null }) {
  if (!derived) return null;
  return (
    <div className="mt-5 rounded-sm border border-line bg-white/[0.025] p-3">
      <div className="flex items-center gap-2 text-[12px] font-medium text-ink">
        <MapPin className="h-3.5 w-3.5 text-warm" />
        Spatial match
      </div>
      <div className="mt-3 grid gap-2 text-[11.5px] text-ink-dim">
        <Metric label="0.5 cell center" value={`${derived.latGrid.toFixed(2)}, ${derived.lonGrid.toFixed(2)}`} />
        <Metric label="Inventory pixel" value={derived.pixel ? `#${derived.pixel.pixel_id_h5}` : "No pixel"} />
        <Metric label="Latitude band" value={derived.pixel?.lat_band.replace(/_/g, " ") ?? derived.band?.latBand ?? "No band"} />
        <Metric
          label="Phase window"
          value={
            derived.phaseWindow
              ? `DOY ${derived.phaseWindow.start_doy}-${derived.phaseWindow.end_doy}${derived.phaseWindow.crosses_year ? " next year" : ""}`
              : "No F window"
          }
        />
        <Metric label="Cell polygon" value={derived.pixel ? polygonLabel(derived.pixel) : "Unavailable"} />
      </div>
    </div>
  );
}

function PixelGuide({
  crop,
  pixels,
  derived,
  onUsePixel
}: {
  crop: Crop;
  pixels: PixelInventoryRow[];
  derived: DerivedContext | null;
  onUsePixel: (pixel: PixelInventoryRow) => void;
}) {
  const cropPixels = useMemo(() => pixels.filter((pixel) => pixel.crop === crop), [crop, pixels]);
  const bandCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const pixel of cropPixels) counts.set(pixel.lat_band, (counts.get(pixel.lat_band) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [cropPixels]);
  const nearby = useMemo(() => {
    const lat = derived?.latGrid ?? 0;
    const lon = derived?.lonGrid ?? 0;
    return [...cropPixels]
      .sort((a, b) => Math.hypot(a.lat - lat, a.lon_ee - lon) - Math.hypot(b.lat - lat, b.lon_ee - lon))
      .slice(0, 8);
  }, [cropPixels, derived?.latGrid, derived?.lonGrid]);

  return (
    <div className="mt-4 rounded-sm border border-line bg-white/[0.025] p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[12px] font-medium text-ink">Pixel guide</p>
          <p className="mt-1 text-[10.5px] text-ink-mute">
            {cropPixels.length.toLocaleString("en-US")} valid H5 pixels for {crop}
          </p>
        </div>
        <span className="num rounded-sm border border-line bg-bg-panel px-2 py-1 text-[10.5px] text-ink-dim">
          0.5 deg cells
        </span>
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {bandCounts.slice(0, 6).map(([band, count]) => (
          <span key={band} className="rounded-sm border border-line bg-white/[0.02] px-2 py-1 text-[10.5px] text-ink-dim">
            {band.replace(/_/g, " ")}: <span className="num text-ink">{count}</span>
          </span>
        ))}
      </div>

      <div className="mt-3 max-h-[235px] overflow-auto rounded-sm border border-line/70">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-bg-panel text-[9.5px] uppercase tracking-wider text-ink-mute">
            <tr>
              <th className="px-2 py-2 font-medium">Center</th>
              <th className="px-2 py-2 font-medium">Band</th>
              <th className="px-2 py-2 font-medium" />
            </tr>
          </thead>
          <tbody>
            {nearby.map((pixel) => (
              <tr key={pixel.pixel_id_h5} className="border-t border-line/60">
                <td className="num px-2 py-2 text-ink-dim">
                  {pixel.lat.toFixed(2)}, {pixel.lon_ee.toFixed(2)}
                </td>
                <td className="px-2 py-2 text-ink-mute">{pixel.lat_band.replace(/_/g, " ")}</td>
                <td className="px-2 py-2 text-right">
                  <button
                    type="button"
                    onClick={() => onUsePixel(pixel)}
                    className="rounded-sm border border-cool/30 bg-cool/[0.08] px-2 py-1 text-[10.5px] font-medium text-ink hover:bg-cool/[0.14]"
                  >
                    Use
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-[10.5px] leading-relaxed text-ink-mute">
        The table lists the nearest valid inventory cells for the selected crop. Use a center point
        from this guide when testing the calculator.
      </p>
    </div>
  );
}

function ProbabilityPanel({ result, variable }: { result: PhaseCalculationResponse["result"] | null; variable: PhaseVariable }) {
  if (!result) {
    return (
      <div className="glass rounded-sm border border-line p-5">
        <p className="kicker">Historical probability</p>
        <div className="mt-5 grid min-h-[170px] place-items-center rounded-sm border border-dashed border-line bg-white/[0.015] text-center">
          <p className="max-w-[420px] text-[12.5px] leading-relaxed text-ink-dim">
            Configure the Earth Engine service account variables in Vercel and run a query to
            calculate event frequency for the selected coordinate, crop, phase and threshold.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="kicker">Historical probability</p>
          <div className="mt-3 flex items-end gap-3">
            <span className="num text-[54px] leading-none text-ink">{(result.probability * 100).toFixed(1)}%</span>
            <span className="pb-2 text-[12px] text-ink-dim">
              {result.event_years}/{result.valid_years} valid years
            </span>
          </div>
        </div>
        <div className="rounded-sm border border-line bg-white/[0.025] px-3 py-2 text-right">
          <p className="text-[11px] text-ink-mute">Critical years</p>
          <p className="num mt-1 text-[13px] text-warm">
            {(result.critical_years ?? result.years_critical ?? []).join(", ") || "None"}
          </p>
        </div>
      </div>
      <p className="mt-4 text-[11.5px] leading-relaxed text-ink-mute">
        Variable: {PHASE_VARIABLES.find((item) => item.id === variable)?.label ?? variable}. Annual metrics are
        calculated inside the selected phenological window only.
      </p>
    </div>
  );
}

function AnnualChart({
  annual,
  selectedYear,
  onSelectYear
}: {
  annual: AnnualPhaseMetric[];
  selectedYear: number;
  onSelectYear: (year: number) => void;
}) {
  const max = Math.max(1, ...annual.map((item) => item.n_exceedance_days));
  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="flex items-end justify-between gap-3 border-b border-line pb-3">
        <div>
          <p className="kicker">Annual chart</p>
          <h3 className="mt-1 text-[17px] font-medium text-ink">Critical days by year</h3>
        </div>
      </div>
      <div className="mt-4 h-[220px]">
        {annual.length ? (
          <svg viewBox="0 0 720 220" className="h-full w-full overflow-visible">
            {annual.map((item, index) => {
              const width = 720 / annual.length - 2;
              const height = (item.n_exceedance_days / max) * 170;
              const x = index * (720 / annual.length);
              const y = 185 - height;
              return (
                <g key={item.year}>
                  <rect
                    x={x}
                    y={y}
                    width={Math.max(4, width)}
                    height={height}
                    rx={1}
                    fill={item.event_occurred ? "var(--risk-high)" : "var(--accent-cool)"}
                    opacity={item.year === selectedYear ? 1 : item.event_occurred ? 0.9 : 0.45}
                    stroke={item.year === selectedYear ? "var(--accent-warm)" : "transparent"}
                    strokeWidth={item.year === selectedYear ? 2 : 0}
                    className="cursor-pointer"
                    onClick={() => onSelectYear(item.year)}
                  />
                  {index % 5 === 0 ? (
                    <text x={x} y={210} className="fill-ink-mute text-[10px]">
                      {item.year}
                    </text>
                  ) : null}
                </g>
              );
            })}
          </svg>
        ) : (
          <EmptyChart />
        )}
      </div>
    </div>
  );
}

function DailyChart({
  annual,
  daily,
  selectedYear,
  onYearChange,
  variable,
  threshold
}: {
  annual: AnnualPhaseMetric[];
  daily: { date: string; value: number | null; exceeds: boolean }[];
  selectedYear: number;
  onYearChange: (year: number) => void;
  variable: PhaseVariable;
  threshold: number;
}) {
  const values = daily.map((item) => item.value).filter((value): value is number => Number.isFinite(value));
  const min = values.length ? Math.min(...values) : 0;
  const max = values.length ? Math.max(...values) : 1;
  const span = Math.max(0.0001, max - min);
  const points = daily
    .map((item, index) => {
      if (item.value == null) return null;
      const x = daily.length > 1 ? (index / (daily.length - 1)) * 700 + 10 : 10;
      const y = 180 - ((item.value - min) / span) * 150;
      return `${x},${y}`;
    })
    .filter(Boolean)
    .join(" ");
  const thresholdY = Number.isFinite(threshold) ? 180 - ((threshold - min) / span) * 150 : null;

  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="flex flex-col gap-3 border-b border-line pb-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="kicker">Daily series</p>
          <h3 className="mt-1 text-[17px] font-medium text-ink">Zoom of selected annual bar</h3>
        </div>
        <select
          value={selectedYear}
          onChange={(event) => onYearChange(Number(event.target.value))}
          className={inputClass("h-9 w-full sm:w-32")}
        >
          {annual.map((item) => (
            <option key={item.year} value={item.year}>
              {item.year}
            </option>
          ))}
        </select>
      </div>
      <div className="mt-4 h-[210px]">
        {daily.length ? (
          <svg viewBox="0 0 720 210" className="h-full w-full overflow-visible">
            {thresholdY != null && thresholdY >= 20 && thresholdY <= 185 ? (
              <>
                <line x1="10" x2="710" y1={thresholdY} y2={thresholdY} stroke="var(--risk-high)" strokeDasharray="4 4" opacity="0.7" />
                <text x="650" y={thresholdY - 5} className="fill-ink-mute text-[10px]">
                  threshold
                </text>
              </>
            ) : null}
            <polyline fill="none" stroke="var(--accent-cool)" strokeWidth="2" points={points} />
            {daily.map((item, index) => {
              if (item.value == null || !item.exceeds) return null;
              const x = daily.length > 1 ? (index / (daily.length - 1)) * 700 + 10 : 10;
              const y = 180 - ((item.value - min) / span) * 150;
              return <circle key={`${item.date}-${index}`} cx={x} cy={y} r="2.5" fill="var(--risk-high)" />;
            })}
            <text x="10" y="16" className="fill-ink-mute text-[10px]">
              {PHASE_VARIABLES.find((item) => item.id === variable)?.unit ?? variable}
            </text>
          </svg>
        ) : (
          <EmptyChart />
        )}
      </div>
    </div>
  );
}

function SourcePanel() {
  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="border-b border-line pb-3">
        <p className="kicker">Source and method</p>
        <h3 className="mt-1 text-[17px] font-medium text-ink">ERA5-Land daily, queried on demand</h3>
      </div>
      <div className="mt-4 grid gap-3 text-[12px] leading-relaxed text-ink-dim md:grid-cols-2">
        <div className="rounded-sm border border-line bg-white/[0.02] p-3">
          <p className="font-medium text-ink">Dataset</p>
          <p className="mt-1">
            Google Earth Engine collection <span className="num text-ink">ECMWF/ERA5_LAND/DAILY_AGGR</span>,
            daily aggregates from ECMWF ERA5-Land reanalysis.
          </p>
          <a
            href="https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR"
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-block text-[11px] font-medium text-cool hover:text-ink"
          >
            Earth Engine Data Catalog
          </a>
        </div>
        <div className="rounded-sm border border-line bg-white/[0.02] p-3">
          <p className="font-medium text-ink">Resolution and scope</p>
          <p className="mt-1">
            Native pixel size is approximately <span className="num text-ink">11,132 m</span>. The
            calculator averages the selected variable over one GDHY-compatible 0.5 degree polygon.
          </p>
        </div>
        <div className="rounded-sm border border-line bg-white/[0.02] p-3">
          <p className="font-medium text-ink">Transformations</p>
          <p className="mt-1">
            Temperatures are converted from Kelvin to deg C, precipitation from meters to mm, and
            root-zone moisture is computed as swvl1*0.07 + swvl2*0.21 + swvl3*0.72.
          </p>
        </div>
        <div className="rounded-sm border border-line bg-white/[0.02] p-3">
          <p className="font-medium text-ink">Storage policy</p>
          <p className="mt-1">
            The app stores only pixel and calendar metadata. Daily values are requested from Earth
            Engine for one coordinate, phase, variable and historical period at a time.
          </p>
        </div>
      </div>
    </div>
  );
}

function AnnualTable({ annual, onExport }: { annual: AnnualPhaseMetric[]; onExport: () => void }) {
  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="flex items-end justify-between gap-3 border-b border-line pb-3">
        <div>
          <p className="kicker">Exportable table</p>
          <h3 className="mt-1 text-[17px] font-medium text-ink">Annual metrics</h3>
        </div>
        <button
          type="button"
          onClick={onExport}
          disabled={!annual.length}
          className="flex h-9 items-center gap-2 rounded-sm border border-line bg-white/[0.02] px-3 text-[12px] text-ink-dim hover:text-ink disabled:opacity-40"
        >
          <Download className="h-3.5 w-3.5" />
          CSV
        </button>
      </div>
      {annual.length ? (
        <div className="mt-4 max-h-[340px] overflow-auto">
          <table className="w-full min-w-[720px] border-collapse text-left text-[12px]">
            <thead className="sticky top-0 bg-bg-panel text-[10px] uppercase tracking-wider text-ink-mute">
              <tr>
                <Th>Year</Th>
                <Th>Days</Th>
                <Th>Critical</Th>
                <Th>Max</Th>
                <Th>Mean</Th>
                <Th>P95</Th>
                <Th>Max run</Th>
                <Th>Event</Th>
              </tr>
            </thead>
            <tbody>
              {annual.map((item) => (
                <tr key={item.year} className="border-b border-line/60">
                  <Td>{item.year}</Td>
                  <Td>{item.n_days}</Td>
                  <Td>{item.n_exceedance_days}</Td>
                  <Td>{formatMetric(item.max_value)}</Td>
                  <Td>{formatMetric(item.mean_value)}</Td>
                  <Td>{formatMetric(item.p95_value)}</Td>
                  <Td>{item.max_consecutive_exceedance_days}</Td>
                  <Td>{item.event_occurred ? "Yes" : "No"}</Td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="mt-4 grid h-[140px] place-items-center rounded-sm border border-dashed border-line bg-white/[0.015]">
          <div className="flex items-center gap-2 text-[12px] text-ink-dim">
            <Table2 className="h-4 w-4" />
            No annual metrics yet.
          </div>
        </div>
      )}
    </div>
  );
}

function StatusPanel({ tone, title, message }: { tone: "warn" | "error"; title: string; message: string }) {
  return (
    <div
      className={cn(
        "rounded-sm border p-4",
        tone === "warn" ? "border-warm/35 bg-warm/[0.08]" : "border-risk-high/35 bg-risk-high/[0.08]"
      )}
    >
      <div className="flex gap-3">
        <AlertTriangle className={cn("mt-0.5 h-4 w-4", tone === "warn" ? "text-warm" : "text-risk-high")} />
        <div>
          <p className="text-[13px] font-semibold text-ink">{title}</p>
          <p className="mt-1 text-[12px] leading-relaxed text-ink-dim">{message}</p>
        </div>
      </div>
    </div>
  );
}

function Segmented({
  options,
  value,
  onChange
}: {
  options: { id: string; label: string }[];
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="grid grid-cols-2 gap-2">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          onClick={() => onChange(option.id)}
          className={cn(
            "h-9 rounded-sm border px-3 text-[12px] font-medium transition-colors",
            value === option.id
              ? "border-cool/40 bg-cool/[0.08] text-ink"
              : "border-line bg-white/[0.02] text-ink-dim hover:text-ink"
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="grid gap-1.5">
      <span className="text-[10px] uppercase tracking-wider text-ink-mute">{label}</span>
      {children}
    </label>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span>{label}</span>
      <span className="num text-right text-ink">{value}</span>
    </div>
  );
}

function EmptyChart() {
  return (
    <div className="grid h-full place-items-center rounded-sm border border-dashed border-line bg-white/[0.015] text-[12px] text-ink-dim">
      Run a configured calculation to render this chart.
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return <th className="px-3 py-2 font-medium">{children}</th>;
}

function Td({ children }: { children: React.ReactNode }) {
  return <td className="num px-3 py-2 text-ink-dim">{children}</td>;
}

function inputClass(extra = "") {
  return cn(
    "h-10 rounded-sm border border-line bg-bg-panel px-3 text-[12.5px] text-ink outline-none transition-colors focus:border-cool/50",
    extra
  );
}

function parsePixelInventory(csv: string): PixelInventoryRow[] {
  const [headerLine, ...lines] = csv.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.filter(Boolean).map((line) => {
    const values = line.split(",");
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index]]));
    return {
      crop: row.crop as Crop,
      pixel_id_h5: Number(row.pixel_id_h5),
      lat_idx: Number(row.lat_idx),
      lon_idx: Number(row.lon_idx),
      lat: Number(row.lat),
      lon: Number(row.lon),
      lon_ee: Number(row.lon_ee),
      lat_band: row.lat_band,
      pixel_lat_min: Number(row.pixel_lat_min),
      pixel_lat_max: Number(row.pixel_lat_max),
      pixel_lon_min_ee: Number(row.pixel_lon_min_ee),
      pixel_lon_max_ee: Number(row.pixel_lon_max_ee)
    };
  });
}

function nearestPixel(pixels: PixelInventoryRow[], lat: number, lon: number) {
  let best: PixelInventoryRow | null = null;
  let bestDistance = Infinity;
  for (const pixel of pixels) {
    const distance = Math.hypot(pixel.lat - lat, pixel.lon_ee - lon);
    if (distance < bestDistance) {
      best = pixel;
      bestDistance = distance;
    }
  }
  return best;
}

function polygonLabel(pixel: PixelInventoryRow) {
  return `${pixel.pixel_lat_min.toFixed(2)}..${pixel.pixel_lat_max.toFixed(2)}, ${pixel.pixel_lon_min_ee.toFixed(2)}..${pixel.pixel_lon_max_ee.toFixed(2)}`;
}

function formatMetric(value: number | null) {
  return Number.isFinite(value) ? Number(value).toFixed(2) : "";
}

function normalizeResponse(
  data: PhaseCalculationResponse | PhaseCalculationResponse["result"] | undefined,
  request: PhaseCalculationRequest
): PhaseCalculationResponse {
  if (!data) {
    return {
      ok: false,
      configured: true,
      request,
      message: "Backend GEE did not return a calculation result."
    };
  }

  if ("ok" in data) {
    if (data.result?.years_critical && !data.result.critical_years) {
      data.result.critical_years = data.result.years_critical;
    }
    return data;
  }

  const result = data;
  if (result?.years_critical && !result.critical_years) {
    result.critical_years = result.years_critical;
  }
  return {
    ok: Boolean(result),
    configured: true,
    request,
    result: result ?? undefined,
    message: result ? undefined : "Backend GEE did not return a calculation result."
  };
}
