"use client";
import Papa from "papaparse";

export async function loadCsv<T>(path: string): Promise<T[]> {
  const res = await fetch(path, { cache: "force-cache" });
  if (!res.ok) throw new Error(`Could not load ${path} (${res.status})`);
  const text = await res.text();
  const parsed = Papa.parse<T>(text, {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: true
  });
  if (parsed.errors.length) {
    // Soft fail: keep good rows
    // eslint-disable-next-line no-console
    console.warn(`CSV parse warnings for ${path}:`, parsed.errors.slice(0, 3));
  }
  return parsed.data;
}
