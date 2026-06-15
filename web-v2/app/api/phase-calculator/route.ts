import { NextResponse } from "next/server";
import type { PhaseCalculationRequest, PhaseCalculationResponse } from "@/lib/phase-calculator";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const GEE_ENDPOINT_URL = process.env.GEE_ENDPOINT_URL;
const GEE_ENDPOINT_API_KEY = process.env.GEE_ENDPOINT_API_KEY;

function isFiniteNumber(value: unknown): value is number {
  return typeof value === "number" && Number.isFinite(value);
}

function validateRequest(body: Partial<PhaseCalculationRequest>): string | null {
  if (!isFiniteNumber(body.lat) || body.lat < -90 || body.lat > 90) return "lat must be a number between -90 and 90";
  if (!isFiniteNumber(body.lon) || body.lon < -360 || body.lon > 360) return "lon must be a number between -360 and 360";
  if (!body.crop) return "crop is required";
  if (!body.phase) return "phase is required";
  if (!body.variable) return "variable is required";
  if (!isFiniteNumber(body.threshold)) return "threshold must be numeric";
  if (!body.event_rule) return "event_rule is required";
  if (typeof body.start_year !== "number" || typeof body.end_year !== "number") {
    return "start_year and end_year are required";
  }
  if (!Number.isInteger(body.start_year) || !Number.isInteger(body.end_year)) return "start_year and end_year must be integers";
  if (body.start_year < 1981 || body.end_year > 2016 || body.start_year > body.end_year) {
    return "year range must be within 1981-2016";
  }
  if (!body.phase_window) return "phase_window is required";
  if (!body.pixel) return "pixel is required";
  return null;
}

export async function GET() {
  const configured = Boolean(GEE_ENDPOINT_URL);
  const body: PhaseCalculationResponse = {
    ok: configured,
    configured,
    message: configured
      ? "Phase calculator API is configured to proxy one-pixel GEE requests."
      : "GEE is not configured. Set GEE_ENDPOINT_URL to a Cloud Function or Cloud Run service."
  };
  return NextResponse.json(body, { status: 200 });
}

export async function POST(request: Request) {
  let payload: PhaseCalculationRequest;

  try {
    payload = await request.json();
  } catch {
    return NextResponse.json<PhaseCalculationResponse>(
      { ok: false, configured: Boolean(GEE_ENDPOINT_URL), message: "Request body must be valid JSON." },
      { status: 400 }
    );
  }

  const validationError = validateRequest(payload);
  if (validationError) {
    return NextResponse.json<PhaseCalculationResponse>(
      { ok: false, configured: Boolean(GEE_ENDPOINT_URL), message: validationError, request: payload },
      { status: 400 }
    );
  }

  if (!GEE_ENDPOINT_URL) {
    return NextResponse.json<PhaseCalculationResponse>({
      ok: false,
      configured: false,
      request: payload,
      message:
        "GEE is not configured for this deployment. The request was prepared but no daily series was queried. Configure GEE_ENDPOINT_URL to enable one-pixel, one-phase calculations."
    });
  }

  try {
    const upstream = await fetch(GEE_ENDPOINT_URL, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        ...(GEE_ENDPOINT_API_KEY ? { authorization: `Bearer ${GEE_ENDPOINT_API_KEY}` } : {})
      },
      body: JSON.stringify(payload),
      cache: "no-store"
    });

    const contentType = upstream.headers.get("content-type") ?? "";
    const data = contentType.includes("application/json") ? await upstream.json() : await upstream.text();

    if (!upstream.ok) {
      return NextResponse.json<PhaseCalculationResponse>(
        {
          ok: false,
          configured: true,
          request: payload,
          message: `Configured GEE endpoint responded ${upstream.status}.`,
          details: data
        },
        { status: 502 }
      );
    }

    return NextResponse.json<PhaseCalculationResponse>({
      ok: true,
      configured: true,
      request: payload,
      result: data.result ?? data
    });
  } catch (error) {
    return NextResponse.json<PhaseCalculationResponse>(
      {
        ok: false,
        configured: true,
        request: payload,
        message: "Could not reach the configured GEE endpoint.",
        details: error instanceof Error ? error.message : String(error)
      },
      { status: 502 }
    );
  }
}
