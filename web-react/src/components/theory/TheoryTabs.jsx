import { Tabs, TabsList, TabsTrigger, TabsContent } from "../ui/tabs";
import Overview from "./sections/Overview";
import CTIBasics from "./sections/CTIBasics";
import IOCs from "./sections/IOCs";
import Architecture from "./sections/Architecture";
import AIML from "./sections/AIML";
import UseCases from "./sections/UseCases";
import Limitations from "./sections/Limitations";
import { useEffect, useState } from "react";

const tabIds = [
  "overview",
  "cti",
  "ioc",
  "architecture",
  "ai",
  "usecases",
  "limitations",
];

const panelClass =
  "neon-card cyber-panel mt-6 rounded-xl border border-slate-200/70 bg-white/80 p-6 dark:border-slate-700/60 dark:bg-slate-900/70";

function PanelBackdrop() {
  return (
    <>
      <div className="panel-grid subtle" aria-hidden="true"></div>
      <div className="panel-scan micro" aria-hidden="true"></div>
      <div className="data-stream" aria-hidden="true"></div>
    </>
  );
}

export default function TheoryTabs() {
  const [tab, setTab] = useState("overview");

  useEffect(() => {
    const readHash = () => {
      const hash = window.location.hash.replace("#", "");
      if (tabIds.includes(hash)) {
        setTab(hash);
      }
    };

    readHash();
    window.addEventListener("hashchange", readHash);
    return () => window.removeEventListener("hashchange", readHash);
  }, []);

  useEffect(() => {
    const { pathname, search, hash } = window.location;
    const nextHash = `#${tab}`;
    if (hash !== nextHash) {
      window.history.replaceState(null, "", `${pathname}${search}${nextHash}`);
    }
  }, [tab]);

  return (
    <Tabs value={tab} onValueChange={setTab}>
      <TabsList className="neon-tabs">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="cti">Cyber Threat Intelligence</TabsTrigger>
        <TabsTrigger value="ioc">Indicators of Compromise</TabsTrigger>
        <TabsTrigger value="architecture">Architecture</TabsTrigger>
        <TabsTrigger value="ai">Artificial Intelligence</TabsTrigger>
        <TabsTrigger value="usecases">Use Cases</TabsTrigger>
        <TabsTrigger value="limitations">Limitations</TabsTrigger>
      </TabsList>

      <TabsContent value="overview" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <Overview />
        </div>
      </TabsContent>

      <TabsContent value="cti" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <CTIBasics />
        </div>
      </TabsContent>

      <TabsContent value="ioc" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <IOCs />
        </div>
      </TabsContent>

      <TabsContent value="architecture" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <Architecture />
        </div>
      </TabsContent>

      <TabsContent value="ai" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <AIML />
        </div>
      </TabsContent>

      <TabsContent value="usecases" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <UseCases />
        </div>
      </TabsContent>

      <TabsContent value="limitations" className={panelClass}>
        <PanelBackdrop />
        <div className="relative z-10">
          <Limitations />
        </div>
      </TabsContent>

    </Tabs>
  );
}
