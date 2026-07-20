"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Calculator, Download, Loader2, MapPin, Play, Table2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Crop } from "@/lib/types";
import { CROPS } from "@/lib/types";
import {
  PHASE_VARIABLES,
  csvEscape,
  latBandKeyFromInventory,
  type AnnualPhaseMetric,
  type CalendarBandWindow,
  type Phase,
  type PhaseCalculationRequest,
  type PhaseCalculationResponse,
  type PhaseCalendarWindows,
  type PhaseCriticalThreshold,
  type PhaseCriticalThresholds,
  type PhaseVariable,
  type PixelInventoryRow,
  type ThresholdOperator
} from "@/lib/phase-calculator";

const PHASES: Phase[] = ["F1", "F2", "F3"];
const DEFAULT_START_YEAR = "1981";
const DEFAULT_END_YEAR = "2016";
// Audited once against the production GEE endpoint: maize F2 had the
// <30 mm rolling 10-day trigger in 3 of 36 years (1981-2016).
const DEFAULT_EXAMPLE_PIXEL_ID = "3150";
const DEFAULT_EXAMPLE_LAT_BAND = "10_to_0";
const DEFAULT_EXAMPLE_TARGET = { lat: 5.25, lon: -75.25 };

type ApiState = "idle" | "loading" | "success" | "error";

interface DerivedContext {
  pixel: PixelInventoryRow | null;
  seasonId: string | null;
  seasonLabel: string | null;
  band: CalendarBandWindow | null;
  phaseWindow: CalendarBandWindow["phases"][Phase] | null;
}

interface FormState {
  crop: Crop;
  pixelId: string;
  phase: Phase;
  startYear: string;
  endYear: string;
}

const INITIAL_FORM: FormState = {
  crop: "maize",
  pixelId: DEFAULT_EXAMPLE_PIXEL_ID,
  phase: "F2",
  startYear: DEFAULT_START_YEAR,
  endYear: DEFAULT_END_YEAR
};

export function PhaseCalculatorBoard() {
  const [form, setForm] = useState<FormState>(INITIAL_FORM);
  const [pixels, setPixels] = useState<PixelInventoryRow[]>([]);
  const [calendar, setCalendar] = useState<PhaseCalendarWindows | null>(null);
  const [thresholds, setThresholds] = useState<PhaseCriticalThresholds | null>(null);
  const [latBandFilter, setLatBandFilter] = useState(DEFAULT_EXAMPLE_LAT_BAND);
  const [apiState, setApiState] = useState<ApiState>("idle");
  const [apiResponse, setApiResponse] = useState<PhaseCalculationResponse | null>(null);
  const [selectedYear, setSelectedYear] = useState<number>(2016);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [hasAutoSubmitted, setHasAutoSubmitted] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/data/phase_pixel_inventory.csv").then((res) => res.text()),
      fetch("/data/phase_calendar_windows.json").then((res) => res.json()),
      fetch("/data/phase_critical_thresholds.json").then((res) => res.json())
    ])
      .then(([csv, calendarData, thresholdData]) => {
        setPixels(parsePixelInventory(csv));
        setCalendar(calendarData);
        setThresholds(thresholdData);
      })
      .catch(() => setLoadError("Could not load public calculator metadata."));
  }, []);

  const cropPixels = useMemo(
    () => pixels.filter((pixel) => pixel.crop === form.crop).sort((a, b) => a.pixel_id_h5 - b.pixel_id_h5),
    [form.crop, pixels]
  );

  const latBands = useMemo(() => {
    const counts = new Map<string, number>();
    for (const pixel of cropPixels) counts.set(pixel.lat_band, (counts.get(pixel.lat_band) ?? 0) + 1);
    return [...counts.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [cropPixels]);

  const visiblePixels = useMemo(() => {
    const filtered = latBandFilter === "all" ? cropPixels : cropPixels.filter((pixel) => pixel.lat_band === latBandFilter);
    return filtered.slice(0, 250);
  }, [cropPixels, latBandFilter]);

  useEffect(() => {
    if (!cropPixels.length) {
      if (pixels.length) update("pixelId", "");
      return;
    }
    const current = cropPixels.some((pixel) => String(pixel.pixel_id_h5) === form.pixelId);
    if (!current) {
      const defaultPixel = pickDefaultPixel(form.crop, cropPixels);
      update("pixelId", String(defaultPixel.pixel_id_h5));
      if (form.crop === "maize") setLatBandFilter(defaultPixel.lat_band);
    }
  }, [cropPixels, form.pixelId]);

  useEffect(() => {
    if (form.crop !== "maize") setLatBandFilter("all");
    setApiResponse(null);
  }, [form.crop]);

  const selectedPixel = useMemo(
    () => cropPixels.find((pixel) => String(pixel.pixel_id_h5) === form.pixelId) ?? cropPixels[0] ?? null,
    [cropPixels, form.pixelId]
  );

  const threshold = thresholds?.crops[form.crop]?.phases?.[form.phase] ?? null;

  const derived = useMemo<DerivedContext>(() => {
    if (!selectedPixel) {
      return { pixel: null, seasonId: null, seasonLabel: null, band: null, phaseWindow: null };
    }

    const cropCalendar = calendar?.crops[form.crop];
    const firstSeason = cropCalendar ? Object.entries(cropCalendar.seasons)[0] : null;
    const bandId = latBandKeyFromInventory(selectedPixel.lat_band);
    const band = firstSeason ? firstSeason[1].bands[bandId] ?? null : null;
    const phaseWindow = band?.phases[form.phase] ?? null;

    return {
      pixel: selectedPixel,
      seasonId: firstSeason?.[0] ?? null,
      seasonLabel: firstSeason?.[1].label ?? null,
      band,
      phaseWindow
    };
  }, [calendar, form.crop, form.phase, selectedPixel]);

  const result = apiResponse?.result ?? null;
  const annual = result?.annual ?? [];
  const dailySeries = useMemo(() => {
    if (!result) return [];
    return annual.find((item) => item.year === selectedYear)?.daily_values ?? result.daily ?? [];
  }, [annual, result, selectedYear]);

  useEffect(() => {
    if (annual.length) setSelectedYear(annual[annual.length - 1].year);
  }, [annual]);

  async function submit() {
    if (!derived.pixel || !derived.phaseWindow) {
      fail("No compatible pixel or phenology window was found for this crop and phase.");
      return;
    }
    if (!threshold) {
      fail("No critical-variable metadata is available for this crop and phase.");
      return;
    }
    if (!threshold.variable || threshold.threshold == null) {
      fail(threshold.note ?? "This phase has a documented critical threshold, but it is not directly calculable with ERA5-Land.");
      return;
    }

    const request: PhaseCalculationRequest = {
      lat: derived.pixel.lat,
      lon: derived.pixel.lon_ee,
      crop: form.crop,
      phase: form.phase,
      variable: threshold.variable,
      threshold: threshold.threshold,
      operator: threshold.operator,
      aggregation: threshold.aggregation,
      window_days: threshold.window_days,
      min_days_event: threshold.min_days_event,
      start_year: Number(form.startYear),
      end_year: Number(form.endYear),
      pixel: derived.pixel,
      phase_window: derived.phaseWindow
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
      fail("No se pudo contactar el backend GEE de Vercel.", true);
    }
  }

  function fail(message: string, configured = true) {
    setApiResponse({ ok: false, configured, message });
    setApiState("error");
  }

  useEffect(() => {
    if (hasAutoSubmitted || apiState !== "idle" || !form.pixelId) return;
    if (form.crop !== "maize" || form.phase !== "F2") return;
    if (form.startYear !== DEFAULT_START_YEAR || form.endYear !== DEFAULT_END_YEAR) return;
    if (!derived.pixel || String(derived.pixel.pixel_id_h5) !== form.pixelId || !derived.phaseWindow) return;
    if (!threshold?.variable || threshold.threshold == null) return;

    setHasAutoSubmitted(true);
    void submit();
  }, [hasAutoSubmitted, apiState, form, derived.pixel, derived.phaseWindow, threshold]);

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
    anchor.download = `phase-calculator-${form.crop}-${form.phase}-${threshold?.variable ?? "variable"}.csv`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  if (loadError) return <StatusPanel tone="error" title="Metadata unavailable" message={loadError} />;

  return (
    <div className="mt-12 grid gap-6 xl:grid-cols-[440px_minmax(0,1fr)]">
      <section className="space-y-4">
        <div className="glass top-edge relative rounded-sm border border-line p-4 animate-fade-up">
          <div className="mb-5 flex items-start justify-between gap-3">
            <div>
              <p className="kicker">Query setup</p>
              <h2 className="mt-1 font-display text-[22px] font-medium tracking-tightest text-ink">
                Crop, valid pixel and phase
              </h2>
            </div>
            <Calculator className="h-5 w-5 text-cool" />
          </div>

          <div className="grid gap-4">
            <Field label="Crop">
              <Segmented options={CROPS} value={form.crop} onChange={(value) => update("crop", value as Crop)} />
            </Field>

            <div className="grid grid-cols-2 gap-3">
              <Field label="Latitude band">
                <select value={latBandFilter} onChange={(event) => setLatBandFilter(event.target.value)} className={inputClass()}>
                  <option value="all">All valid bands</option>
                  {latBands.map(([band, count]) => (
                    <option key={band} value={band}>
                      {band.replace(/_/g, " ")} ({count})
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Pixel">
                <select value={form.pixelId} onChange={(event) => update("pixelId", event.target.value)} className={inputClass()}>
                  {visiblePixels.map((pixel) => (
                    <option key={pixel.pixel_id_h5} value={pixel.pixel_id_h5}>
                      #{pixel.pixel_id_h5} | {pixel.lat.toFixed(2)}, {pixel.lon_ee.toFixed(2)}
                    </option>
                  ))}
                </select>
              </Field>
            </div>

            <Field label="Phase">
              <Segmented
                options={PHASES.map((phase) => ({ id: phase, label: phase }))}
                value={form.phase}
                onChange={(value) => update("phase", value as Phase)}
              />
            </Field>

            <CriticalVariableCard threshold={threshold} />

            <div className="grid grid-cols-2 gap-3">
              <Field label="Start year">
                <input value={form.startYear} onChange={(event) => update("startYear", event.target.value)} className={inputClass()} />
              </Field>
              <Field label="End year">
                <input value={form.endYear} onChange={(event) => update("endYear", event.target.value)} className={inputClass()} />
              </Field>
            </div>

            <button
              type="button"
              onClick={submit}
              disabled={apiState === "loading" || !derived.pixel || !threshold?.variable || threshold.threshold == null}
              className="mt-1 flex h-10 items-center justify-center gap-2 rounded-md border-none bg-teal-600 px-5 py-2.5 text-[12.5px] font-medium text-white transition-colors hover:bg-teal-700 disabled:cursor-not-allowed disabled:bg-[#4A7A66] disabled:text-[#A8C8BE]"
            >
              {apiState === "loading" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              Calculate historical trigger frequency
            </button>
          </div>

          <ExamplePreloadNote crop={form.crop} phase={form.phase} startYear={form.startYear} endYear={form.endYear} pixel={selectedPixel} />
          <PixelSummary derived={derived} />
          <PixelGuide
            crop={form.crop}
            cropPixels={cropPixels}
            visiblePixels={visiblePixels}
            selectedPixel={selectedPixel}
            onUsePixel={(pixel) => update("pixelId", String(pixel.pixel_id_h5))}
          />
        </div>

        <SourcePanel />
      </section>

      <section className="space-y-6">
        {apiResponse && !apiResponse.ok ? (
          <StatusPanel
            tone={apiResponse.configured ? "error" : "warn"}
            title={
              apiResponse.message?.startsWith("Backend GEE no configurado")
                ? "Backend GEE no configurado"
                : "No se pudo completar el cálculo"
            }
            message={apiResponse.message ?? "No calculation result was returned."}
          />
        ) : null}

        <ProbabilityPanel result={result} threshold={threshold} />
        <ProbabilityCurve annual={annual} threshold={threshold} />
        <AnnualChart annual={annual} selectedYear={selectedYear} onSelectYear={setSelectedYear} />
        <CriticalYearsPanel annual={annual} threshold={threshold} />
        <DailyChart
          annual={annual}
          daily={dailySeries}
          selectedYear={selectedYear}
          onYearChange={setSelectedYear}
          variable={threshold?.variable ?? "tmax_c"}
          threshold={threshold}
        />
        <AnnualTable annual={annual} onExport={exportCsv} />
      </section>
    </div>
  );

  function update<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((current) => ({ ...current, [key]: value }));
  }
}

function CriticalVariableCard({ threshold }: { threshold: PhaseCriticalThreshold | null }) {
  if (!threshold) {
    return <StatusPanel tone="warn" title="No critical threshold" message="This crop-phase combination does not have a configured critical variable yet." />;
  }

  return (
    <div className="rounded-sm border border-line bg-white/[0.025] p-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-[12px] font-medium text-ink">Audited scientific trigger</p>
          <p className="mt-1 text-[11px] text-ink-mute">{threshold.phase_label}</p>
        </div>
        <span className="rounded-sm border border-line bg-bg-panel px-2 py-1 text-[10px] uppercase tracking-wider text-ink-mute">
          {threshold.stress_type}
        </span>
      </div>
      <div className="mt-3 grid gap-2 text-[11.5px] text-ink-dim">
        <Metric label="Variable" value={threshold.variable_label} />
        <Metric
          label="GEE variable"
          value={threshold.variable ? `${threshold.variable} (${variableUnit(threshold.variable)})` : "Not available in ERA5-Land"}
        />
        <Metric
          label="Critical threshold"
          value={threshold.threshold == null ? threshold.threshold_text : `${threshold.operator} ${threshold.threshold} ${threshold.unit}`}
        />
        <Metric label="Evidence" value={threshold.evidence_type} />
        <Metric
          label="Aggregation"
          value={
            threshold.calculation_status === "provisional"
              ? aggregationLabel(threshold)
              : "Not calculable with the current evidence and ERA5-Land variables"
          }
        />
        <Metric
          label="Event rule"
          value={threshold.calculation_status === "provisional" ? `${threshold.min_days_event}+ critical observation(s) in phase` : "Disabled"}
        />
      </div>
      <p className="mt-3 text-[10.5px] leading-relaxed text-ink-mute">{threshold.threshold_text}</p>
      {threshold.note ? <p className="mt-2 text-[10.5px] leading-relaxed text-warm">{threshold.note}</p> : null}
      <a href={threshold.link} target="_blank" rel="noreferrer" className="mt-2 inline-block text-[11px] font-medium text-cool hover:text-ink">
        {threshold.source}
      </a>
    </div>
  );
}

function PixelSummary({ derived }: { derived: DerivedContext }) {
  if (!derived.pixel) return null;
  return (
    <div className="mt-5 rounded-sm border border-line bg-white/[0.025] p-3">
      <div className="flex items-center gap-2 text-[12px] font-medium text-ink">
        <MapPin className="h-3.5 w-3.5 text-warm" />
        Selected valid pixel
      </div>
      <div className="mt-3 grid gap-2 text-[11.5px] text-ink-dim">
        <Metric label="Inventory pixel" value={`#${derived.pixel.pixel_id_h5}`} />
        <Metric label="Cell center" value={`${derived.pixel.lat.toFixed(2)}, ${derived.pixel.lon_ee.toFixed(2)}`} />
        <Metric label="Latitude band" value={derived.pixel.lat_band.replace(/_/g, " ")} />
        <Metric
          label="Phase window"
          value={
            derived.phaseWindow
              ? `DOY ${derived.phaseWindow.start_doy}-${derived.phaseWindow.end_doy}${derived.phaseWindow.crosses_year ? " next year" : ""}`
              : "No F window"
          }
        />
        <Metric label="Cell polygon" value={polygonLabel(derived.pixel)} />
      </div>
    </div>
  );
}

function ExamplePreloadNote({
  crop,
  phase,
  startYear,
  endYear,
  pixel
}: {
  crop: Crop;
  phase: Phase;
  startYear: string;
  endYear: string;
  pixel: PixelInventoryRow | null;
}) {
  if (!pixel) return null;
  const cropLabel = CROPS.find((item) => item.id === crop)?.label ?? crop;
  return (
    <div className="mt-4 rounded-sm border border-line bg-white/[0.025] p-3 text-[11.5px] leading-relaxed text-ink-mute">
      <p>
        Example pre-loaded · {cropLabel} · {phase} · {pixel.lat.toFixed(2)}, {pixel.lon_ee.toFixed(2)} · {startYear}-{endYear}
      </p>
      <p>Change any parameter and recalculate to explore other locations.</p>
    </div>
  );
}

function PixelGuide({
  crop,
  cropPixels,
  visiblePixels,
  selectedPixel,
  onUsePixel
}: {
  crop: Crop;
  cropPixels: PixelInventoryRow[];
  visiblePixels: PixelInventoryRow[];
  selectedPixel: PixelInventoryRow | null;
  onUsePixel: (pixel: PixelInventoryRow) => void;
}) {
  return (
    <div className="mt-4 rounded-sm border border-line bg-white/[0.025] p-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[12px] font-medium text-ink">Valid pixel list</p>
          <p className="mt-1 text-[10.5px] text-ink-mute">
            Showing {visiblePixels.length.toLocaleString("en-US")} of {cropPixels.length.toLocaleString("en-US")} {crop} pixels
          </p>
        </div>
        <span className="num rounded-sm border border-line bg-bg-panel px-2 py-1 text-[10.5px] text-ink-dim">0.5 deg</span>
      </div>

      <div className="mt-3 max-h-[250px] overflow-auto rounded-sm border border-line/70">
        <table className="w-full border-collapse text-left text-[11px]">
          <thead className="sticky top-0 bg-bg-panel text-[9.5px] uppercase tracking-wider text-ink-mute">
            <tr>
              <th className="px-2 py-2 font-medium">Pixel</th>
              <th className="px-2 py-2 font-medium">Center</th>
              <th className="px-2 py-2 font-medium">Band</th>
              <th className="px-2 py-2 font-medium" />
            </tr>
          </thead>
          <tbody>
            {visiblePixels.map((pixel) => (
              <tr key={pixel.pixel_id_h5} className={cn("border-t border-line/60", selectedPixel?.pixel_id_h5 === pixel.pixel_id_h5 && "bg-cool/[0.08]")}>
                <td className="num px-2 py-2 text-ink">#{pixel.pixel_id_h5}</td>
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
        Select a row from the valid H5/GDHY-compatible inventory. The request sent to GEE uses only this pixel center and its 0.5 degree polygon.
      </p>
    </div>
  );
}

function ProbabilityPanel({ result, threshold }: { result: PhaseCalculationResponse["result"] | null; threshold: PhaseCriticalThreshold | null }) {
  if (!result) {
    return (
      <div className="glass rounded-sm border border-line p-5">
        <p className="kicker">Historical trigger frequency</p>
        <div className="mt-5 grid min-h-[170px] place-items-center rounded-sm border border-dashed border-line bg-white/[0.015] text-center">
          <p className="max-w-[440px] text-[12.5px] leading-relaxed text-ink-dim">
            Choose a crop, a valid pixel and a phenological phase. Calculations are enabled only for literature-aligned provisional triggers.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="kicker">Historical trigger frequency</p>
          <div className="mt-3 flex items-end gap-3">
            <span className="num text-[54px] leading-none text-ink">{(result.probability * 100).toFixed(1)}%</span>
            <span className="pb-2 text-[12px] text-ink-dim">
              {result.event_years}/{result.valid_years} valid years
            </span>
          </div>
        </div>
        <div className="rounded-sm border border-line bg-white/[0.025] px-3 py-2 text-right">
          <p className="text-[11px] text-ink-mute">Threshold used</p>
          <p className="num mt-1 text-[13px] text-warm">
            {threshold?.threshold != null ? `${threshold.operator} ${threshold.threshold} ${threshold.unit}` : "Unavailable"}
          </p>
        </div>
      </div>
      <p className="mt-4 text-[11.5px] leading-relaxed text-ink-mute">
        This is the fraction of valid years in which the operational trigger occurred inside the selected phenological window. It is not a probability of crop damage or yield loss.
      </p>
    </div>
  );
}

function ProbabilityCurve({ annual, threshold }: { annual: AnnualPhaseMetric[]; threshold: PhaseCriticalThreshold | null }) {
  const curve = useMemo(() => buildProbabilityCurve(annual, threshold), [annual, threshold]);
  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="border-b border-line pb-3">
        <p className="kicker">Sensitivity curve</p>
        <h3 className="mt-1 text-[17px] font-medium text-ink">Historical trigger frequency across thresholds</h3>
      </div>
      <div className="mt-4 h-[230px]">
        {curve.points.length ? (
          <svg viewBox="0 0 720 230" className="h-full w-full overflow-visible">
            <polyline fill="none" stroke="var(--accent-cool)" strokeWidth="2.2" points={curve.points.map((p) => `${p.x},${p.y}`).join(" ")} />
            {curve.marker ? (
              <>
                <line x1={curve.marker.x} x2={curve.marker.x} y1="28" y2="190" stroke="var(--accent-warm)" strokeDasharray="4 4" />
                <circle cx={curve.marker.x} cy={curve.marker.y} r="4" fill="var(--accent-warm)" />
              </>
            ) : null}
            <line x1="36" x2="700" y1="190" y2="190" stroke="var(--line)" />
            <line x1="36" x2="36" y1="28" y2="190" stroke="var(--line)" />
            <text x="36" y="214" className="fill-ink-mute text-[10px]">{curve.minLabel}</text>
            <text x="646" y="214" className="fill-ink-mute text-[10px]">{curve.maxLabel}</text>
            <text x="8" y="34" className="fill-ink-mute text-[10px]">100%</text>
            <text x="16" y="193" className="fill-ink-mute text-[10px]">0%</text>
          </svg>
        ) : (
          <EmptyChart />
        )}
      </div>
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
          <p className="kicker">Historical years</p>
          <h3 className="mt-1 text-[17px] font-medium text-ink">Critical observations by year in this pixel</h3>
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

function CriticalYearsPanel({ annual, threshold }: { annual: AnnualPhaseMetric[]; threshold: PhaseCriticalThreshold | null }) {
  const critical = annual.filter((item) => item.event_occurred);
  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="border-b border-line pb-3">
        <p className="kicker">Critical years</p>
        <h3 className="mt-1 text-[17px] font-medium text-ink">Historical event years in selected pixel</h3>
      </div>
      {annual.length ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {critical.length ? (
            critical.map((item) => (
              <span key={item.year} className="num rounded-sm border border-risk-high/30 bg-risk-high/[0.08] px-2 py-1 text-[12px] text-ink">
                {item.year} · {item.n_exceedance_days} observations
              </span>
            ))
          ) : (
            <p className="text-[12.5px] text-ink-dim">
              No critical years were detected with {threshold?.operator ?? ">"} {threshold?.threshold ?? ""} {threshold?.unit ?? ""}.
            </p>
          )}
        </div>
      ) : (
        <div className="mt-4 grid h-[120px] place-items-center rounded-sm border border-dashed border-line bg-white/[0.015] text-[12px] text-ink-dim">
          Run a calculation to list critical years.
        </div>
      )}
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
  threshold: PhaseCriticalThreshold | null;
}) {
  const values = daily.map((item) => item.value).filter((value): value is number => Number.isFinite(value));
  const thresholdValue = threshold?.threshold ?? NaN;
  const min = values.length ? Math.min(...values, Number.isFinite(thresholdValue) ? thresholdValue : values[0]) : 0;
  const max = values.length ? Math.max(...values, Number.isFinite(thresholdValue) ? thresholdValue : values[0]) : 1;
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
  const thresholdY = Number.isFinite(thresholdValue) ? 180 - ((thresholdValue - min) / span) * 150 : null;

  return (
    <div className="glass rounded-sm border border-line p-5">
      <div className="flex flex-col gap-3 border-b border-line pb-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="kicker">Evaluated series</p>
          <h3 className="mt-1 text-[17px] font-medium text-ink">Daily or rolling values inside selected phase</h3>
        </div>
        <select value={selectedYear} onChange={(event) => onYearChange(Number(event.target.value))} className={inputClass("h-9 w-full sm:w-32")}>
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
                <text x="650" y={thresholdY - 5} className="fill-ink-mute text-[10px]">threshold</text>
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
              {variableUnit(variable)}
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
        <p className="kicker">Static climate data source</p>
        <h3 className="mt-1 text-[17px] font-medium text-ink">ERA5-Land daily from Google Earth Engine</h3>
      </div>
      <div className="mt-4 grid gap-3 text-[12px] leading-relaxed text-ink-dim">
        <p>
          The local climate values are extracted on demand from <span className="num text-ink">ECMWF/ERA5_LAND/DAILY_AGGR</span>.
          The app sends one selected crop pixel, phase window, variable and threshold to the backend.
        </p>
        <p>
          Native pixel size is approximately <span className="num text-ink">11,132 m</span>. The query averages the selected ERA5-Land
          variable over the GDHY/SST-compatible 0.5 degree polygon around the selected pixel center.
        </p>
        <p>
          Conversions: temperature from Kelvin to deg C; precipitation from meters to mm; root-zone moisture as
          swvl1*0.07 + swvl2*0.21 + swvl3*0.72.
        </p>
        <a
          href="https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR"
          target="_blank"
          rel="noreferrer"
          className="inline-block text-[11px] font-medium text-cool hover:text-ink"
        >
          Earth Engine Data Catalog
        </a>
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
                <Th>Evaluated</Th>
                <Th>Critical obs.</Th>
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
    <div className={cn("rounded-sm border p-4", tone === "warn" ? "border-warm/35 bg-warm/[0.08]" : "border-risk-high/35 bg-risk-high/[0.08]")}>
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
    <div className="grid grid-cols-3 gap-2">
      {options.map((option) => (
        <button
          key={option.id}
          type="button"
          onClick={() => onChange(option.id)}
          className={cn(
            "h-9 rounded-sm border px-3 text-[12px] font-medium transition-colors",
            value === option.id ? "border-cool/40 bg-cool/[0.08] text-ink" : "border-line bg-white/[0.02] text-ink-dim hover:text-ink"
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
  return cn("h-10 rounded-sm border border-line bg-bg-panel px-3 text-[12.5px] text-ink outline-none transition-colors focus:border-cool/50", extra);
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

function pickDefaultPixel(crop: Crop, pixels: PixelInventoryRow[]) {
  if (crop !== "maize") return pixels[0];
  const tropicalPixels = pixels.filter((pixel) => pixel.lat >= -15 && pixel.lat <= 15);
  const candidates = tropicalPixels.length ? tropicalPixels : pixels;
  return candidates.reduce((best, pixel) => {
    const bestDistance = pixelDistance(best);
    const pixelDistanceValue = pixelDistance(pixel);
    if (pixelDistanceValue < bestDistance) return pixel;
    if (pixelDistanceValue === bestDistance && pixel.pixel_id_h5 < best.pixel_id_h5) return pixel;
    return best;
  }, candidates[0]);
}

function pixelDistance(pixel: PixelInventoryRow) {
  return Math.pow(pixel.lat - DEFAULT_EXAMPLE_TARGET.lat, 2) + Math.pow(pixel.lon_ee - DEFAULT_EXAMPLE_TARGET.lon, 2);
}

function polygonLabel(pixel: PixelInventoryRow) {
  return `${pixel.pixel_lat_min.toFixed(2)}..${pixel.pixel_lat_max.toFixed(2)}, ${pixel.pixel_lon_min_ee.toFixed(2)}..${pixel.pixel_lon_max_ee.toFixed(2)}`;
}

function formatMetric(value: number | null) {
  return Number.isFinite(value) ? Number(value).toFixed(2) : "";
}

function variableUnit(variable: PhaseVariable) {
  return PHASE_VARIABLES.find((item) => item.id === variable)?.unit ?? variable;
}

function aggregationLabel(threshold: PhaseCriticalThreshold) {
  if (threshold.aggregation === "rolling_sum") return `Rolling ${threshold.window_days}-day sum`;
  if (threshold.aggregation === "rolling_mean") return `Rolling ${threshold.window_days}-day mean`;
  return "Daily observation";
}

function compare(value: number | null, threshold: number, operator: ThresholdOperator) {
  if (value == null || !Number.isFinite(value)) return false;
  if (operator === "<") return value < threshold;
  if (operator === "<=") return value <= threshold;
  if (operator === ">=") return value >= threshold;
  return value > threshold;
}

function buildProbabilityCurve(annual: AnnualPhaseMetric[], threshold: PhaseCriticalThreshold | null) {
  if (!annual.length || !threshold?.variable || threshold.threshold == null) {
    return { points: [], marker: null, minLabel: "", maxLabel: "" };
  }

  const values = annual.flatMap((year) =>
    (year.daily_values ?? []).map((daily) => daily.value).filter((value): value is number => Number.isFinite(value))
  );
  if (!values.length) return { points: [], marker: null, minLabel: "", maxLabel: "" };

  const min = Math.min(...values, threshold.threshold);
  const max = Math.max(...values, threshold.threshold);
  const span = Math.max(0.0001, max - min);
  const candidates = Array.from({ length: 40 }, (_, index) => min + (span * index) / 39);
  const points = candidates.map((candidate) => {
    const eventYears = annual.filter((year) => {
      const daily = year.daily_values ?? [];
      const n = daily.filter((item) => compare(item.value, candidate, threshold.operator)).length;
      return n >= threshold.min_days_event;
    }).length;
    const probability = annual.length ? eventYears / annual.length : 0;
    return {
      threshold: candidate,
      probability,
      x: 36 + ((candidate - min) / span) * 664,
      y: 190 - probability * 162
    };
  });

  const markerProbability = points.reduce((best, point) =>
    Math.abs(point.threshold - threshold.threshold!) < Math.abs(best.threshold - threshold.threshold!) ? point : best
  );

  return {
    points,
    marker: { x: 36 + ((threshold.threshold - min) / span) * 664, y: markerProbability.y },
    minLabel: `${min.toFixed(1)} ${threshold.unit}`,
    maxLabel: `${max.toFixed(1)} ${threshold.unit}`
  };
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
    if (data.result?.years_critical && !data.result.critical_years) data.result.critical_years = data.result.years_critical;
    return data;
  }

  const result = data;
  if (result?.years_critical && !result.critical_years) result.critical_years = result.years_critical;
  return {
    ok: Boolean(result),
    configured: true,
    request,
    result: result ?? undefined,
    message: result ? undefined : "Backend GEE did not return a calculation result."
  };
}
