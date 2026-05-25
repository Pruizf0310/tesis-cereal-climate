import { NextResponse } from "next/server";
import type { ProductImageData, SignalApiResponse } from "@/lib/signals";

export const revalidate = 21600;

const SOURCE_URL = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/whindex.shtml";
const IMAGE_URL = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/obs_phase40_small.gif";

export async function GET() {
  const body: SignalApiResponse<ProductImageData> = {
    ok: true,
    signal: "mjo",
    source: "NOAA CPC",
    sourceUrl: SOURCE_URL,
    lastUpdated: null,
    data: {
      imageUrl: IMAGE_URL,
      productUrl: SOURCE_URL,
      statusLabel: "Official RMM phase-space product",
      interpretativeLabel: "Active MJO outside unit circle; weak signal inside unit circle"
    }
  };
  return NextResponse.json(body);
}
