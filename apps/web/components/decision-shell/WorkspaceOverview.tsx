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

        <p className="mt-4 max-w-3xl text-sm leading-7 text-paper/75">
          {controller.activeDecision?.decision_brief ??
            "The frontend is now tied to persisted records in Postgres through the API. Create a fresh decision frame from structured fields and build the analysis in-place."}
        </p>

        {controller.activeDecision ? (
          <div className="mt-6 space-y-4">
            {controller.showDecisionQuestion ? (
              <div className="rounded-2xl bg-white/[0.03] p-4">
                <p className="text-xs uppercase tracking-[0.3em] text-paper/55">
                  Core Question
                </p>
                <p className="mt-2 text-sm leading-7 text-paper/80">
                  {controller.activeDecision.question}
                </p>
              </div>
            ) : null}

            <div className="rounded-2xl bg-white/[0.03] p-4">
              <p className="text-xs uppercase tracking-[0.3em] text-paper/55">
                Context
              </p>
              <p className="mt-2 text-sm leading-7 text-paper/80">
                {controller.activeDecision.context}
              </p>
            </div>
          </div>
        ) : null}

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
        <StatCard
          label="Evidence Count"
          value={
            controller.activeDecision ? String(controller.evidence.length) : "..."
          }
          description="Source-backed notes and validation leads captured so far."
        />
      </div>

      {controller.decisionErrorMessage && !controller.isCreateDecisionOpen ? (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.decisionErrorMessage}
        </div>
      ) : null}
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
