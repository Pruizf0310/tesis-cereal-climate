const cropLabels = { rice: "Arroz", maize: "Maíz", wheat: "Trigo", soybean: "Soya" };
const cropFiles = {
  rice: "../outputs/web/rice_puntos_utiles_interseccion.csv",
  maize: "../outputs/web/maize_puntos_utiles_interseccion.csv",
  wheat: "../outputs/web/wheat_puntos_utiles_interseccion.csv",
  soybean: "../outputs/web/soybean_puntos_utiles_interseccion.csv"
};
const signalLabels = { ONI: "ENSO / ONI", RMM: "MJO / RMM", SST: "SST correlation" };
const triggerSteps = [
  ["Clima observado", "ENSO/MJO/SST como señal monitoreable."],
  ["Cultivo expuesto", "Cereal y zona agrícola seleccionada."],
  ["Fase sensible", "Ventana fenológica por conectar con GEOGLAM."],
  ["Anomalía", "Respuesta de rendimiento pendiente de validación."],
  ["Trigger", "Candidato paramétrico, no definitivo."]
];
let map;
let pointLayer;
let demoLayer;
let rowsByCrop = [];
function parseCsv(text) {
  const [headerLine, ...lines] = text.trim().split(/\r?\n/);
  const headers = headerLine.split(",");
  return lines.filter(Boolean).map(line => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((h, index) => [h, values[index] ?? ""]));
  });
}
function riskClass(row) {
  const std = Number(row.std);
  if (Number.isFinite(std) && std >= 1.35) return "extreme";
  if (Number.isFinite(std) && std >= 1) return "high";
  if (Number.isFinite(std) && std >= 0.55) return "moderate";
  return "low";
}
function riskLabel(value) {
  return { low: "Bajo", moderate: "Moderado", high: "Alto", extreme: "Extremo", all: "Demo" }[value] || "Demo";
}
function formatCoord(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(2) : "sin dato";
}
function updateStaticReadout(crop) {
  const phase = document.getElementById("phaseSelect").value;
  const signal = document.getElementById("signalSelect").value;
  const risk = document.getElementById("riskSelect").value;
  document.getElementById("cropValue").textContent = cropLabels[crop];
  document.getElementById("phaseValue").textContent = phase;
  document.getElementById("signalValue").textContent = signalLabels[signal];
  document.getElementById("riskValue").textContent = riskLabel(risk);
}
function updateInsightFromRow(row, crop) {
  const phase = document.getElementById("phaseSelect").value;
  const signal = document.getElementById("signalSelect").value;
  const risk = riskClass(row);
  document.getElementById("zoneTitle").textContent = `Pixel agrícola seleccionado`;
  document.getElementById("zoneValue").textContent = `lat ${formatCoord(row.lat)}, lon ${formatCoord(row.lon)}`;
  document.getElementById("cropValue").textContent = cropLabels[crop];
  document.getElementById("phaseValue").textContent = phase;
  document.getElementById("signalValue").textContent = signalLabels[signal];
  document.getElementById("climateValue").textContent = signal === "ONI" ? "ONI por conectar" : signal === "RMM" ? "RMM por conectar" : "SST por conectar";
  document.getElementById("sensitivityValue").textContent = `Clase ${row.cluster || "sin dato"} · demo`;
  document.getElementById("anomalyValue").textContent = "Pendiente de validación";
  document.getElementById("riskValue").textContent = `${riskLabel(risk)} · demo`;
  document.getElementById("triggerCard").querySelector("strong").textContent = `${signalLabels[signal]} > umbral por validar durante ${phase.toLowerCase()}`;
}
function markerFor(row, crop) {
  const risk = riskClass(row);
  const radius = { low: 6, moderate: 8, high: 10, extreme: 12 }[risk];
  return L.circleMarker([Number(row.lat), Number(row.lon)], {
    radius,
    className: `risk-marker risk-${risk}`,
    color: "rgba(255,255,255,0.82)",
    weight: 1,
    fillOpacity: risk === "low" ? 0.5 : 0.76
  }).on("click", () => updateInsightFromRow(row, crop));
}
function initMap() {
  if (!window.L) {
    document.getElementById("mapFallback").hidden = false;
    document.getElementById("mapStatus").textContent = "demo";
    return false;
  }
  map = L.map("map", { minZoom: 2, maxZoom: 7, worldCopyJump: true, preferCanvas: true }).setView([12, -35], 2);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 7 }).addTo(map);
  demoLayer = L.layerGroup().addTo(map);
  pointLayer = L.layerGroup().addTo(map);
  // TODO: conectar aquí GeoJSON/tiles reales desde /outputs/web_ready o /web/data.
  const demoZones = [
    [[-18, -82], [10, -34], "ENSO/SST demo", "#d98232"],
    [[6, 58], [32, 124], "MJO/fenología demo", "#f1c75b"],
    [[-36, 108], [-9, 154], "hotspot demo", "#b44335"],
    [[32, -104], [49, -76], "zona agrícola demo", "#55a870"]
  ];
  demoZones.forEach(([a, b, label, color]) => L.rectangle([a, b], { color, weight: 1, fillColor: color, fillOpacity: 0.15 }).bindTooltip(label).addTo(demoLayer));
  map.on("zoomend moveend", () => {
    document.getElementById("mapSubtitle").textContent = "Explora, haz zoom y selecciona puntos agrícolas. Capas demo no son resultados finales.";
  });
  return true;
}
async function loadCrop(crop) {
  updateStaticReadout(crop);
  document.getElementById("mapTitle").textContent = `${cropLabels[crop]} · crop-risk layer`;
  document.getElementById("mapStatus").textContent = "loading";
  if (!pointLayer) return;
  pointLayer.clearLayers();
  try {
    const response = await fetch(cropFiles[crop]);
    if (!response.ok) throw new Error("CSV no disponible");
    rowsByCrop = parseCsv(await response.text()).filter(row => Number.isFinite(Number(row.lat)) && Number.isFinite(Number(row.lon)));
    const selectedRisk = document.getElementById("riskSelect").value;
    const visibleRows = rowsByCrop.filter(row => selectedRisk === "all" || riskClass(row) === selectedRisk).slice(0, 1300);
    const clusters = [...new Set(rowsByCrop.map(row => row.cluster).filter(Boolean))].sort((a, b) => Number(a) - Number(b));
    document.getElementById("somSelect").innerHTML = `<option value="all">Todas las clases</option>${clusters.map(cluster => `<option value="${cluster}">Clase ${cluster}</option>`).join("")}`;
    visibleRows.forEach(row => markerFor(row, crop).addTo(pointLayer));
    document.getElementById("mapStatus").textContent = `${visibleRows.length.toLocaleString("es-CO")} points`;
    document.getElementById("mapSubtitle").textContent = "CSV real de puntos útiles · riesgo visual demo";
  } catch (error) {
    document.getElementById("mapStatus").textContent = "placeholder";
    document.getElementById("mapSubtitle").textContent = `${error.message}. Conectar CSV, JSON o GeoJSON validado.`;
  }
}
function renderTriggerFlow() {
  document.getElementById("triggerFlow").innerHTML = triggerSteps.map((step, index) => `
    <article class="trigger-node"><span>${index + 1}</span><h3>${step[0]}</h3><p>${step[1]}</p></article>
  `).join("");
}
function bindControls() {
  ["cropSelect", "signalSelect", "phaseSelect", "riskSelect", "monthSelect", "somSelect"].forEach(id => {
    document.getElementById(id).addEventListener("change", () => loadCrop(document.getElementById("cropSelect").value));
  });
  document.querySelectorAll(".layer-chip").forEach(button => {
    button.addEventListener("click", () => {
      button.classList.toggle("active");
      if (button.dataset.layer !== "points") document.getElementById("mapSubtitle").textContent = `${button.textContent}: placeholder listo para conectar con outputs reales.`;
    });
  });
}
renderTriggerFlow();
bindControls();
if (initMap()) loadCrop("rice");
else updateStaticReadout("rice");
