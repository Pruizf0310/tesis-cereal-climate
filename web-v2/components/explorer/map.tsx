"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import maplibregl, {
  Map as MapLibreMap,
  MapMouseEvent,
  StyleSpecification
} from "maplibre-gl";
import { Minus, Plus } from "lucide-react";
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

const SVG_RISK_COLOR: Record<CropPoint["risk"], string> = {
  low: "#4D9C7C",
  moderate: "#E0B154",
  high: "#D97B45",
  extreme: "#B23D3D"
};

const WORLD_OUTLINES: { name: string; points: [number, number][] }[] = [
  {
    name: "north-america",
    points: [
      [-168, 71], [-145, 68], [-126, 53], [-124, 39], [-117, 31], [-101, 22],
      [-89, 18], [-80, 25], [-66, 45], [-54, 49], [-60, 58], [-92, 74],
      [-122, 72], [-168, 71]
    ]
  },
  {
    name: "south-america",
    points: [
      [-81, 12], [-68, 8], [-52, -7], [-44, -22], [-50, -39], [-65, -55],
      [-73, -42], [-79, -17], [-81, 12]
    ]
  },
  {
    name: "eurasia",
    points: [
      [-10, 36], [4, 58], [31, 70], [64, 63], [96, 70], [132, 54],
      [153, 47], [139, 31], [111, 23], [81, 8], [54, 22], [31, 31],
      [10, 36], [-10, 36]
    ]
  },
  {
    name: "africa",
    points: [
      [-17, 35], [9, 36], [33, 28], [51, 9], [42, -18], [28, -35],
      [14, -35], [-2, -18], [-16, 5], [-17, 35]
    ]
  },
  {
    name: "australia",
    points: [
      [112, -11], [133, -9], [154, -25], [146, -43], [122, -37], [112, -25],
      [112, -11]
    ]
  },
  {
    name: "greenland",
    points: [
      [-52, 60], [-31, 66], [-25, 78], [-46, 83], [-64, 76], [-52, 60]
    ]
  },
  {
    name: "madagascar",
    points: [
      [47, -13], [51, -21], [48, -26], [43, -21], [47, -13]
    ]
  }
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
    window.requestAnimationFrame(() => map.resize());
    window.setTimeout(() => map.resize(), 250);

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
          risk: f.properties.risk,
          climate: f.properties.climate ? JSON.parse(f.properties.climate) : undefined
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
          risk: f.properties.risk,
          climate: f.properties.climate ? JSON.parse(f.properties.climate) : undefined
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
            risk: p.risk,
            climate: p.climate ? JSON.stringify(p.climate) : ""
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

  return (
    <div className="absolute inset-0 z-[1]" aria-label="Global crop-risk map">
      <div ref={containerRef} className="absolute inset-0" />
      <PointSvgOverlay
        points={points}
        selected={selected}
        onHover={onHover}
        onSelect={onSelect}
      />
    </div>
  );
}

function projectPoint(point: CropPoint) {
  return projectLonLat(point.lon, point.lat);
}

function projectLonLat(lon: number, lat: number) {
  const x = ((lon + 180) / 360) * 1000;
  const y = ((90 - lat) / 180) * 500;
  return { x, y };
}

function PointSvgOverlay({
  points,
  selected,
  onHover,
  onSelect
}: {
  points: CropPoint[];
  selected: CropPoint | null;
  onHover: (point: CropPoint | null) => void;
  onSelect: (point: CropPoint | null) => void;
}) {
  const [zoom, setZoom] = useState(1);
  const center = useMemo(() => {
    if (selected && zoom > 1) return projectPoint(selected);
    return { x: 500, y: 250 };
  }, [selected, zoom]);
  const transform = `translate(500 250) scale(${zoom}) translate(${-center.x} ${-center.y})`;
  const pointRadius = Math.max(3.2 / zoom, 1.8);

  const zoomIn = () => setZoom((z) => Math.min(5, Number((z + 0.5).toFixed(1))));
  const zoomOut = () => setZoom((z) => Math.max(1, Number((z - 0.5).toFixed(1))));

  return (
    <>
      <svg
        viewBox="0 0 1000 500"
        preserveAspectRatio="xMidYMid meet"
        className="absolute inset-0 h-full w-full"
        role="img"
        aria-label="Projected crop pixels"
        onClick={() => onSelect(null)}
      >
        <defs>
          <radialGradient id="ocean-glow" cx="50%" cy="50%" r="65%">
            <stop offset="0%" stopColor="rgba(127,212,223,0.11)" />
            <stop offset="72%" stopColor="rgba(127,212,223,0.025)" />
            <stop offset="100%" stopColor="rgba(5,11,18,0)" />
          </radialGradient>
        </defs>
        <rect width="1000" height="500" fill="rgba(7,20,29,0.92)" pointerEvents="none" />
        <rect width="1000" height="500" fill="url(#ocean-glow)" pointerEvents="none" />
        <g transform={transform}>
          {Array.from({ length: 7 }, (_, i) => 125 + i * 125).map((x) => (
            <line key={`lon-${x}`} x1={x} x2={x} y1={0} y2={500} stroke="rgba(255,255,255,0.075)" />
          ))}
          {Array.from({ length: 5 }, (_, i) => 83.33 + i * 83.33).map((y) => (
            <line key={`lat-${y}`} x1={0} x2={1000} y1={y} y2={y} stroke="rgba(255,255,255,0.075)" />
          ))}
          {WORLD_OUTLINES.map((shape) => (
            <polygon
              key={shape.name}
              points={shape.points.map(([lon, lat]) => {
                const p = projectLonLat(lon, lat);
                return `${p.x},${p.y}`;
              }).join(" ")}
              fill="rgba(127,175,123,0.11)"
              stroke="rgba(230,238,242,0.58)"
              strokeWidth={1.8 / zoom}
              vectorEffect="non-scaling-stroke"
              pointerEvents="none"
            />
          ))}
          {points.map((point) => {
            const { x, y } = projectPoint(point);
            const selectedPoint = selected?.id === point.id;
            const radius = selectedPoint ? pointRadius + 2.8 / zoom : pointRadius;
            return (
              <circle
                key={point.id}
                cx={x}
                cy={y}
                r={radius}
                fill={SVG_RISK_COLOR[point.risk]}
                fillOpacity={selectedPoint ? 1 : 0.88}
                stroke={selectedPoint ? "#E6EEF2" : "rgba(255,255,255,0.58)"}
                strokeWidth={selectedPoint ? 1.4 / zoom : 0.55 / zoom}
                className="cursor-pointer transition-opacity hover:opacity-100"
                vectorEffect="non-scaling-stroke"
                onMouseEnter={() => onHover(point)}
                onMouseLeave={() => onHover(null)}
                onClick={(event) => {
                  event.stopPropagation();
                  onSelect(point);
                }}
              />
            );
          })}
        </g>
      </svg>
      <div className="absolute right-3 top-3 z-10 flex overflow-hidden rounded-sm border border-line bg-bg-panel/85 shadow-glass backdrop-blur-xs">
        <button
          type="button"
          onClick={zoomOut}
          className="flex h-8 w-8 items-center justify-center text-ink-dim transition hover:bg-white/[0.06] hover:text-ink"
          aria-label="Zoom out"
        >
          <Minus className="h-4 w-4" />
        </button>
        <div className="flex h-8 min-w-12 items-center justify-center border-x border-line px-2 text-[10.5px] text-ink-mute">
          {zoom.toFixed(1)}x
        </div>
        <button
          type="button"
          onClick={zoomIn}
          className="flex h-8 w-8 items-center justify-center text-ink-dim transition hover:bg-white/[0.06] hover:text-ink"
          aria-label="Zoom in"
        >
          <Plus className="h-4 w-4" />
        </button>
      </div>
    </>
  );
}
