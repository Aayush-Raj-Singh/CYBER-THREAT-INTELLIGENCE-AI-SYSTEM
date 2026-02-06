import { useEffect, useMemo, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "";
const api = {
  health: `${API_BASE}/api/health`,
  summary: `${API_BASE}/api/summary`,
  events: `${API_BASE}/api/events?limit=500`,
  campaigns: `${API_BASE}/api/campaigns`,
  iocs: `${API_BASE}/api/iocs?limit=1000`,
  report: `${API_BASE}/api/reports/latest`,
};

const pageSizes = [10, 25, 50, 100];

const emptySummary = {
  total_events: 0,
  severity_counts: { high: 0, medium: 0, low: 0, informational: 0 },
  incident_counts: {},
  sector_counts: {},
  campaign_count: 0,
  ioc_count: 0,
};

function toNumber(value) {
  if (typeof value === "number") return value;
  const parsed = Number(value);
  return Number.isNaN(parsed) ? 0 : parsed;
}

function formatNumber(value) {
  return new Intl.NumberFormat("en-IN").format(toNumber(value));
}

function severityBadge(label = "informational") {
  const map = {
    high: "badge badge-high",
    medium: "badge badge-medium",
    low: "badge badge-low",
    informational: "badge badge-informational",
  };
  return map[label] || map.informational;
}

async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json();
}

export default function App() {
  const [theme, setTheme] = useState("light");
  const [health, setHealth] = useState("Checking API...");
  const [summary, setSummary] = useState(emptySummary);
  const [events, setEvents] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [iocs, setIocs] = useState([]);
  const [report, setReport] = useState("No report loaded");

  const [filters, setFilters] = useState({
    severity: "all",
    incident: "all",
    sector: "all",
  });
  const [eventPage, setEventPage] = useState(1);
  const [eventPageSize, setEventPageSize] = useState(10);

  const [iocSearch, setIocSearch] = useState("");
  const [iocType, setIocType] = useState("all");
  const [iocSort, setIocSort] = useState("confidence_desc");
  const [iocPage, setIocPage] = useState(1);
  const [iocPageSize, setIocPageSize] = useState(10);

  const [detailOpen, setDetailOpen] = useState(false);
  const [detail, setDetail] = useState(null);
  const [detailError, setDetailError] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("cti-theme");
    if (saved === "dark") {
      setTheme("dark");
    }
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("cti-theme", theme);
  }, [theme]);

  useEffect(() => {
    const load = async () => {
      try {
        await fetchJSON(api.health);
        setHealth("API online");
      } catch {
        setHealth("API offline");
      }

      try {
        const data = await fetchJSON(api.summary);
        setSummary(data);
      } catch {
        setSummary(emptySummary);
      }

      try {
        const data = await fetchJSON(api.events);
        setEvents(data);
      } catch {
        setEvents([]);
      }

      try {
        const data = await fetchJSON(api.campaigns);
        setCampaigns(data);
      } catch {
        setCampaigns([]);
      }

      try {
        const data = await fetchJSON(api.iocs);
        setIocs(data);
      } catch {
        setIocs([]);
      }

      await loadReport();
    };

    load();
  }, []);

  const loadReport = async () => {
    setReport("Loading...");
    try {
      const data = await fetchJSON(api.report);
      setReport(data.raw_json || "No report content");
    } catch {
      setReport("Report not found. Run the pipeline to generate reports.");
    }
  };

  const severities = useMemo(() => {
    return ["all", ...new Set(events.map((event) => event.severity_label))];
  }, [events]);

  const incidents = useMemo(() => {
    return ["all", ...new Set(events.map((event) => event.incident_type))];
  }, [events]);

  const sectors = useMemo(() => {
    return ["all", ...new Set(events.map((event) => event.sector))];
  }, [events]);

  const filteredEvents = useMemo(() => {
    let list = [...events];
    if (filters.severity !== "all") {
      list = list.filter((event) => event.severity_label === filters.severity);
    }
    if (filters.incident !== "all") {
      list = list.filter((event) => event.incident_type === filters.incident);
    }
    if (filters.sector !== "all") {
      list = list.filter((event) => event.sector === filters.sector);
    }
    return list;
  }, [events, filters]);

  const eventTotalPages = Math.max(1, Math.ceil(filteredEvents.length / eventPageSize));
  const pagedEvents = useMemo(() => {
    const start = (eventPage - 1) * eventPageSize;
    return filteredEvents.slice(start, start + eventPageSize);
  }, [filteredEvents, eventPage, eventPageSize]);

  useEffect(() => {
    setEventPage(1);
  }, [filters.severity, filters.incident, filters.sector, eventPageSize]);

  useEffect(() => {
    if (eventPage > eventTotalPages) {
      setEventPage(eventTotalPages);
    }
  }, [eventPage, eventTotalPages]);

  const iocTypes = useMemo(() => {
    return ["all", ...new Set(iocs.map((ioc) => ioc.ioc_type))];
  }, [iocs]);

  const filteredIocs = useMemo(() => {
    let list = [...iocs];
    if (iocType !== "all") {
      list = list.filter((ioc) => ioc.ioc_type === iocType);
    }
    if (iocSearch.trim()) {
      const search = iocSearch.toLowerCase();
      list = list.filter((ioc) =>
        (ioc.normalized_value || ioc.value || "").toLowerCase().includes(search)
      );
    }
    if (iocSort === "confidence_desc") {
      list.sort((a, b) => toNumber(b.confidence) - toNumber(a.confidence));
    }
    if (iocSort === "confidence_asc") {
      list.sort((a, b) => toNumber(a.confidence) - toNumber(b.confidence));
    }
    if (iocSort === "type_asc") {
      list.sort((a, b) => (a.ioc_type || "").localeCompare(b.ioc_type || ""));
    }
    if (iocSort === "value_asc") {
      list.sort((a, b) =>
        (a.normalized_value || a.value || "").localeCompare(b.normalized_value || b.value || "")
      );
    }
    return list;
  }, [iocs, iocType, iocSearch, iocSort]);

  const iocTotalPages = Math.max(1, Math.ceil(filteredIocs.length / iocPageSize));
  const pagedIocs = useMemo(() => {
    const start = (iocPage - 1) * iocPageSize;
    return filteredIocs.slice(start, start + iocPageSize);
  }, [filteredIocs, iocPage, iocPageSize]);

  useEffect(() => {
    setIocPage(1);
  }, [iocSearch, iocType, iocSort, iocPageSize]);

  useEffect(() => {
    if (iocPage > iocTotalPages) {
      setIocPage(iocTotalPages);
    }
  }, [iocPage, iocTotalPages]);

  const openDetail = async (eventId) => {
    setDetailOpen(true);
    setDetail(null);
    setDetailError("");
    try {
      const data = await fetchJSON(`${API_BASE}/api/events/${eventId}`);
      setDetail(data);
    } catch (err) {
      setDetailError(err.message || "Failed to load detail");
    }
  };

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div className="mx-auto w-full max-w-6xl px-6 py-10">
        <section className="glass-card rounded-[32px] p-8 shadow-soft">
          <nav className="flex flex-wrap items-center justify-between gap-6">
            <div className="flex flex-wrap items-center gap-2 rounded-full bg-white/80 px-4 py-2 text-xs font-semibold text-slate-500 shadow-sm dark:bg-slate-900/70 dark:text-slate-300">
              {[
                "Services",
                "Pricing",
                "About",
                "Insights",
                "Contact",
              ].map((item) => (
                <span key={item} className="rounded-full px-3 py-1 transition hover:bg-white/90 dark:hover:bg-slate-800/70">
                  {item}
                </span>
              ))}
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={toggleTheme}
                aria-label="Toggle theme"
                className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200/70 bg-white/80 text-slate-600 transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-700/60 dark:bg-slate-900/70 dark:text-slate-200"
              >
                {theme === "dark" ? (
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-5 w-5"
                  >
                    <circle cx="12" cy="12" r="4.5"></circle>
                    <path d="M12 2.5v2.5"></path>
                    <path d="M12 19v2.5"></path>
                    <path d="M4.6 4.6l1.8 1.8"></path>
                    <path d="M17.6 17.6l1.8 1.8"></path>
                    <path d="M2.5 12h2.5"></path>
                    <path d="M19 12h2.5"></path>
                    <path d="M4.6 19.4l1.8-1.8"></path>
                    <path d="M17.6 6.4l1.8-1.8"></path>
                  </svg>
                ) : (
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.8"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="h-5 w-5"
                  >
                    <path d="M21 14.5A8.5 8.5 0 1 1 9.5 3a6.5 6.5 0 0 0 11.5 11.5Z"></path>
                  </svg>
                )}
              </button>
              <button className="text-xs font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-300 dark:hover:text-white">
                Login
              </button>
              <button className="rounded-full bg-slate-900 px-4 py-2 text-xs font-semibold text-white transition hover:-translate-y-0.5 hover:shadow-lg dark:bg-white dark:text-slate-900">
                Get Started ->
              </button>
            </div>
          </nav>

          <div className="mt-10 grid gap-10 lg:grid-cols-[1.2fr_1fr]">
            <div>
              <h1 className="text-5xl font-bold tracking-tight text-slate-900 dark:text-white md:text-6xl">
                CTI FORCE.
              </h1>
              <p className="mt-4 max-w-xl text-base text-slate-600 dark:text-slate-300">
                ML-assisted OSINT platform for scheduled cyber incident monitoring in Indian
                cyberspace.
              </p>
              <div className="mt-8 grid gap-4 sm:grid-cols-3">
                {[
                  { title: "OSINT", sub: "Public sources only" },
                  { title: "Explainable", sub: "TF-IDF + classical ML" },
                  { title: "Scheduled", sub: "Hourly or daily runs" },
                ].map((item) => (
                  <div key={item.title} className="rounded-2xl border border-white/70 bg-white/70 p-4 text-sm shadow-sm dark:border-slate-700/60 dark:bg-slate-900/70">
                    <p className="text-lg font-semibold text-slate-900 dark:text-white">
                      {item.title}
                    </p>
                    <p className="text-xs text-slate-500 dark:text-slate-400">{item.sub}</p>
                  </div>
                ))}
              </div>
              <div className="mt-10 flex flex-wrap items-center gap-6">
                <button className="rounded-full border border-slate-900/10 bg-lime-300/70 px-6 py-3 text-sm font-semibold text-slate-900 shadow-soft transition hover:-translate-y-0.5 dark:border-lime-200/20 dark:text-slate-900">
                  How it works?
                </button>
                <div className="text-sm font-semibold text-slate-600 dark:text-slate-300">
                  {health}
                </div>
              </div>
            </div>
            <div className="relative flex items-center justify-center">
              <div className="hero-orb"></div>
              <div className="hero-ring"></div>
              <div className="hero-ring secondary"></div>
              <div className="absolute right-2 top-6 hidden flex-col gap-2 text-xs text-slate-500 dark:text-slate-400 lg:flex">
                <span>Web based / 01</span>
                <span>Collaborative / 02</span>
                <span>Near real-time / 03</span>
              </div>
              <div className="absolute bottom-6 left-6 max-w-[180px] text-xs text-slate-500 dark:text-slate-400">
                The CTI system keeps your SOC workflow connected to authoritative advisories,
                sector-specific sources, and IOC-driven correlation.
              </div>
            </div>
          </div>
        </section>

        <section className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[
            { label: "Total Events", value: summary.total_events },
            { label: "Campaigns", value: summary.campaign_count },
            { label: "IOCs", value: summary.ioc_count },
            { label: "High Severity", value: summary.severity_counts?.high || 0 },
            { label: "Medium Severity", value: summary.severity_counts?.medium || 0 },
            { label: "Low Severity", value: summary.severity_counts?.low || 0 },
          ].map((metric) => (
            <div key={metric.label} className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-soft dark:border-slate-700/60 dark:bg-slate-900/70">
              <p className="text-sm text-slate-500 dark:text-slate-400">{metric.label}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                {formatNumber(metric.value)}
              </p>
            </div>
          ))}
        </section>

        <section className="mt-10 rounded-3xl border border-white/70 bg-white/80 p-6 shadow-soft dark:border-slate-700/60 dark:bg-slate-900/70">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h2 className="text-xl font-semibold">Event Intelligence</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Scheduled OSINT monitoring, correlation, and scoring
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs">
              <select
                value={filters.severity}
                onChange={(event) => setFilters({ ...filters, severity: event.target.value })}
                className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
              >
                {severities.map((value) => (
                  <option key={value} value={value}>
                    {value === "all" ? "Severity: All" : value}
                  </option>
                ))}
              </select>
              <select
                value={filters.incident}
                onChange={(event) => setFilters({ ...filters, incident: event.target.value })}
                className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
              >
                {incidents.map((value) => (
                  <option key={value} value={value}>
                    {value === "all" ? "Incident: All" : value}
                  </option>
                ))}
              </select>
              <select
                value={filters.sector}
                onChange={(event) => setFilters({ ...filters, sector: event.target.value })}
                className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
              >
                {sectors.map((value) => (
                  <option key={value} value={value}>
                    {value === "all" ? "Sector: All" : value}
                  </option>
                ))}
              </select>
              <select
                value={eventPageSize}
                onChange={(event) => setEventPageSize(Number(event.target.value))}
                className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
              >
                {pageSizes.map((size) => (
                  <option key={size} value={size}>{`Show: ${size}`}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="mt-6 space-y-2">
            <div className="table-row header">
              <span>Event</span>
              <span>Incident</span>
              <span>Sector</span>
              <span>Severity</span>
              <span>Confidence</span>
            </div>
            {pagedEvents.length ? (
              pagedEvents.map((event) => (
                <button
                  key={event.event_id}
                  className="table-row w-full text-left"
                  onClick={() => openDetail(event.event_id)}
                >
                  <span className="font-semibold text-slate-900 dark:text-white">
                    {event.event_id?.slice(0, 8)}
                  </span>
                  <span>{event.incident_type}</span>
                  <span>{event.sector}</span>
                  <span>
                    <span className={severityBadge(event.severity_label)}>
                      {event.severity_label}
                    </span>
                  </span>
                  <span>{toNumber(event.confidence).toFixed(2)}</span>
                </button>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950">
                No events yet. Run the pipeline with real OSINT sources.
              </div>
            )}
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setEventPage((page) => Math.max(1, page - 1))}
                disabled={eventPage <= 1}
                className="rounded-full border border-slate-200 px-4 py-2 text-xs disabled:opacity-50 dark:border-slate-700"
              >
                Prev
              </button>
              <span>{`Page ${eventPage} of ${eventTotalPages}`}</span>
              <span className="text-slate-500 dark:text-slate-400">
                {filteredEvents.length} items
              </span>
              <button
                onClick={() => setEventPage((page) => Math.min(eventTotalPages, page + 1))}
                disabled={eventPage >= eventTotalPages}
                className="rounded-full border border-slate-200 px-4 py-2 text-xs disabled:opacity-50 dark:border-slate-700"
              >
                Next
              </button>
            </div>
          </div>
        </section>

        <section className="mt-10 rounded-3xl border border-white/70 bg-white/80 p-6 shadow-soft dark:border-slate-700/60 dark:bg-slate-900/70">
          <div>
            <h2 className="text-xl font-semibold">Campaigns</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              Graph-based grouping by IOC reuse and time windows
            </p>
          </div>
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            {campaigns.length ? (
              campaigns.map((camp) => (
                <div key={camp.campaign_id} className="rounded-2xl border border-slate-200 bg-white/70 p-4 text-sm dark:border-slate-700 dark:bg-slate-950">
                  <p className="text-base font-semibold text-slate-900 dark:text-white">
                    {camp.name || camp.campaign_id}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Confidence: {toNumber(camp.confidence).toFixed(2)}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Events: {camp.event_ids?.length || 0}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    MITRE: {(camp.mitre_tactics || []).slice(0, 3).join(", ") || "None"}
                  </p>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950">
                No campaigns yet. Run the pipeline with real data.
              </div>
            )}
          </div>
        </section>

        <section className="mt-10 rounded-3xl border border-white/70 bg-white/80 p-6 shadow-soft dark:border-slate-700/60 dark:bg-slate-900/70">
          <div>
            <h2 className="text-xl font-semibold">IOC Explorer</h2>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              High-signal indicators extracted from OSINT
            </p>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-3 text-xs">
            <input
              value={iocSearch}
              onChange={(event) => setIocSearch(event.target.value)}
              placeholder="Search indicators..."
              className="w-full rounded-full border border-slate-200 bg-white px-4 py-2 text-xs sm:w-64 dark:border-slate-700 dark:bg-slate-950"
            />
            <select
              value={iocType}
              onChange={(event) => setIocType(event.target.value)}
              className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
            >
              {iocTypes.map((value) => (
                <option key={value} value={value}>
                  {value === "all" ? "Type: All" : `Type: ${value}`}
                </option>
              ))}
            </select>
            <select
              value={iocSort}
              onChange={(event) => setIocSort(event.target.value)}
              className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
            >
              <option value="confidence_desc">Sort: Confidence (High -> Low)</option>
              <option value="confidence_asc">Sort: Confidence (Low -> High)</option>
              <option value="type_asc">Sort: Type (A -> Z)</option>
              <option value="value_asc">Sort: Value (A -> Z)</option>
            </select>
            <select
              value={iocPageSize}
              onChange={(event) => setIocPageSize(Number(event.target.value))}
              className="rounded-full border border-slate-200 bg-white px-3 py-2 text-xs dark:border-slate-700 dark:bg-slate-950"
            >
              {pageSizes.map((size) => (
                <option key={size} value={size}>{`Show: ${size}`}</option>
              ))}
            </select>
          </div>
          <div className="mt-6 space-y-2">
            <div className="ioc-row header">
              <span>Indicator</span>
              <span>Type</span>
              <span>Confidence</span>
            </div>
            {pagedIocs.length ? (
              pagedIocs.map((ioc, index) => (
                <div key={`${ioc.normalized_value || ioc.value}-${index}`} className="ioc-row">
                  <span className="truncate font-semibold text-slate-900 dark:text-white" title={ioc.normalized_value || ioc.value}>
                    {ioc.normalized_value || ioc.value}
                  </span>
                  <span>{ioc.ioc_type}</span>
                  <span>{toNumber(ioc.confidence).toFixed(2)}</span>
                </div>
              ))
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950">
                No IOCs yet. Pipeline output required.
              </div>
            )}
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 text-sm">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIocPage((page) => Math.max(1, page - 1))}
                disabled={iocPage <= 1}
                className="rounded-full border border-slate-200 px-4 py-2 text-xs disabled:opacity-50 dark:border-slate-700"
              >
                Prev
              </button>
              <span>{`Page ${iocPage} of ${iocTotalPages}`}</span>
              <span className="text-slate-500 dark:text-slate-400">
                {filteredIocs.length} items
              </span>
              <button
                onClick={() => setIocPage((page) => Math.min(iocTotalPages, page + 1))}
                disabled={iocPage >= iocTotalPages}
                className="rounded-full border border-slate-200 px-4 py-2 text-xs disabled:opacity-50 dark:border-slate-700"
              >
                Next
              </button>
            </div>
          </div>
        </section>

        <section className="mt-10 rounded-3xl border border-white/70 bg-white/80 p-6 shadow-soft dark:border-slate-700/60 dark:bg-slate-900/70">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-xl font-semibold">Latest Report</h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Machine-readable JSON bundle
              </p>
            </div>
            <button
              onClick={loadReport}
              className="rounded-full border border-slate-200 px-4 py-2 text-xs dark:border-slate-700"
            >
              Refresh
            </button>
          </div>
          <pre className="code-block mt-6">{report}</pre>
        </section>

        <footer className="mt-10 text-center text-xs text-slate-500 dark:text-slate-400">
          Built for blue-team operations | OSINT only | Analyst assist
        </footer>
      </div>

      {detailOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-end">
          <div
            className="absolute inset-0 drawer-backdrop"
            onClick={() => setDetailOpen(false)}
          />
          <div className="relative h-full w-full max-w-xl overflow-y-auto bg-white p-6 shadow-2xl dark:bg-slate-900">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">Event Detail</h3>
              <button
                onClick={() => setDetailOpen(false)}
                className="rounded-full border border-slate-200 px-3 py-1 text-xs dark:border-slate-700"
              >
                Close
              </button>
            </div>
            <div className="mt-4 text-sm text-slate-600 dark:text-slate-300">
              {detailError && <p>{detailError}</p>}
              {!detailError && !detail && <p>Loading...</p>}
              {detail && (
                <div className="space-y-3">
                  <div><strong>Event ID:</strong> {detail.event_id}</div>
                  <div><strong>Incident:</strong> {detail.incident_type} ({toNumber(detail.incident_confidence).toFixed(2)})</div>
                  <div><strong>Sector:</strong> {detail.sector} ({toNumber(detail.sector_confidence).toFixed(2)})</div>
                  <div><strong>Severity:</strong> {detail.severity_label} ({toNumber(detail.severity).toFixed(2)})</div>
                  <div><strong>Confidence:</strong> {toNumber(detail.confidence).toFixed(2)}</div>
                  <div><strong>Source:</strong> {detail.source}</div>
                  <div><strong>Source URL:</strong> {detail.source_url}</div>
                  <div><strong>MITRE Tactics:</strong> {(detail.mitre_tactics || []).join(", ") || "None"}</div>
                  <div><strong>Campaign:</strong> {detail.campaign_id || "None"}</div>
                  <div><strong>Shared IOCs:</strong> {(detail.shared_iocs || []).slice(0, 10).join(", ") || "None"}</div>
                  <div><strong>IOCs:</strong> {(detail.iocs || []).slice(0, 20).join(", ") || "None"}</div>
                  <div>
                    <strong>Clean Text:</strong>
                    <pre className="code-block mt-2">{detail.clean_text}</pre>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
