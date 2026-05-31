import {
  formatTimestamp,
  measurementTypeLabel,
  type DecisionWorkspaceController,
} from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function TradeoffsSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Tradeoffs
          </p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Structured tradeoff matrix
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Generate criterion-by-option assessments from the stored decision
            frame, assumptions, and weighted criteria.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void controller.generateTradeoffMatrix()}
          disabled={
            !controller.canGenerateTradeoffMatrix ||
            controller.isGeneratingTradeoffMatrix
          }
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isGeneratingTradeoffMatrix
            ? "Generating..."
            : "Generate Tradeoff Matrix"}
        </button>
      </div>

      <p className="mt-3 text-sm text-ink/65">
        Generate Tradeoff Matrix replaces the current matrix for this decision.
      </p>

      <div className="mt-4 grid gap-3 md:grid-cols-4">
        <MetricCard label="Options" value={controller.options.length} />
        <MetricCard label="Criteria" value={controller.criteria.length} />
        <MetricCard label="Assumptions" value={controller.assumptions.length} />
        <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Prerequisites
          </p>
          <p className="mt-2 font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
            {controller.canGenerateTradeoffMatrix ? "Ready" : "Incomplete"}
          </p>
        </div>
      </div>

      {controller.activeDecision && !controller.canGenerateTradeoffMatrix ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Tradeoff matrix generation requires at least one option, one
          criterion, and one assumption.
        </div>
      ) : null}

      {controller.tradeoffMatrixErrorMessage ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.tradeoffMatrixErrorMessage}
        </div>
      ) : null}

      {controller.tradeoffMatrixSuccessMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {controller.tradeoffMatrixSuccessMessage}
        </div>
      ) : null}

      {controller.isLoadingTradeoffMatrix ? (
        <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
          Loading tradeoff matrix...
        </div>
      ) : controller.tradeoffMatrix ? (
        <div className="mt-6 space-y-5">
          <div className="rounded-2xl border border-black/10 bg-paper p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-steel">
              Matrix Summary
            </p>
            <p className="mt-3 text-sm leading-7 text-ink/80">
              {controller.tradeoffMatrix.summary}
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-ink/65">
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                {controller.tradeoffMatrix.scoring_scale_label}
              </span>
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Model {controller.tradeoffMatrix.model}
              </span>
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Updated {formatTimestamp(controller.tradeoffMatrix.updated_at)}
              </span>
            </div>
          </div>

          <div className="space-y-4">
            {controller.criteria.map((criterion) => {
              const criterionAssessments =
                controller.tradeoffMatrix?.assessments.filter(
                  (assessment) => assessment.criterion_id === criterion.id,
                ) ?? [];

              if (criterionAssessments.length === 0) {
                return null;
              }

              return (
                <section
                  key={criterion.id}
                  className="rounded-2xl border border-black/10 bg-paper p-5"
                >
                  <div className="flex flex-wrap gap-2">
                    <p className="font-[family-name:var(--font-heading)] text-xl font-semibold text-ink">
                      {criterion.name}
                    </p>
                    <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                      Weight {criterion.weight}
                    </span>
                    <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                      {measurementTypeLabel(criterion.measurement_type)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-ink/70">
                    {criterion.description}
                  </p>

                  <div className="mt-5 grid gap-4 xl:grid-cols-2">
                    {criterionAssessments.map((assessment) => {
                      const option = controller.optionMap.get(assessment.option_id);

                      return (
                        <article
                          key={assessment.id}
                          className="rounded-2xl border border-black/10 bg-white/70 p-4"
                        >
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                              {option?.name ?? assessment.option_id}
                            </p>
                            <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                              Score {assessment.score.toFixed(1)}
                            </span>
                          </div>
                          <p className="mt-3 text-sm leading-6 text-ink/75">
                            {assessment.rationale}
                          </p>
                        </article>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
          No tradeoff matrix yet. Generate one once the decision has options,
          criteria, and assumptions.
        </div>
      )}
    </section>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
      <p className="text-xs uppercase tracking-[0.3em] text-steel">{label}</p>
      <p className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
        {value}
      </p>
    </div>
  );
}
