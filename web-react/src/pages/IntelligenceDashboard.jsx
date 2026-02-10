import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import TopNav from "../components/TopNav";
import { useTheme } from "../hooks/useTheme";
import { useLayoutWidth } from "../hooks/useLayoutWidth";

/* ===================== API CONFIG ===================== */
const API_BASE = import.meta.env.VITE_API_BASE || "";
const api = {
  health: `${API_BASE}/api/health`,
  summary: `${API_BASE}/api/summary`,
  report: `${API_BASE}/api/reports/latest`,
};

const buildEventsUrl = (limit, offset) =>
  `${API_BASE}/api/events?limit=${limit}&offset=${offset}`;
const buildIndicatorsUrl = (limit, offset) =>
  `${API_BASE}/api/iocs?limit=${limit}&offset=${offset}`;

const pageSizes = [10, 25, 50, 100];

const emptySummary = {
  total_events: 0,
  severity_counts: { high: 0, medium: 0, low: 0, informational: 0 },
  campaign_count: 0,
  ioc_count: 0,
};

const toNumber = (v) => (Number.isFinite(+v) ? +v : 0);
const formatNumber = (v) => new Intl.NumberFormat("en-IN").format(toNumber(v));

const severityBadge = (s = "informational") =>
  ({
    high: "badge badge-high",
    medium: "badge badge-medium",
    low: "badge badge-low",
    informational: "badge badge-informational",
  }[s] || "badge badge-informational");

const fetchJSON = async (url) => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(res.statusText);
  return res.json();
};

const formatList = (list, fallback) =>
  list.length ? list.join(", ") : fallback;

const buildReportSummary = (raw) => {
  let payload;
  try {
    payload = JSON.parse(raw);
  } catch {
    return [
      {
        title: "Summary unavailable",
        detail:
          "Report data could not be parsed. Generate a new report to view a readable summary.",
      },
    ];
  }

  const items = Array.isArray(payload?.items) ? payload.items : [];
  const campaigns = Array.isArray(payload?.campaigns) ? payload.campaigns : [];

  const countBy = (list, getter) =>
    list.reduce((acc, item) => {
      const key = getter(item);
      if (!key) return acc;
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

  const topKeys = (counts, limit) =>
    Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, limit)
      .map(([key]) => key);

  const incidentCounts = countBy(items, (item) => item.incident_type || "unknown");
  const sectorCounts = countBy(items, (item) => item.sector || "unknown");
  const severityCounts = countBy(items, (item) => item.severity_label || "informational");

  const tactics = [];
  items.forEach((item) => {
    (item.mitre_tactics || []).forEach((tactic) => tactics.push(tactic));
  });
  const tacticCounts = countBy(tactics, (item) => item || "unknown");

  const indicators = new Set();
  let indicatorTotal = 0;
  items.forEach((item) => {
    const list = item.iocs || [];
    indicatorTotal += list.length;
    list.forEach((ioc) => indicators.add(ioc));
  });

  const topIncidents = topKeys(incidentCounts, 2);
  const topSectors = topKeys(sectorCounts, 2);
  const topTactics = topKeys(tacticCounts, 3);

  const totalEvents = items.length;
  const indicatorCount = indicators.size || indicatorTotal;
  const high = severityCounts.high || 0;
  const medium = severityCounts.medium || 0;
  const low = severityCounts.low || 0;
  const info = severityCounts.informational || 0;
  const campaignCount = campaigns.length;

  return [
    {
      title: "Scope",
      detail: `This summary reflects ${totalEvents || "the available"} events from the latest Cyber Threat Intelligence run so analysts can prioritize review.`,
    },
    {
      title: "Incident focus",
      detail: `Most common incident types: ${formatList(
        topIncidents,
        "a broad mix of incident types"
      )}.`,
    },
    {
      title: "Sector exposure",
      detail: `Most touched sectors: ${formatList(topSectors, "multiple sectors")}.`,
    },
    {
      title: "Severity signal",
      detail: "Severity labels are derived from confidence, correlation strength, and the volume of Indicators of Compromise tied to each event.",
    },
    {
      title: "Severity distribution",
      detail: `${high} high, ${medium} medium, ${low} low, and ${info} informational items were observed in this run.`,
    },
    {
      title: "Indicators of Compromise",
      detail:
        indicatorCount > 0
          ? `Approximately ${indicatorCount} Indicators of Compromise were captured, including network addresses, domains, URLs, and file hashes.`
          : "No Indicators of Compromise were captured, which can occur when sources provide narrative-only detail.",
    },
    {
      title: "Campaign grouping",
      detail:
        campaignCount > 0
          ? `Campaign grouping shows ${campaignCount} cluster${campaignCount === 1 ? "" : "s"} of shared infrastructure and timing.`
          : "Campaign grouping did not form clusters, suggesting isolated or early-stage activity.",
    },
    {
      title: "MITRE ATT&CK mapping",
      detail: topTactics.length
        ? `Most frequent tactics: ${formatList(topTactics, "several common tactics")}.`
        : "MITRE ATT&CK mapping coverage is limited; treat tactic gaps as verification tasks.",
    },
    {
      title: "Analyst action",
      detail:
        "Validate high-priority items against internal logs, then use the report to guide monitoring, threat hunting, and detection tuning.",
    },
    {
      title: "Defensive posture",
      detail:
        "This report is defensive only. Treat public-source indicators as leads until corroborated by internal evidence.",
    },
  ];
};

/* ===================== COMPONENT ===================== */
export default function IntelligenceDashboard() {
  const { theme, toggleTheme } = useTheme();
  const { width: layoutWidth } = useLayoutWidth();
  const [health, setHealth] = useState("Checking API...");
  const [summary, setSummary] = useState(emptySummary);
  const [events, setEvents] = useState([]);
  const [iocs, setIocs] = useState([]);
  const [report, setReport] = useState("No report loaded");
  const [reportSummary, setReportSummary] = useState([]);

  const [eventPage, setEventPage] = useState(1);
  const [eventPageSize, setEventPageSize] = useState(10);
  const [iocPage, setIocPage] = useState(1);
  const [iocPageSize, setIocPageSize] = useState(10);

  /* ===================== EFFECTS ===================== */
  useEffect(() => {
    (async () => {
      try {
        await fetchJSON(api.health);
        setHealth("API online");
      } catch {
        setHealth("API offline");
      }

      try {
        setSummary(await fetchJSON(api.summary));
      } catch {
        setSummary(emptySummary);
      }

      loadReport();
    })();
  }, []);

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const offset = (eventPage - 1) * eventPageSize;
        setEvents(await fetchJSON(buildEventsUrl(eventPageSize, offset)));
      } catch {
        setEvents([]);
      }
    };

    loadEvents();
  }, [eventPage, eventPageSize]);

  useEffect(() => {
    const loadIndicators = async () => {
      try {
        const offset = (iocPage - 1) * iocPageSize;
        setIocs(await fetchJSON(buildIndicatorsUrl(iocPageSize, offset)));
      } catch {
        setIocs([]);
      }
    };

    loadIndicators();
  }, [iocPage, iocPageSize]);

  useEffect(() => {
    setEventPage(1);
  }, [eventPageSize]);

  useEffect(() => {
    setIocPage(1);
  }, [iocPageSize]);

  const loadReport = async () => {
    try {
      const data = await fetchJSON(api.report);
      const raw = data.raw_json || "No report content";
      setReport(raw);
      setReportSummary(buildReportSummary(raw));
    } catch {
      setReport("Report not found");
      setReportSummary([]);
    }
  };

  /* ===================== SORTING ===================== */
  const severityOrder = {
    high: 4,
    medium: 3,
    low: 2,
    informational: 1,
  };

  const [eventSort, setEventSort] = useState({
    key: "confidence",
    direction: "desc",
  });
  const [iocSort, setIocSort] = useState({ key: "value", direction: "asc" });

  const toggleSort = (setSort, key, defaultDirection = "asc") => {
    setSort((prev) => {
      if (prev.key === key) {
        return {
          key,
          direction: prev.direction === "asc" ? "desc" : "asc",
        };
      }
      return { key, direction: defaultDirection };
    });
  };

  const sortItems = (items, { key, direction }, accessor) => {
    const list = [...items];
    const dir = direction === "asc" ? 1 : -1;
    list.sort((a, b) => {
      const aValue = accessor ? accessor(a, key) : a?.[key];
      const bValue = accessor ? accessor(b, key) : b?.[key];
      if (typeof aValue === "number" && typeof bValue === "number") {
        return (aValue - bValue) * dir;
      }
      return (
        String(aValue ?? "").localeCompare(String(bValue ?? ""), "en", {
          sensitivity: "base",
        }) * dir
      );
    });
    return list;
  };

  const sortedEvents = useMemo(
    () =>
      sortItems(events, eventSort, (item, key) => {
        if (key === "severity_label") {
          return severityOrder[item?.severity_label] || 0;
        }
        if (key === "confidence") {
          return toNumber(item?.confidence);
        }
        return item?.[key];
      }),
    [events, eventSort]
  );

  const sortedIocs = useMemo(
    () =>
      sortItems(iocs, iocSort, (item, key) => {
        if (key === "confidence") {
          return toNumber(item?.confidence);
        }
        if (key === "value") {
          return (item?.normalized_value || item?.value || "").toLowerCase();
        }
        return item?.[key];
      }),
    [iocs, iocSort]
  );

  const isActiveSort = (sortState, key) => sortState.key === key;

  const SortIndicator = ({ active, direction }) => (
    <span
      className={`text-[10px] ${
        active ? "text-emerald-500 dark:text-emerald-300" : "text-slate-400"
      }`}
    >
      {active ? (direction === "asc" ? "^" : "v") : "<>"}
    </span>
  );

  /* ===================== DERIVED DATA ===================== */
  const eventTotalCount = Math.max(summary.total_events || 0, events.length || 0);
  const iocTotalCount = Math.max(summary.ioc_count || 0, iocs.length || 0);
  const eventTotalPages = Math.max(1, Math.ceil(eventTotalCount / eventPageSize));
  const iocTotalPages = Math.max(1, Math.ceil(iocTotalCount / iocPageSize));

  useEffect(() => {
    if (eventPage > eventTotalPages) {
      setEventPage(eventTotalPages);
    }
  }, [eventPage, eventTotalPages]);

  useEffect(() => {
    if (iocPage > iocTotalPages) {
      setIocPage(iocTotalPages);
    }
  }, [iocPage, iocTotalPages]);

  /* ===================== UI ===================== */
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div
        className="layout-container mx-auto px-6 py-10"
        style={{ "--layout-width": `${layoutWidth}vw` }}
      >
        {/* HERO */}
        <section className="glass-card neon-panel relative overflow-hidden rounded-[32px] p-8 shadow-soft">
          <div className="cyber-grid" aria-hidden="true"></div>
          <div className="cyber-scan" aria-hidden="true"></div>
          <div className="cyber-orb orb-one" aria-hidden="true"></div>
          <div className="cyber-orb orb-two" aria-hidden="true"></div>
          <div className="cyber-nodes" aria-hidden="true">
            <span className="cyber-node node-a"></span>
            <span className="cyber-node node-b"></span>
            <span className="cyber-node node-c"></span>
            <span className="cyber-node node-d"></span>
          </div>
          <TopNav theme={theme} onToggleTheme={toggleTheme} />

          <div className="mt-8">
            <h1 className="text-5xl font-extrabold">
              <span className="hero-title">Cyber Threat Intelligence Force.</span>
            </h1>
            <p className="mt-4 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              Cyber Threat Intelligence Force turns public threat reporting into a prioritized
              view for defenders in a single workspace. It collects open-source intelligence,
              cleans and normalizes text, and scores events by incident type, sector, severity,
              and confidence. Analysts can validate indicators against internal telemetry, link
              related activity, and brief leadership with evidence-backed context. The platform
              stays explainable and audit-friendly, helping teams reduce noise while focusing on
              real risk.
            </p>
          </div>

          <div className="mt-8 flex items-center gap-6">
            <Link
              to="/intelligence-docs#architecture"
              className="neon-pill rounded-full bg-lime-300 px-6 py-3 text-sm font-semibold text-slate-900"
            >
              How it works?
            </Link>
            <span className="text-sm">{health}</span>
          </div>
        </section>

        {/* METRICS */}
        <section className="relative mt-10 overflow-hidden rounded-3xl">
          <div className="panel-grid subtle" aria-hidden="true"></div>
          <div className="panel-scan micro" aria-hidden="true"></div>
          <div className="data-stream" aria-hidden="true"></div>
          <div className="relative z-10 grid gap-4 sm:grid-cols-3">
            {[
              ["Total Events", summary.total_events],
              ["Campaigns", summary.campaign_count],
              ["Indicators of Compromise", summary.ioc_count],
            ].map(([k, v]) => (
              <div
                key={k}
                className="neon-card rounded-3xl bg-white/80 p-6 dark:bg-slate-900/70"
              >
                <p className="text-sm text-slate-500 dark:text-slate-400">{k}</p>
                <p className="text-2xl font-semibold">{formatNumber(v)}</p>
              </div>
            ))}
          </div>
        </section>

        {/* EVENTS */}
        <section className="neon-card cyber-panel mt-10 rounded-3xl bg-white/80 p-6 dark:bg-slate-900/70">
          <div className="panel-grid" aria-hidden="true"></div>
          <div className="panel-scan" aria-hidden="true"></div>
          <div className="data-stream alt" aria-hidden="true"></div>
          <div className="relative z-10">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold hover-title">Event Intelligence</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Prioritized events with severity, sector, and confidence
                </p>
              </div>
              <Link
                to="/intelligence-docs#cti"
                className="text-xs text-emerald-400 hover:underline"
              >
                Cyber Threat Intelligence Lifecycle
              </Link>
            </div>

            <div className="mt-4 space-y-2">
              <div className="table-row header">
                <button
                  onClick={() => toggleSort(setEventSort, "event_id")}
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Event ID
                  <SortIndicator
                    active={isActiveSort(eventSort, "event_id")}
                    direction={eventSort.direction}
                  />
                </button>
                <button
                  onClick={() => toggleSort(setEventSort, "incident_type")}
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Incident Type
                  <SortIndicator
                    active={isActiveSort(eventSort, "incident_type")}
                    direction={eventSort.direction}
                  />
                </button>
                <button
                  onClick={() => toggleSort(setEventSort, "sector")}
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Sector
                  <SortIndicator
                    active={isActiveSort(eventSort, "sector")}
                    direction={eventSort.direction}
                  />
                </button>
                <button
                  onClick={() =>
                    toggleSort(setEventSort, "severity_label", "desc")
                  }
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Severity
                  <SortIndicator
                    active={isActiveSort(eventSort, "severity_label")}
                    direction={eventSort.direction}
                  />
                </button>
                <button
                  onClick={() =>
                    toggleSort(setEventSort, "confidence", "desc")
                  }
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Confidence
                  <SortIndicator
                    active={isActiveSort(eventSort, "confidence")}
                    direction={eventSort.direction}
                  />
                </button>
              </div>
              {sortedEvents.length ? (
                sortedEvents.map((e) => (
                  <div key={e.event_id} className="table-row">
                    <span>{e.event_id?.slice(0, 8)}</span>
                    <span>{e.incident_type}</span>
                    <span>{e.sector}</span>
                    <span className={severityBadge(e.severity_label)}>
                      {e.severity_label}
                    </span>
                    <span>{toNumber(e.confidence).toFixed(2)}</span>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950">
                  No events yet. Run the pipeline with real open-source intelligence sources.
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
                  {eventTotalCount} items
                </span>
                <button
                  onClick={() => setEventPage((page) => Math.min(eventTotalPages, page + 1))}
                  disabled={eventPage >= eventTotalPages}
                  className="rounded-full border border-slate-200 px-4 py-2 text-xs disabled:opacity-50 dark:border-slate-700"
                >
                  Next
                </button>
              </div>
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
        </section>

        {/* INDICATORS */}
        <section className="neon-card cyber-panel mt-10 rounded-3xl bg-white/80 p-6 dark:bg-slate-900/70">
          <div className="panel-grid" aria-hidden="true"></div>
          <div className="panel-scan" aria-hidden="true"></div>
          <div className="data-stream" aria-hidden="true"></div>
          <div className="relative z-10">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold hover-title">
                  Indicators of Compromise Explorer
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Observable artifacts extracted from public sources
                </p>
              </div>
              <Link
                to="/intelligence-docs#ioc"
                className="text-xs text-emerald-400 hover:underline"
              >
                What is an Indicator of Compromise?
              </Link>
            </div>

            <div className="mt-4 space-y-2">
              <div className="ioc-row header">
                <button
                  onClick={() => toggleSort(setIocSort, "value")}
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Indicator
                  <SortIndicator
                    active={isActiveSort(iocSort, "value")}
                    direction={iocSort.direction}
                  />
                </button>
                <button
                  onClick={() => toggleSort(setIocSort, "ioc_type")}
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Type
                  <SortIndicator
                    active={isActiveSort(iocSort, "ioc_type")}
                    direction={iocSort.direction}
                  />
                </button>
                <button
                  onClick={() => toggleSort(setIocSort, "confidence", "desc")}
                  className="flex items-center gap-2 text-left transition hover:text-slate-900 dark:hover:text-white"
                >
                  Confidence
                  <SortIndicator
                    active={isActiveSort(iocSort, "confidence")}
                    direction={iocSort.direction}
                  />
                </button>
              </div>
              {sortedIocs.length ? (
                sortedIocs.map((ioc, i) => (
                  <div key={i} className="ioc-row">
                    <span className="truncate">
                      {ioc.normalized_value || ioc.value}
                    </span>
                    <span>{ioc.ioc_type}</span>
                    <span>{toNumber(ioc.confidence).toFixed(2)}</span>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-white/60 p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950">
                  No Indicators of Compromise yet. Pipeline output required.
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
                  {iocTotalCount} items
                </span>
                <button
                  onClick={() => setIocPage((page) => Math.min(iocTotalPages, page + 1))}
                  disabled={iocPage >= iocTotalPages}
                  className="rounded-full border border-slate-200 px-4 py-2 text-xs disabled:opacity-50 dark:border-slate-700"
                >
                  Next
                </button>
              </div>
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
          </div>
        </section>

        {/* REPORT */}
        <section className="neon-card cyber-panel mt-10 rounded-3xl bg-white/80 p-6 dark:bg-slate-900/70">
          <div className="panel-grid subtle" aria-hidden="true"></div>
          <div className="panel-scan slow" aria-hidden="true"></div>
          <div className="data-stream alt" aria-hidden="true"></div>
          <div className="relative z-10">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-xl font-semibold">Latest Report</h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Plain language summary and raw data
                </p>
              </div>
              <button
                onClick={loadReport}
                className="rounded-full border px-4 py-2 text-xs dark:border-slate-700"
              >
                Refresh
              </button>
            </div>

            <div className="mt-4 rounded-2xl border border-slate-200/70 bg-white/70 p-4 text-sm text-slate-600 dark:border-slate-700/60 dark:bg-slate-950 dark:text-slate-300">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                Detailed Summary (Plain Words)
              </h3>
              {reportSummary.length ? (
                <ul className="mt-3 space-y-2 text-sm">
                  {reportSummary.map((item) => (
                    <li key={item.title} className="flex gap-2">
                      <span className="mt-2 h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
                      <span>
                        <span className="font-semibold text-slate-900 dark:text-white">
                          {item.title}:
                        </span>{" "}
                        {item.detail}
                      </span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-3 leading-relaxed">
                  Report summary will appear after the latest report is generated.
                </p>
              )}
            </div>

            <details className="mt-4">
              <summary className="cursor-pointer text-xs font-semibold text-slate-500 dark:text-slate-400">
                View raw report JSON
              </summary>
              <pre className="code-block mt-4">{report}</pre>
            </details>
          </div>
        </section>

        <footer className="mt-10 text-center text-xs text-slate-500 dark:text-slate-400">
          Built for blue-team operations | Open-source intelligence only | Analyst assist
        </footer>
      </div>
    </div>
  );
}
