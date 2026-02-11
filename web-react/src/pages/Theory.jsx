import TheoryTabs from "../components/theory/TheoryTabs";
import TopNav from "../components/TopNav";
import { useTheme } from "../hooks/useTheme";
import { useLayoutWidth } from "../hooks/useLayoutWidth";

export default function Theory() {
  const { theme, toggleTheme } = useTheme();
  const { width: layoutWidth } = useLayoutWidth();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 dark:bg-slate-950 dark:text-slate-100">
      <div
        className="layout-container mx-auto w-full px-4 sm:px-6 py-8 sm:py-10"
        style={{ "--layout-width": `${layoutWidth}vw` }}
      >
        <section className="glass-card neon-panel relative overflow-hidden rounded-[32px] p-8 shadow-soft">
          <div className="cyber-grid subtle" aria-hidden="true"></div>
          <div className="cyber-scan slow" aria-hidden="true"></div>
          <div className="data-stream alt" aria-hidden="true"></div>
          <div className="cyber-orb orb-one" aria-hidden="true"></div>
          <TopNav theme={theme} onToggleTheme={toggleTheme} />
          <div className="mt-8">
            <h1 className="text-2xl sm:text-3xl font-bold mb-4">Cyber Threat Intelligence Theory</h1>
            <TheoryTabs />
          </div>
        </section>
      </div>
    </div>
  );
}
