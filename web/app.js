const api = {
  health: "/api/health",
  summary: "/api/summary",
  events: "/api/events?limit=200",
  campaigns: "/api/campaigns",
  iocs: "/api/iocs?limit=200",
  report: "/api/reports/latest",
};

const state = {
  events: [],
  campaigns: [],
  iocs: [],
  iocPage: 1,
  theme: "light",
  eventPage: 1,
};

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json();
}

function setHealth(status) {
  const health = document.getElementById("health");
  health.textContent = status;
}

function renderMetrics(summary) {
  const metrics = document.getElementById("metrics");
  metrics.innerHTML = "";
  const cards = [
    { title: "Total Events", value: summary.total_events },
    { title: "Campaigns", value: summary.campaign_count },
    { title: "IOCs", value: summary.ioc_count },
    { title: "High Severity", value: summary.severity_counts.high || 0 },
    { title: "Medium Severity", value: summary.severity_counts.medium || 0 },
    { title: "Low Severity", value: summary.severity_counts.low || 0 },
  ];

  for (const card of cards) {
    const div = document.createElement("div");
    div.className = "metric-card";
    div.innerHTML = `<h3>${card.title}</h3><p>${card.value}</p>`;
    metrics.appendChild(div);
  }
}

function renderEvents(events) {
  const table = document.getElementById("eventsTable");
  table.innerHTML = "";
  const header = document.createElement("div");
  header.className = "table-row header";
  header.innerHTML = "<span>Event</span><span>Incident</span><span>Sector</span><span>Severity</span><span>Confidence</span>";
  table.appendChild(header);

  if (!events.length) {
    const empty = document.createElement("div");
    empty.className = "card";
    empty.innerHTML = "<h4>No events yet</h4><small>Run the pipeline with real OSINT sources.</small>";
    table.appendChild(empty);
    return;
  }

  for (const event of events) {
    const row = document.createElement("div");
    row.className = "table-row";
    row.innerHTML = `
      <span>${event.event_id.slice(0, 8)}?</span>
      <span>${event.incident_type}</span>
      <span>${event.sector}</span>
      <span><span class="badge ${event.severity_label}">${event.severity_label}</span></span>
      <span>${event.confidence.toFixed(2)}</span>
    `;
    row.addEventListener("click", () => showDetail(event.event_id));
    table.appendChild(row);
  }
}

function populateFilters(events) {
  const severity = document.getElementById("filterSeverity");
  const incident = document.getElementById("filterIncident");
  const sector = document.getElementById("filterSector");

  const severities = ["all", ...new Set(events.map((e) => e.severity_label))];
  const incidents = ["all", ...new Set(events.map((e) => e.incident_type))];
  const sectors = ["all", ...new Set(events.map((e) => e.sector))];

  fillSelect(severity, severities, "Severity");
  fillSelect(incident, incidents, "Incident");
  fillSelect(sector, sectors, "Sector");
}

function fillSelect(select, options, label) {
  select.innerHTML = "";
  for (const option of options) {
    const opt = document.createElement("option");
    opt.value = option;
    opt.textContent = option === "all" ? `${label}: All` : option;
    select.appendChild(opt);
  }
}

function applyFilters() {
  const severity = document.getElementById("filterSeverity").value;
  const incident = document.getElementById("filterIncident").value;
  const sector = document.getElementById("filterSector").value;
  const pageSize = Number(document.getElementById("eventPageSize").value || 50);

  let filtered = [...state.events];
  if (severity !== "all") {
    filtered = filtered.filter((e) => e.severity_label === severity);
  }
  if (incident !== "all") {
    filtered = filtered.filter((e) => e.incident_type === incident);
  }
  if (sector !== "all") {
    filtered = filtered.filter((e) => e.sector === sector);
  }
  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  if (state.eventPage > totalPages) {
    state.eventPage = totalPages;
  }
  if (state.eventPage < 1) {
    state.eventPage = 1;
  }

  const start = (state.eventPage - 1) * pageSize;
  const pageItems = filtered.slice(start, start + pageSize);
  renderEvents(pageItems);

  const pageInfo = document.getElementById("eventPageInfo");
  if (pageInfo) {
    pageInfo.textContent = `Page ${state.eventPage} of ${totalPages}`;
  }

  const countInfo = document.getElementById("eventCount");
  if (countInfo) {
    countInfo.textContent = `${filtered.length} items`;
  }

  const prev = document.getElementById("eventPrev");
  const next = document.getElementById("eventNext");
  if (prev) prev.disabled = state.eventPage <= 1;
  if (next) next.disabled = state.eventPage >= totalPages;
}

async function showDetail(eventId) {
  const drawer = document.getElementById("detailDrawer");
  const detailBody = document.getElementById("detailBody");
  detailBody.innerHTML = "Loading?";
  drawer.classList.add("open");

  try {
    const detail = await fetchJSON(`/api/events/${eventId}`);
    detailBody.innerHTML = `
      <div class="detail-grid">
        <div><strong>Event ID:</strong> ${detail.event_id}</div>
        <div><strong>Incident:</strong> ${detail.incident_type} (${detail.incident_confidence.toFixed(2)})</div>
        <div><strong>Sector:</strong> ${detail.sector} (${detail.sector_confidence.toFixed(2)})</div>
        <div><strong>Severity:</strong> ${detail.severity_label} (${detail.severity.toFixed(2)})</div>
        <div><strong>Confidence:</strong> ${detail.confidence.toFixed(2)}</div>
        <div><strong>Source:</strong> ${detail.source}</div>
        <div><strong>Source URL:</strong> ${detail.source_url}</div>
        <div><strong>MITRE Tactics:</strong> ${(detail.mitre_tactics || []).join(", ") || "None"}</div>
        <div><strong>Campaign:</strong> ${detail.campaign_id || "None"}</div>
        <div><strong>Shared IOCs:</strong> ${(detail.shared_iocs || []).slice(0, 10).join(", ") || "None"}</div>
        <div><strong>IOCs:</strong> ${(detail.iocs || []).slice(0, 20).join(", ") || "None"}</div>
        <div><strong>Clean Text:</strong></div>
        <pre class="code-block">${detail.clean_text}</pre>
      </div>
    `;
  } catch (err) {
    detailBody.innerHTML = `Failed to load detail: ${err.message}`;
  }
}

function renderCampaigns(campaigns) {
  const container = document.getElementById("campaigns");
  container.innerHTML = "";
  if (!campaigns.length) {
    container.innerHTML = "<div class=\"card\"><h4>No campaigns yet</h4><small>Run the pipeline with real data.</small></div>";
    return;
  }
  const list = document.createElement("div");
  list.className = "card-list";
  for (const camp of campaigns) {
    const card = document.createElement("div");
    card.className = "card";
    card.innerHTML = `
      <h4>${camp.name}</h4>
      <small>Confidence: ${camp.confidence.toFixed(2)}</small>
      <small>Events: ${camp.event_ids.length}</small>
      <small>MITRE: ${(camp.mitre_tactics || []).slice(0, 3).join(", ") || "None"}</small>
    `;
    list.appendChild(card);
  }
  container.appendChild(list);
}

function renderIOCs(iocs) {
  const container = document.getElementById("iocs");
  container.innerHTML = "";
  if (!iocs.length) {
    container.innerHTML = "<div class=\"card\"><h4>No IOCs yet</h4><small>Pipeline output required.</small></div>";
    return;
  }
  const table = document.createElement("div");
  table.className = "ioc-table";

  const header = document.createElement("div");
  header.className = "ioc-row header";
  header.innerHTML = "<span>Indicator</span><span>Type</span><span>Confidence</span>";
  table.appendChild(header);

  for (const ioc of iocs) {
    const row = document.createElement("div");
    row.className = "ioc-row";
    row.innerHTML = `
      <span class="ioc-value" title="${ioc.normalized_value}">${ioc.normalized_value}</span>
      <span class="ioc-type">${ioc.ioc_type}</span>
      <span class="ioc-conf">${ioc.confidence.toFixed(2)}</span>
    `;
    table.appendChild(row);
  }

  container.appendChild(table);
}

function populateIocTypeFilter(iocs) {
  const filter = document.getElementById("iocTypeFilter");
  if (!filter) return;
  const types = ["all", ...new Set(iocs.map((ioc) => ioc.ioc_type))];
  filter.innerHTML = "";
  for (const type of types) {
    const opt = document.createElement("option");
    opt.value = type;
    opt.textContent = type === "all" ? "Type: All" : `Type: ${type}`;
    filter.appendChild(opt);
  }
}

function applyIocControls() {
  const search = document.getElementById("iocSearch").value.toLowerCase().trim();
  const type = document.getElementById("iocTypeFilter").value;
  const sort = document.getElementById("iocSort").value;
  const pageSize = Number(document.getElementById("iocPageSize").value || 50);

  let filtered = [...state.iocs];
  if (type !== "all") {
    filtered = filtered.filter((ioc) => ioc.ioc_type === type);
  }
  if (search) {
    filtered = filtered.filter((ioc) => ioc.normalized_value.toLowerCase().includes(search));
  }

  if (sort === "confidence_desc") {
    filtered.sort((a, b) => b.confidence - a.confidence);
  } else if (sort === "confidence_asc") {
    filtered.sort((a, b) => a.confidence - b.confidence);
  } else if (sort === "type_asc") {
    filtered.sort((a, b) => a.ioc_type.localeCompare(b.ioc_type));
  } else if (sort === "value_asc") {
    filtered.sort((a, b) => a.normalized_value.localeCompare(b.normalized_value));
  }

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  if (state.iocPage > totalPages) {
    state.iocPage = totalPages;
  }
  if (state.iocPage < 1) {
    state.iocPage = 1;
  }

  const start = (state.iocPage - 1) * pageSize;
  const pageItems = filtered.slice(start, start + pageSize);

  renderIOCs(pageItems);
  const pageInfo = document.getElementById("iocPageInfo");
  if (pageInfo) {
    pageInfo.textContent = `Page ${state.iocPage} of ${totalPages}`;
  }
  const countInfo = document.getElementById("iocCount");
  if (countInfo) {
    countInfo.textContent = `${filtered.length} items`;
  }

  const prev = document.getElementById("iocPrev");
  const next = document.getElementById("iocNext");
  if (prev) prev.disabled = state.iocPage <= 1;
  if (next) next.disabled = state.iocPage >= totalPages;
}

async function loadReport() {
  const report = document.getElementById("report");
  report.textContent = "Loading?";
  try {
    const data = await fetchJSON(api.report);
    report.textContent = data.raw_json;
  } catch (err) {
    report.textContent = "Report not found. Run the pipeline to generate reports.";
  }
}

async function init() {
  try {
    await fetchJSON(api.health);
    setHealth("API online");
  } catch (err) {
    setHealth("API offline");
  }

  try {
    const summary = await fetchJSON(api.summary);
    renderMetrics(summary);
  } catch {
    renderMetrics({
      total_events: 0,
      severity_counts: { high: 0, medium: 0, low: 0 },
      incident_counts: {},
      sector_counts: {},
      campaign_count: 0,
      ioc_count: 0,
    });
  }

  try {
    state.events = await fetchJSON(api.events);
    populateFilters(state.events);
    applyFilters();
  } catch (err) {
    renderEvents([]);
  }

  try {
    state.campaigns = await fetchJSON(api.campaigns);
    renderCampaigns(state.campaigns);
  } catch {
    renderCampaigns([]);
  }

  try {
    state.iocs = await fetchJSON(api.iocs);
    populateIocTypeFilter(state.iocs);
    applyIocControls();
  } catch {
    renderIOCs([]);
  }

  await loadReport();

  document.getElementById("filterSeverity").addEventListener("change", applyFilters);
  document.getElementById("filterIncident").addEventListener("change", applyFilters);
  document.getElementById("filterSector").addEventListener("change", applyFilters);
  document.getElementById("eventPageSize").addEventListener("change", () => {
    state.eventPage = 1;
    applyFilters();
  });
  document.getElementById("eventPrev").addEventListener("click", () => {
    state.eventPage -= 1;
    applyFilters();
  });
  document.getElementById("eventNext").addEventListener("click", () => {
    state.eventPage += 1;
    applyFilters();
  });
  document.getElementById("refreshReport").addEventListener("click", loadReport);
  document.getElementById("closeDrawer").addEventListener("click", () => {
    document.getElementById("detailDrawer").classList.remove("open");
  });
  document.getElementById("iocSearch").addEventListener("input", applyIocControls);
  document.getElementById("iocTypeFilter").addEventListener("change", applyIocControls);
  document.getElementById("iocSort").addEventListener("change", applyIocControls);
  document.getElementById("iocPageSize").addEventListener("change", () => {
    state.iocPage = 1;
    applyIocControls();
  });
  document.getElementById("iocPrev").addEventListener("click", () => {
    state.iocPage -= 1;
    applyIocControls();
  });
  document.getElementById("iocNext").addEventListener("click", () => {
    state.iocPage += 1;
    applyIocControls();
  });

  setupParallax();
  setupThemeToggle();
}

init();

function setupParallax() {
  const hero = document.getElementById("hero");
  if (!hero) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  const layers = Array.from(hero.querySelectorAll(".parallax-layer"));
  if (!layers.length) return;

  let rect = hero.getBoundingClientRect();
  let targetX = 0;
  let targetY = 0;
  let rafId = null;

  function update() {
    rafId = null;
    layers.forEach((layer) => {
      const depth = Number(layer.dataset.depth || 0);
      const x = targetX * depth;
      const y = targetY * depth;
      layer.style.transform = `translate3d(${x}px, ${y}px, 0)`;
    });
  }

  function handleMove(event) {
    if (event.pointerType && event.pointerType !== "mouse") return;
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;
    const cx = rect.width / 2;
    const cy = rect.height / 2;
    targetX = (x - cx) / rect.width;
    targetY = (y - cy) / rect.height;
    if (!rafId) {
      rafId = requestAnimationFrame(update);
    }
  }

  function reset() {
    targetX = 0;
    targetY = 0;
    if (!rafId) {
      rafId = requestAnimationFrame(update);
    }
  }

  hero.addEventListener("pointermove", handleMove);
  hero.addEventListener("pointerleave", reset);
  window.addEventListener("resize", () => {
    rect = hero.getBoundingClientRect();
  });
}

function setupThemeToggle() {
  const toggle = document.getElementById("themeToggle");
  if (!toggle) return;

  const saved = localStorage.getItem("cti-theme");
  if (saved === "dark") {
    document.body.classList.add("theme-dark");
    state.theme = "dark";
    toggle.classList.add("is-dark");
  }

  toggle.addEventListener("click", () => {
    const isDark = document.body.classList.toggle("theme-dark");
    state.theme = isDark ? "dark" : "light";
    toggle.classList.toggle("is-dark", isDark);
    localStorage.setItem("cti-theme", state.theme);
  });
}
