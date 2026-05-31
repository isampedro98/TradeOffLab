import {
  formatTimestamp,
  type DecisionWorkspaceController,
} from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function WorkspaceOverview({ controller }: Props) {
  return (
    <>
      <div className="rounded-[28px] bg-ink p-6 text-paper">
        <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.35em] text-paper/60">
          Active Decision
        </p>

        <h2 className="mt-3 max-w-3xl font-[family-name:var(--font-heading)] text-3xl font-semibold leading-tight md:text-4xl">
          {controller.activeDecision?.title ??
            "Create a decision to start the workspace."}
        </h2>

        <p className="mt-4 max-w-2xl text-sm text-paper/75">
          {controller.activeDecision?.decision_brief ??
            "The frontend is now tied to persisted records in Postgres through the API. Create a fresh decision frame from structured fields and build the analysis in-place."}
        </p>

        {controller.activeDecision ? (
          <div className="mt-5 flex flex-wrap gap-2 text-xs text-paper/70">
            <span className="rounded-full border border-paper/15 px-3 py-1">
              {controller.activeDecision.id}
            </span>
            <span className="rounded-full border border-paper/15 px-3 py-1">
              {formatTimestamp(controller.activeDecision.created_at)}
            </span>
            <span className="rounded-full border border-paper/15 px-3 py-1">
              Updated {formatTimestamp(controller.activeDecision.updated_at)}
            </span>
            <button
              type="button"
              onClick={() => void controller.deleteDecision()}
              className="rounded-full border border-red-300/50 px-3 py-1 text-red-100 transition hover:border-red-200 hover:bg-red-500/20"
            >
              Delete Decision
            </button>
          </div>
        ) : null}
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <StatCard
          label="Persistence"
          value="Postgres"
          description="Decisions are now stored through the API, not embedded in the UI shell."
        />
        <StatCard
          label="Option Count"
          value={controller.activeDecision ? String(controller.options.length) : "..."}
          description="Candidate options available for the current decision."
        />
        <StatCard
          label="Criteria Count"
          value={
            controller.activeDecision ? String(controller.criteria.length) : "..."
          }
          description="Structured evaluation criteria loaded for this decision."
        />
      </div>

      {controller.decisionErrorMessage && !controller.isCreateDecisionOpen ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.decisionErrorMessage}
        </div>
      ) : null}

      <section className="rounded-[28px] border border-dashed border-black/15 bg-white/65 p-6">
        <p className="text-xs uppercase tracking-[0.3em] text-steel">
          Active Record
        </p>

        {controller.activeDecision ? (
          <div className="mt-4 space-y-5 text-sm text-ink/80">
            <div>
              <p className="font-[family-name:var(--font-heading)] text-3xl font-semibold text-ink">
                {controller.activeDecision.title}
              </p>
              {controller.showDecisionBrief ? (
                <p className="mt-3 max-w-3xl text-lg leading-8 text-ink/80">
                  {controller.activeDecision.decision_brief}
                </p>
              ) : null}
              {controller.showDecisionQuestion ? (
                <p className="mt-3 max-w-3xl leading-7 text-ink/70">
                  {controller.activeDecision.question}
                </p>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-2 text-xs text-ink/65">
              <span className="rounded-full border border-black/10 px-3 py-1">
                Updated {formatTimestamp(controller.activeDecision.updated_at)}
              </span>
            </div>

            <div className="rounded-2xl bg-black/[0.03] p-5">
              <p className="text-xs uppercase tracking-[0.3em] text-steel">
                Context
              </p>
              <p className="mt-3 max-w-4xl leading-7">
                {controller.activeDecision.context}
              </p>
            </div>
          </div>
        ) : (
          <p className="mt-4 text-sm text-ink/65">
            Nothing selected yet. Open New Decision to create a fresh workspace
            entry.
          </p>
        )}
      </section>
    </>
  );
}

function StatCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="rounded-[24px] border border-black/10 bg-paper p-5">
      <p className="text-xs uppercase tracking-[0.3em] text-steel">{label}</p>
      <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
        {value}
      </p>
      <p className="mt-2 text-sm text-ink/70">{description}</p>
    </div>
  );
}
