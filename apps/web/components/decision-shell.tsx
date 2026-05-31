"use client";

import { AdversarialReviewSection } from "./decision-shell/AdversarialReviewSection";
import { AssumptionsSection } from "./decision-shell/AssumptionsSection";
import { CriteriaSection } from "./decision-shell/CriteriaSection";
import { EvidenceSection } from "./decision-shell/EvidenceSection";
import { ExportSection } from "./decision-shell/ExportSection";
import { NewDecisionModal } from "./decision-shell/NewDecisionModal";
import { OptionsSection } from "./decision-shell/OptionsSection";
import { PlaceholderSection } from "./decision-shell/PlaceholderSection";
import { RecommendationSection } from "./decision-shell/RecommendationSection";
import { TradeoffsSection } from "./decision-shell/TradeoffsSection";
import { useDecisionWorkspace } from "./decision-shell/useDecisionWorkspace";
import { WorkspaceOverview } from "./decision-shell/WorkspaceOverview";
import { WorkspaceSidebar } from "./decision-shell/WorkspaceSidebar";

export function DecisionShell() {
  const controller = useDecisionWorkspace();

  return (
    <>
      <main className="min-h-screen px-4 py-6 md:px-8">
        <div className="mx-auto grid max-w-[1500px] gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <WorkspaceSidebar controller={controller} />

          <section className="rounded-[32px] border border-black/10 bg-white/75 p-6 shadow-panel backdrop-blur">
            <div className="flex flex-col gap-6">
              <ActiveSection controller={controller} />
            </div>
          </section>
        </div>
      </main>

      <NewDecisionModal controller={controller} />
    </>
  );
}

function ActiveSection({ controller }: { controller: ReturnType<typeof useDecisionWorkspace> }) {
  switch (controller.activeSection) {
    case "Overview":
      return <WorkspaceOverview controller={controller} />;
    case "Options":
      return <OptionsSection controller={controller} />;
    case "Criteria":
      return <CriteriaSection controller={controller} />;
    case "Evidence":
      return <EvidenceSection controller={controller} />;
    case "Assumptions":
      return <AssumptionsSection controller={controller} />;
    case "Tradeoffs":
      return <TradeoffsSection controller={controller} />;
    case "Adversarial Review":
      return <AdversarialReviewSection controller={controller} />;
    case "Recommendation":
      return <RecommendationSection controller={controller} />;
    case "Export":
      return <ExportSection controller={controller} />;
    default:
      return <PlaceholderSection controller={controller} section="Export" />;
  }
}
