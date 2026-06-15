from __future__ import annotations

import json
import math
import os
from datetime import date, timedelta
from pathlib import Path
from statistics import mean
from typing import Any, Literal

import ee
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


DATASET = "ECMWF/ERA5_LAND/DAILY_AGGR"
CALENDAR_PATH = Path(os.getenv("PHASE_CALENDAR_PATH", "data/phase_calendar_windows.json"))
ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")

Variable = Literal["tmax_c", "tmean_c", "tmin_c", "precip_mm", "swvl1", "swvl2", "swvl3", "rootzone_sm"]
Phase = Literal["F1", "F2", "F3"]
Crop = Literal["maize", "rice", "wheat", "soybean"]


class PhaseRiskRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-360, le=360)
    crop: Crop
    phase: Phase
    variable: Variable
    threshold: float
    start_year: int = Field(default=1981, ge=1981, le=2016)
    end_year: int = Field(default=2016, ge=1981, le=2016)
    min_days_event: int = Field(default=1, ge=1, le=366)


app = FastAPI(title="CerealRisk GEE phase calculator", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ALLOWED_ORIGIN] if ALLOWED_ORIGIN != "*" else ["*"],
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

_calendar: dict[str, Any] | None = None
_ee_initialized = False


def wrap_lon_180(lon: float) -> float:
    return ((lon + 180) % 360) - 180


def lat_band_id(lat: float) -> str:
    upper = math.ceil(lat / 10) * 10
    if lat == upper:
        upper += 10
    lower = upper - 10
    return f"{upper}_{lower}"


def doy_to_date(year: int, doy: int) -> date:
    return date(year, 1, 1) + timedelta(days=doy - 1)


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lower = math.floor(pos)
    upper = math.ceil(pos)
    if lower == upper:
        return ordered[int(pos)]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (pos - lower)


def max_consecutive(flags: list[bool]) -> int:
    best = 0
    current = 0
    for flag in flags:
        if flag:
            current += 1
            best = max(best, current)
        else:
            current = 0
    return best


def load_calendar() -> dict[str, Any]:
    global _calendar
    if _calendar is None:
        if not CALENDAR_PATH.exists():
            raise RuntimeError(f"Phase calendar file not found: {CALENDAR_PATH}")
        _calendar = json.loads(CALENDAR_PATH.read_text(encoding="utf-8"))
    return _calendar


def find_phase_window(crop: Crop, lat: float, phase: Phase) -> dict[str, Any]:
    calendar = load_calendar()
    crop_calendar = calendar.get("crops", {}).get(crop)
    if not crop_calendar:
        raise HTTPException(status_code=422, detail=f"No calendar available for crop={crop}")

    seasons = crop_calendar.get("seasons", {})
    if not seasons:
        raise HTTPException(status_code=422, detail=f"No phenology seasons available for crop={crop}")

    # Use the first typical season, matching the current web-v2 risk calendar behavior.
    season = next(iter(seasons.values()))
    bands = season.get("bands", {})
    band = bands.get(lat_band_id(lat))
    if band is None:
        band = next(
            (
                item
                for item in bands.values()
                if lat >= min(item["latMin"], item["latMax"]) and lat < max(item["latMin"], item["latMax"])
            ),
            None,
        )
    if band is None:
        raise HTTPException(status_code=422, detail=f"No latitude band found for lat={lat}")

    window = band.get("phases", {}).get(phase)
    if not window:
        raise HTTPException(status_code=422, detail=f"No {phase} window for crop={crop} at lat={lat}")

    return {
        **window,
        "lat_band": band.get("latBand"),
        "lat_band_id": lat_band_id(lat),
    }


def initialize_ee() -> None:
    global _ee_initialized
    if _ee_initialized:
        return

    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    service_account = os.getenv("GEE_SERVICE_ACCOUNT_EMAIL")
    private_key = os.getenv("GEE_SERVICE_ACCOUNT_PRIVATE_KEY")
    if not project or not service_account or not private_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "GEE backend is not configured. Set GOOGLE_CLOUD_PROJECT, "
                "GEE_SERVICE_ACCOUNT_EMAIL and GEE_SERVICE_ACCOUNT_PRIVATE_KEY."
            ),
        )

    private_key = private_key.replace("\\n", "\n")
    credentials = ee.ServiceAccountCredentials(
        service_account,
        key_data=json.dumps(
            {
                "type": "service_account",
                "project_id": project,
                "private_key_id": os.getenv("GEE_SERVICE_ACCOUNT_PRIVATE_KEY_ID", ""),
                "private_key": private_key,
                "client_email": service_account,
                "client_id": os.getenv("GEE_SERVICE_ACCOUNT_CLIENT_ID", ""),
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{service_account}",
            }
        ),
    )
    ee.Initialize(credentials, project=project)
    _ee_initialized = True


def variable_image(image: ee.Image, variable: str) -> ee.Image:
    if variable == "tmax_c":
        return image.select("temperature_2m_max").subtract(273.15).rename("value")
    if variable == "tmean_c":
        return image.select("temperature_2m").subtract(273.15).rename("value")
    if variable == "tmin_c":
        return image.select("temperature_2m_min").subtract(273.15).rename("value")
    if variable == "precip_mm":
        return image.select("total_precipitation_sum").multiply(1000).rename("value")
    if variable == "swvl1":
        return image.select("volumetric_soil_water_layer_1").rename("value")
    if variable == "swvl2":
        return image.select("volumetric_soil_water_layer_2").rename("value")
    if variable == "swvl3":
        return image.select("volumetric_soil_water_layer_3").rename("value")
    if variable == "rootzone_sm":
        return (
            image.select("volumetric_soil_water_layer_1").multiply(0.07)
            .add(image.select("volumetric_soil_water_layer_2").multiply(0.21))
            .add(image.select("volumetric_soil_water_layer_3").multiply(0.72))
            .rename("value")
        )
    raise HTTPException(status_code=422, detail=f"Unsupported variable: {variable}")


def query_daily_values(geometry: ee.Geometry, start: date, end_exclusive: date, variable: str) -> list[dict[str, Any]]:
    collection = ee.ImageCollection(DATASET).filterDate(start.isoformat(), end_exclusive.isoformat())

    def reduce_image(image: ee.Image) -> ee.Feature:
        value = variable_image(image, variable).reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=11132,
            bestEffort=True,
            maxPixels=1000000,
        ).get("value")
        return ee.Feature(
            None,
            {
                "date": image.date().format("YYYY-MM-dd"),
                "doy": image.date().getRelative("day", "year").add(1),
                "value": value,
            },
        )

    features = collection.map(reduce_image).getInfo().get("features", [])
    return [feature.get("properties", {}) for feature in features]


def annual_metrics(year: int, daily: list[dict[str, Any]], threshold: float, min_days_event: int) -> dict[str, Any]:
    values = [float(item["value"]) for item in daily if item.get("value") is not None]
    enriched = []
    flags = []
    for item in daily:
        value = item.get("value")
        exceeds = value is not None and float(value) > threshold
        flags.append(exceeds)
        enriched.append(
            {
                "date": item.get("date"),
                "doy": int(item.get("doy")) if item.get("doy") is not None else None,
                "value": float(value) if value is not None else None,
                "exceeds": exceeds,
            }
        )

    n_exceedance_days = sum(flags)
    run = max_consecutive(flags)
    return {
        "year": year,
        "n_days": len(values),
        "n_exceedance_days": n_exceedance_days,
        "max_value": max(values) if values else None,
        "mean_value": mean(values) if values else None,
        "p95_value": percentile(values, 0.95),
        "max_consecutive_exceedance_days": run,
        "event_occurred": n_exceedance_days >= min_days_event,
        "daily_values": enriched,
    }


@app.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True, "gee_configured": bool(os.getenv("GEE_SERVICE_ACCOUNT_EMAIL"))}


@app.post("/calculate-phase-risk")
def calculate_phase_risk(payload: PhaseRiskRequest) -> dict[str, Any]:
    if payload.start_year > payload.end_year:
        raise HTTPException(status_code=422, detail="start_year must be <= end_year")

    initialize_ee()

    lon = wrap_lon_180(payload.lon)
    geometry = ee.Geometry.Rectangle([lon - 0.25, payload.lat - 0.25, lon + 0.25, payload.lat + 0.25])
    phase_window = find_phase_window(payload.crop, payload.lat, payload.phase)

    annual = []
    for year in range(payload.start_year, payload.end_year + 1):
        start = doy_to_date(year, int(phase_window["start_doy"]))
        end_year = year + 1 if phase_window.get("crosses_year") else year
        end = doy_to_date(end_year, int(phase_window["end_doy"])) + timedelta(days=1)
        daily = query_daily_values(geometry, start, end, payload.variable)
        annual.append(annual_metrics(year, daily, payload.threshold, payload.min_days_event))

    valid_years = sum(1 for item in annual if item["n_days"] > 0)
    critical_years = [item["year"] for item in annual if item["n_days"] > 0 and item["event_occurred"]]
    event_years = len(critical_years)
    probability = event_years / valid_years if valid_years else 0

    return {
        "ok": True,
        "configured": True,
        "request": payload.model_dump(),
        "result": {
            "probability": probability,
            "event_years": event_years,
            "valid_years": valid_years,
            "critical_years": critical_years,
            "years_critical": critical_years,
            "annual": annual,
            "daily": annual[-1]["daily_values"] if annual else [],
            "source": DATASET,
            "phase_window": phase_window,
            "geometry": {
                "lat_min": payload.lat - 0.25,
                "lat_max": payload.lat + 0.25,
                "lon_min": lon - 0.25,
                "lon_max": lon + 0.25,
            },
        },
    }
