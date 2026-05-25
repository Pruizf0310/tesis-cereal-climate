import { NextResponse } from "next/server";
import type { ProductImageData, SignalApiResponse } from "@/lib/signals";

export const revalidate = 21600;

const SOURCE_URL = "https://psl.noaa.gov/map/clim/olr.shtml";
const PRODUCT_URL = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/olra_last30days-3plots.gif";
const IMAGE_URL = "https://www.cpc.ncep.noaa.gov/products/precip/CWlink/MJO/olra_last30days-3plots_2.gif";

export async function GET() {
  const body: SignalApiResponse<ProductImageData> = {
    ok: true,
    signal: "olr",
    source: "NOAA PSL / CPC Blended OLR",
    sourceUrl: SOURCE_URL,
    lastUpdated: null,
    data: {
      imageUrl: IMAGE_URL,
      productUrl: PRODUCT_URL,
      statusLabel: "Official tropical convection product available",
      interpretativeLabel: "Negative OLR anomalies indicate enhanced convection; positive anomalies indicate suppressed convection"
    }
  };
  return NextResponse.json(body);
}
