"use client";

import { AdversarialReviewSection } from "./decision-shell/AdversarialReviewSection";
import { AssumptionsSection } from "./decision-shell/AssumptionsSection";
import { CriteriaSection } from "./decision-shell/CriteriaSection";
import { NewDecisionModal } from "./decision-shell/NewDecisionModal";
import { OptionsSection } from "./decision-shell/OptionsSection";
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
              <WorkspaceOverview controller={controller} />

              <div className="grid gap-4 xl:grid-cols-2">
                <OptionsSection controller={controller} />
                <CriteriaSection controller={controller} />
              </div>

              <AssumptionsSection controller={controller} />
              <TradeoffsSection controller={controller} />
              <AdversarialReviewSection controller={controller} />
              <RecommendationSection controller={controller} />
            </div>
          </section>
        </div>
      </main>

      <NewDecisionModal controller={controller} />
    </>
  );
}
