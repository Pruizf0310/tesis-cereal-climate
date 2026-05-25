import { NextResponse } from "next/server";
import type { ProductImageData, SignalApiResponse } from "@/lib/signals";

export const revalidate = 21600;

const SOURCE_URL = "https://www.ospo.noaa.gov/products/ocean/sst/anomaly/index.html";
const IMAGE_URL = "https://www.ospo.noaa.gov/data/cb/ssta/ssta.daily.current.png";

export async function GET() {
  const body: SignalApiResponse<ProductImageData> = {
    ok: true,
    signal: "sst",
    source: "NOAA OSPO / Coral Reef Watch",
    sourceUrl: SOURCE_URL,
    lastUpdated: null,
    data: {
      imageUrl: IMAGE_URL,
      productUrl: SOURCE_URL,
      statusLabel: "Official SST anomaly map available",
      interpretativeLabel: "Oceanic forcing field for ENSO and related teleconnection fingerprints"
    }
  };
  return NextResponse.json(body);
}
