import { NavLink } from "react-router-dom";
import { cn } from "../lib/utils";

const navItems = [
  { label: "Dashboard", to: "/" },
  { label: "Project Theory", to: "/intelligence-docs" },
];

function ThemeIcon({ theme }) {
  if (theme === "dark") {
    return (
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
    );
  }

  return (
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
  );
}

export default function TopNav({
  theme,
  onToggleTheme,
  layoutWidth,
  onWidthIncrease,
  onWidthDecrease,
  onWidthReset,
  minWidth = 70,
  maxWidth = 100,
  showWidthControls = false,
}) {
  const hasWidthControls =
    showWidthControls &&
    Number.isFinite(layoutWidth) &&
    onWidthIncrease &&
    onWidthDecrease;

  return (
    <nav className="flex flex-wrap items-center justify-between gap-6">
      <div className="flex flex-wrap items-center gap-2 rounded-full bg-white/80 px-4 py-2 text-xs font-semibold text-slate-500 shadow-sm dark:bg-slate-900/70 dark:text-slate-300">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "rounded-full px-3 py-1 transition",
                isActive
                  ? "bg-slate-900 text-white shadow-soft dark:bg-white dark:text-slate-900"
                  : "hover:bg-white/90 dark:hover:bg-slate-800/70"
              )
            }
          >
            {item.label}
          </NavLink>
        ))}
      </div>
      <div className="flex items-center gap-4">
        {hasWidthControls ? (
          <div className="hidden items-center gap-2 rounded-full border border-slate-200/70 bg-white/80 px-3 py-2 text-xs font-semibold text-slate-500 shadow-sm dark:border-slate-700/60 dark:bg-slate-900/70 dark:text-slate-300 md:flex">
            <span className="text-[10px] uppercase tracking-[0.2em] text-slate-400 dark:text-slate-500">
              Width
            </span>
            <button
              onClick={onWidthDecrease}
              disabled={layoutWidth <= minWidth}
              aria-label="Decrease page width"
              className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200/60 text-slate-500 transition hover:-translate-y-0.5 hover:bg-white/70 hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700/60 dark:text-slate-300 dark:hover:bg-slate-800/70"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-3.5 w-3.5"
              >
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
            <span className="tabular-nums text-xs text-slate-700 dark:text-slate-200">
              {layoutWidth}%
            </span>
            <button
              onClick={onWidthIncrease}
              disabled={layoutWidth >= maxWidth}
              aria-label="Increase page width"
              className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-slate-200/60 text-slate-500 transition hover:-translate-y-0.5 hover:bg-white/70 hover:shadow-sm disabled:cursor-not-allowed disabled:opacity-40 dark:border-slate-700/60 dark:text-slate-300 dark:hover:bg-slate-800/70"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-3.5 w-3.5"
              >
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
            {onWidthReset ? (
              <button
                onClick={onWidthReset}
                className="rounded-full border border-slate-200/60 px-2.5 py-1 text-[10px] uppercase tracking-wide text-slate-500 transition hover:-translate-y-0.5 hover:bg-white/70 hover:shadow-sm dark:border-slate-700/60 dark:text-slate-300 dark:hover:bg-slate-800/70"
              >
                Reset
              </button>
            ) : null}
          </div>
        ) : null}
        <button
          onClick={onToggleTheme}
          aria-label="Toggle theme"
          className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200/70 bg-white/80 text-slate-600 transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-700/60 dark:bg-slate-900/70 dark:text-slate-200"
        >
          <ThemeIcon theme={theme} />
        </button>
      </div>
    </nav>
  );
}
