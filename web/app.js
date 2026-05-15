const DATA_ROOTS = ["", "./", "data/", "../outputs/web/"];
const cropFiles = {
  rice: "rice_puntos_utiles_interseccion.csv",
  maize: "maize_puntos_utiles_interseccion.csv",
  wheat: "wheat_puntos_utiles_interseccion.csv",
  soybean: "soybean_puntos_utiles_interseccion.csv"
};
const cropLabels = { rice: "Rice", maize: "Maize", wheat: "Wheat", soybean: "Soybean" };
const cropColors = { rice: "#58b47b", maize: "#f0c85c", wheat: "#d99b52", soybean: "#7ad7e3" };
const clusterPalette = ["#7ad7e3", "#58b47b", "#f0c85c", "#da8234", "#bf4638", "#8d7df2", "#38a3a5", "#e26d5c"];
let map;
let pointLayer;
let activeCrop = "rice";
let cropRows = [];
let clusterMeans = [];
let triggerRows = [];
let phaseRows = [];
let oniRows = [];

async function fetchText(file) {
  for (const root of DATA_ROOTS) {
    try {
      const response = await fetch(root + file);
      if (response.ok) return response.text();
    } catch (_) {}
  }
  throw new Error(`Could not load ${file}`);
}
function parseCSV(text) {
  const [head, ...lines] = text.trim().split(/\r?\n/);
  const headers = head.split(",");
  return lines.filter(Boolean).map(line => {
    const values = line.split(",");
    return Object.fromEntries(headers.map((h, i) => [h, values[i] ?? ""]));
  });
}
function num(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}
function fmt(value, digits = 2) {
  const parsed = num(value);
  return parsed === null ? "n/a" : parsed.toFixed(digits);
}
function variabilityClass(row) {
  const value = num(row.std) ?? 0;
  if (value >= 1.35) return "extreme";
  if (value >= 1) return "high";
  if (value >= 0.55) return "elevated";
  return "low";
}
function colorFor(row) {
  const mode = document.getElementById("colorMode").value;
  if (mode === "crop") return cropColors[activeCrop];
  if (mode === "cluster") return clusterPalette[(Number(row.cluster) || 0) % clusterPalette.length];
  if (mode === "trigger") {
    const trigger = triggerRows.find(item => item.som_label === row.cluster);
    const value = Math.abs(num(trigger?.trigger_oni_approx) ?? 0);
    if (value > 0.6) return "#bf4638";
    if (value > 0.35) return "#da8234";
    return "#f0c85c";
  }
  const cls = variabilityClass(row);
  return { low: "#58b47b", elevated: "#7ad7e3", high: "#da8234", extreme: "#bf4638" }[cls];
}
function initMap() {
  if (!window.L) {
    document.getElementById("mapFallback").hidden = false;
    return false;
  }
  map = L.map("map", { preferCanvas: true, minZoom: 2, maxZoom: 7, worldCopyJump: true }).setView([12, -38], 2);
  L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", { maxZoom: 7 }).addTo(map);
  pointLayer = L.layerGroup().addTo(map);
  const zones = [
    [[30, -106], [49, -75], "North American grain belt · methodological preview", "#58b47b"],
    [[-36, -66], [-7, -36], "South American crop-risk corridor · methodological preview", "#da8234"],
    [[5, 66], [33, 123], "Asian monsoon agriculture · MJO-ready layer", "#f0c85c"],
    [[-35, 110], [-9, 154], "Oceania climate exposure · future layer", "#bf4638"]
  ];
  zones.forEach(([a, b, label, color]) => L.rectangle([a, b], { color, weight: 1, fillColor: color, fillOpacity: 0.13 }).bindTooltip(label).addTo(map));
  return true;
}
function marker(row) {
  const lat = num(row.lat);
  const lon = num(row.lon);
  if (lat === null || lon === null) return null;
  const color = colorFor(row);
  const radius = 4 + Math.min(7, (num(row.std) ?? 0) * 3);
  return L.circleMarker([lat, lon], {
    radius,
    className: "pixel-marker",
    color: "rgba(255,255,255,.86)",
    weight: 1,
    fillColor: color,
    fillOpacity: 0.72
  }).on("click", () => selectPixel(row));
}
function selectPixel(row) {
  const signal = document.getElementById("signalSelect").value;
  const phase = document.getElementById("phaseSelect").value;
  const trigger = triggerRows.find(item => item.som_label === row.cluster);
  document.getElementById("pixelTitle").textContent = "Pixel intelligence profile";
  document.getElementById("pixelLocation").textContent = `${fmt(row.lat)}, ${fmt(row.lon)}`;
  document.getElementById("pixelCrop").textContent = cropLabels[activeCrop];
  document.getElementById("pixelCluster").textContent = `Class ${row.cluster || "n/a"}`;
  document.getElementById("pixelStd").textContent = `${fmt(row.std)} variability index`;
  document.getElementById("pixelSignal").textContent = signal === "ONI" ? "ENSO / ONI" : signal === "MJO" ? "MJO / RMM-ready" : "SST correlation-ready";
  document.getElementById("pixelPhase").textContent = phase;
  const triggerText = trigger ? `ONI ${Number(trigger.trigger_oni_approx) >= 0 ? ">" : "<"} ${fmt(trigger.trigger_oni_approx)} around exposed windows.` : "Trigger signal will be assigned after class-level validation.";
  document.getElementById("triggerSentence").textContent = triggerText;
  drawSpark(row.cluster);
}
async function loadCrop(crop) {
  activeCrop = crop;
  document.getElementById("mapTitle").textContent = `${cropLabels[crop]} climate-risk pixels`;
  document.getElementById("mapKicker").textContent = "Loading crop layer";
  if (!pointLayer) return;
  pointLayer.clearLayers();
  cropRows = parseCSV(await fetchText(cropFiles[crop])).filter(row => num(row.lat) !== null && num(row.lon) !== null);
  const selectedCluster = document.getElementById("clusterSelect").value;
  const filtered = cropRows.filter(row => selectedCluster === "all" || row.cluster === selectedCluster).slice(0, 2200);
  filtered.forEach(row => {
    const item = marker(row);
    if (item) item.addTo(pointLayer);
  });
  const clusters = [...new Set(cropRows.map(row => row.cluster).filter(Boolean))].sort((a, b) => Number(a) - Number(b));
  const clusterSelect = document.getElementById("clusterSelect");
  const current = clusterSelect.value;
  clusterSelect.innerHTML = `<option value="all">All classes</option>${clusters.map(c => `<option value="${c}">Class ${c}</option>`).join("")}`; if (selectedCluster !== "all" && clusters.includes(selectedCluster)) clusterSelect.value = selectedCluster;
  if (clusters.includes(current)) clusterSelect.value = current;
  document.getElementById("mapKicker").textContent = `${filtered.length.toLocaleString("en-US")} pixels rendered`;
  document.getElementById("mapSubtitle").textContent = `Color mode: ${document.getElementById("colorMode").selectedOptions[0].text}`;
  document.getElementById("heroMetric").textContent = `${cropRows.length.toLocaleString("en-US")} ${cropLabels[crop]} pixels`;
  if (clusterMeans.length) renderClassList(); if (filtered[0]) selectPixel(filtered[0]);
}
function drawSpark(cluster) {
  const canvas = document.getElementById("miniSpark");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const values = oniRows.filter(row => !cluster || row.som_label === cluster).slice(0, 36).map(row => num(row.oni_critical_top2) ?? 0);
  const series = values.length ? values : [0.1, 0.8, -0.2, -0.6, 0.4, 1.1, -0.4, 0.2];
  ctx.strokeStyle = "rgba(255,255,255,.18)";
  ctx.beginPath(); ctx.moveTo(0, 76); ctx.lineTo(canvas.width, 76); ctx.stroke();
  ctx.strokeStyle = "#7ad7e3"; ctx.lineWidth = 4; ctx.beginPath();
  series.forEach((value, index) => {
    const x = (index / Math.max(1, series.length - 1)) * canvas.width;
    const y = 76 - value * 28;
    if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.stroke();
}
function drawFingerprint(activeLabel = "0") {
  const canvas = document.getElementById("fingerprintChart");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  const row = clusterMeans.find(item => item.label === activeLabel) || clusterMeans[0];
  if (!row) return;
  const keys = ["nino12", "nino3", "nino34", "nino4"];
  const w = canvas.width / keys.length;
  keys.forEach((key, i) => {
    const value = num(row[key]) ?? 0;
    const height = Math.abs(value) * 520;
    const x = i * w + 42;
    const base = canvas.height / 2;
    ctx.fillStyle = value >= 0 ? "#da8234" : "#7ad7e3";
    ctx.fillRect(x, value >= 0 ? base - height : base, w - 80, height);
    ctx.fillStyle = "#526874"; ctx.font = "16px Inter"; ctx.fillText(key.toUpperCase(), x, canvas.height - 22);
  });
  ctx.strokeStyle = "#d8e3e2"; ctx.beginPath(); ctx.moveTo(20, canvas.height / 2); ctx.lineTo(canvas.width - 20, canvas.height / 2); ctx.stroke();
  document.getElementById("activeClassTitle").textContent = `Class ${row.label} ENSO fingerprint`;
}
function drawScatter() {
  const canvas = document.getElementById("oniScatter");
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = "#ffffff"; ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = "#d8e3e2";
  ctx.beginPath(); ctx.moveTo(52, 24); ctx.lineTo(52, canvas.height - 42); ctx.lineTo(canvas.width - 24, canvas.height - 42); ctx.stroke();
  oniRows.slice(0, 1800).forEach(row => {
    const xVal = num(row.oni_critical_top2) ?? 0;
    const yVal = num(row.yield_anomaly) ?? 0;
    const x = 52 + ((xVal + 2.5) / 5) * (canvas.width - 88);
    const y = canvas.height - 42 - ((yVal + 1) / 2) * (canvas.height - 76);
    ctx.fillStyle = yVal < 0 ? "rgba(191,70,56,.34)" : "rgba(88,180,123,.34)";
    ctx.beginPath(); ctx.arc(x, y, 2.2, 0, Math.PI * 2); ctx.fill();
  });
  ctx.fillStyle = "#526874"; ctx.font = "14px Inter"; ctx.fillText("ONI critical window", 58, canvas.height - 12); ctx.save(); ctx.translate(16, canvas.height / 2 + 72); ctx.rotate(-Math.PI / 2); ctx.fillText("Yield anomaly", 0, 0); ctx.restore();
}
function renderClassList() {
  const summaryByClass = cropRows.reduce((acc, row) => { const key = row.cluster || "n/a"; (acc[key] ||= []).push(row); return acc; }, {});
  const container = document.getElementById("classList");
  container.innerHTML = clusterMeans.map((row, index) => {
    const count = summaryByClass[row.label]?.length ?? "research layer";
    return `<article class="class-card ${index === 0 ? "active" : ""}" data-label="${row.label}"><h3><span style="background:${clusterPalette[index % clusterPalette.length]}"></span>Class ${row.label}</h3><p>${count} pixels in current crop layer. ENSO fingerprint available from cluster means.</p></article>`;
  }).join("");
  container.querySelectorAll(".class-card").forEach(card => card.addEventListener("click", () => {
    container.querySelectorAll(".class-card").forEach(item => item.classList.remove("active"));
    card.classList.add("active");
    drawFingerprint(card.dataset.label);
  }));
}
function renderPhenology() {
  const container = document.getElementById("phenologyTimeline");
  container.innerHTML = phaseRows.map(row => `<article class="phase-card"><h3>${row.phase_name}</h3><div class="phase-bar"></div><p>${row.records_with_phase} records with phase · ${row.percent_with_phase}% coverage in the lightweight summary.</p></article>`).join("");
}
function renderTriggers() {
  document.getElementById("triggerGrid").innerHTML = triggerRows.map(row => `<article class="trigger-tile"><span>Class ${row.som_label}</span><div class="trigger-value">${fmt(row.trigger_oni_approx)}</div><h3>Candidate ONI signal</h3><p>${row.n_years} years represented in the research curve. Yield range: ${fmt(row.curve_min_yield)} to ${fmt(row.curve_max_yield)}.</p></article>`).join("");
}
function renderTriggerFlow() {
  const steps = ["Climate variability", "Crop exposure", "Correlation fingerprint", "Phenological window", "Candidate trigger"];
  document.querySelector(".narrative-band").setAttribute("data-ready", steps.join(" > "));
}
function bindControls() {
  ["cropSelect", "colorMode", "signalSelect", "phaseSelect", "clusterSelect"].forEach(id => document.getElementById(id).addEventListener("change", () => loadCrop(document.getElementById("cropSelect").value)));
  document.querySelectorAll(".layer-toggle").forEach(button => button.addEventListener("click", () => button.classList.toggle("active")));
}
async function boot() {
  bindControls();
  initMap();
  [clusterMeans, triggerRows, phaseRows, oniRows] = await Promise.all([
    fetchText("cluster_means.csv").then(parseCSV),
    fetchText("trigger_summary_preliminar.csv").then(parseCSV),
    fetchText("geoglam_resumen_fases.csv").then(parseCSV),
    fetchText("oni_yield_pixel_year_merged.csv").then(parseCSV)
  ]);
  await loadCrop("rice");
  renderClassList();
  drawFingerprint("0");
  drawScatter();
  renderPhenology();
  renderTriggers();
  renderTriggerFlow();
}
boot().catch(error => {
  document.getElementById("mapKicker").textContent = "Data layer offline";
  document.getElementById("mapSubtitle").textContent = error.message;
});


