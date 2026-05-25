import { NextResponse } from "next/server";
import { ensoState, type OniPoint, type SignalApiResponse, type OniData } from "@/lib/signals";

export const revalidate = 86400;

const SOURCE_URL = "https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php";
const EVENTS: OniData["events"] = [
  { label: "1982-83", start: 1982, end: 1983, type: "el" },
  { label: "1997-98", start: 1997, end: 1998, type: "el" },
  { label: "2010-11", start: 2010, end: 2011, type: "la" },
  { label: "2015-16", start: 2015, end: 2016, type: "el" },
  { label: "2023-24", start: 2023, end: 2024, type: "el" }
];

function parseOni(text: string): OniPoint[] {
  const plain = text
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/\s+/g, " ");
  const matches = [...plain.matchAll(/\b(DJF|JFM|FMA|MAM|AMJ|MJJ|JJA|JAS|ASO|SON|OND|NDJ)\s+(\d{4})\s+(-?\d+\.\d+)/g)];
  return matches.map((m) => ({
    season: m[1],
    year: Number(m[2]),
    value: Number(m[3])
  }));
}

export async function GET() {
  try {
    const response = await fetch(SOURCE_URL, { next: { revalidate } });
    if (!response.ok) throw new Error(`NOAA CPC responded ${response.status}`);
    const html = await response.text();
    const series = parseOni(html);
    if (!series.length) throw new Error("ONI table could not be parsed");
    const latest = series[series.length - 1];
    const body: SignalApiResponse<OniData> = {
      ok: true,
      signal: "oni",
      source: "NOAA CPC",
      sourceUrl: SOURCE_URL,
      lastUpdated: null,
      data: {
        current: { ...latest, state: ensoState(latest.value) },
        series,
        events: EVENTS
      }
    };
    return NextResponse.json(body);
  } catch (error) {
    const body: SignalApiResponse = {
      ok: false,
      signal: "oni",
      source: "NOAA CPC",
      sourceUrl: SOURCE_URL,
      error: "Official product unavailable or could not be parsed",
      fallbackUrl: SOURCE_URL
    };
    return NextResponse.json(body, { status: 200 });
  }
}
