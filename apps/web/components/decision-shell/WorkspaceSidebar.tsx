import { sections, type DecisionWorkspaceController } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function WorkspaceSidebar({ controller }: Props) {
  return (
    <aside className="rounded-[28px] border border-black/10 bg-white/70 p-5 shadow-panel backdrop-blur">
      <div className="mb-6">
        <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.35em] text-steel">
          TradeOffLab
        </p>
        <h1 className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
          Decision Lab
        </h1>
      </div>

      <nav className="space-y-2">
        {sections.map((section, index) => (
          <div
            key={section}
            className={`rounded-2xl px-4 py-3 text-sm ${
              index === 0 ? "bg-ink text-paper" : "bg-black/[0.03] text-ink/80"
            }`}
          >
            {section}
          </div>
        ))}
      </nav>

      <div className="mt-6 border-t border-black/10 pt-5">
        <div className="mb-3 flex items-center justify-between">
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Decisions
          </p>
          <div className="flex items-center gap-2">
            <span className="rounded-full bg-black/[0.04] px-2 py-1 text-xs text-ink/70">
              {controller.decisions.length}
            </span>
            <button
              type="button"
              onClick={controller.openCreateDecisionModal}
              className="rounded-full border border-black/10 px-3 py-1 text-xs font-medium text-ink transition hover:border-ink hover:bg-ink hover:text-paper"
            >
              New
            </button>
          </div>
        </div>

        <div className="space-y-2">
          {controller.decisions.map((decision) => {
            const isActive = decision.id === controller.activeDecisionId;

            return (
              <button
                key={decision.id}
                type="button"
                onClick={() => controller.setActiveDecisionId(decision.id)}
                className={`w-full rounded-2xl border px-3 py-3 text-left transition ${
                  isActive
                    ? "border-ink bg-ink text-paper"
                    : "border-black/10 bg-white/60 text-ink hover:bg-black/[0.03]"
                }`}
              >
                <p className="font-[family-name:var(--font-heading)] text-sm font-semibold">
                  {decision.title}
                </p>
                <p
                  className={`mt-2 line-clamp-2 text-xs ${
                    isActive ? "text-paper/75" : "text-ink/65"
                  }`}
                >
                  {decision.decision_brief}
                </p>
              </button>
            );
          })}

          {!controller.isLoading && controller.decisions.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-black/15 px-3 py-4 text-sm text-ink/65">
              No persisted decisions yet.
            </div>
          ) : null}
        </div>
      </div>
    </aside>
  );
}
