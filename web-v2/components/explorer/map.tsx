"use client";

import { useEffect, useRef } from "react";
import maplibregl, {
  Map as MapLibreMap,
  MapMouseEvent,
  StyleSpecification
} from "maplibre-gl";
import type { CropPoint } from "@/lib/types";

const MAP_STYLE: StyleSpecification = {
  version: 8,
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
  sources: {
    "carto-dark": {
      type: "raster",
      tiles: [
        "https://a.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
        "https://b.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
        "https://c.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png",
        "https://d.basemaps.cartocdn.com/dark_nolabels/{z}/{x}/{y}@2x.png"
      ],
      tileSize: 256,
      attribution: "© OpenStreetMap contributors · © CARTO"
    }
  },
  layers: [
    {
      id: "background",
      type: "background",
      paint: { "background-color": "#050B12" }
    },
    {
      id: "carto",
      type: "raster",
      source: "carto-dark",
      paint: {
        "raster-opacity": 0.55,
        "raster-contrast": 0.08,
        "raster-saturation": -0.45,
        "raster-brightness-min": 0.05,
        "raster-brightness-max": 0.85
      }
    }
  ]
};

const RISK_COLOR_EXPR: maplibregl.ExpressionSpecification = [
  "match",
  ["get", "risk"],
  "low",
  "#4D9C7C",
  "moderate",
  "#E0B154",
  "high",
  "#D97B45",
  "extreme",
  "#B23D3D",
  "#4D9C7C"
];

const RISK_RADIUS_EXPR: maplibregl.ExpressionSpecification = [
  "interpolate",
  ["linear"],
  ["zoom"],
  1,
  ["match", ["get", "risk"], "low", 2, "moderate", 2.4, "high", 2.8, "extreme", 3.2, 2],
  4,
  ["match", ["get", "risk"], "low", 3, "moderate", 3.8, "high", 4.6, "extreme", 5.4, 3],
  7,
  ["match", ["get", "risk"], "low", 5, "moderate", 6.5, "high", 8, "extreme", 10, 5]
];

interface MapViewProps {
  points: CropPoint[];
  onHover: (point: CropPoint | null) => void;
  onSelect: (point: CropPoint | null) => void;
  selected: CropPoint | null;
}

export function MapView({ points, onHover, onSelect, selected }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const readyRef = useRef(false);

  // Initialize once
  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [10, 18],
      zoom: 1.6,
      minZoom: 1.2,
      maxZoom: 7,
      pitch: 0,
      bearing: 0,
      attributionControl: { compact: true },
      renderWorldCopies: true,
      antialias: true
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

    map.on("load", () => {
      // Empty source — filled by the points effect
      map.addSource("crop-points", {
        type: "geojson",
        data: { type: "FeatureCollection", features: [] },
        cluster: false
      });

      // Soft halo glow layer behind the points
      map.addLayer({
        id: "crop-points-glow",
        type: "circle",
        source: "crop-points",
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1,
            ["match", ["get", "risk"], "low", 3, "moderate", 4, "high", 5, "extreme", 6, 3],
            7,
            ["match", ["get", "risk"], "low", 7, "moderate", 9, "high", 12, "extreme", 14, 7]
          ],
          "circle-color": RISK_COLOR_EXPR,
          "circle-opacity": 0.18,
          "circle-blur": 1
        }
      });

      // Main points
      map.addLayer({
        id: "crop-points-core",
        type: "circle",
        source: "crop-points",
        paint: {
          "circle-radius": RISK_RADIUS_EXPR,
          "circle-color": RISK_COLOR_EXPR,
          "circle-opacity": 0.92,
          "circle-stroke-width": 0.6,
          "circle-stroke-color": "rgba(255,255,255,0.6)",
          "circle-stroke-opacity": 0.5
        }
      });

      // Hover ring
      map.addLayer({
        id: "crop-points-hover",
        type: "circle",
        source: "crop-points",
        paint: {
          "circle-radius": [
            "interpolate",
            ["linear"],
            ["zoom"],
            1,
            6,
            7,
            14
          ],
          "circle-color": "transparent",
          "circle-stroke-width": 1.5,
          "circle-stroke-color": "#E6EEF2",
          "circle-stroke-opacity": 0.9
        },
        filter: ["==", ["get", "id"], "__none__"]
      });

      readyRef.current = true;

      // Hover interaction
      map.on("mousemove", "crop-points-core", (e: MapMouseEvent & { features?: any[] }) => {
        if (!e.features?.length) return;
        const f = e.features[0];
        map.getCanvas().style.cursor = "pointer";
        map.setFilter("crop-points-hover", ["==", ["get", "id"], f.properties.id]);
        onHover({
          id: f.properties.id,
          lat: f.properties.lat,
          lon: f.properties.lon,
          cluster: f.properties.cluster,
          std: f.properties.std,
          longestRun: f.properties.longestRun,
          yearsValid: f.properties.yearsValid,
          risk: f.properties.risk
        });
      });

      map.on("mouseleave", "crop-points-core", () => {
        map.getCanvas().style.cursor = "";
        map.setFilter("crop-points-hover", ["==", ["get", "id"], "__none__"]);
        onHover(null);
      });

      // Click to pin a selection
      map.on("click", "crop-points-core", (e: MapMouseEvent & { features?: any[] }) => {
        if (!e.features?.length) return;
        const f = e.features[0];
        onSelect({
          id: f.properties.id,
          lat: f.properties.lat,
          lon: f.properties.lon,
          cluster: f.properties.cluster,
          std: f.properties.std,
          longestRun: f.properties.longestRun,
          yearsValid: f.properties.yearsValid,
          risk: f.properties.risk
        });
      });

      // Click outside any point to clear selection
      map.on("click", (e: MapMouseEvent) => {
        const features = map.queryRenderedFeatures(e.point, { layers: ["crop-points-core"] });
        if (!features.length) onSelect(null);
      });
    });

    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
      readyRef.current = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update the points source whenever data changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    const update = () => {
      const src = map.getSource("crop-points") as maplibregl.GeoJSONSource | undefined;
      if (!src) return;
      src.setData({
        type: "FeatureCollection",
        features: points.map((p) => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: [p.lon, p.lat] },
          properties: {
            id: p.id,
            lat: p.lat,
            lon: p.lon,
            cluster: p.cluster,
            std: p.std,
            longestRun: p.longestRun,
            yearsValid: p.yearsValid,
            risk: p.risk
          }
        }))
      });
    };
    if (readyRef.current) update();
    else map.once("load", update);
  }, [points]);

  // Reflect selected as ring (persistent highlight)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !readyRef.current) return;
    if (!selected) return;
    // optional: smooth pan to selected
  }, [selected]);

  return <div ref={containerRef} className="absolute inset-0" aria-label="Global crop-risk map" />;
}
