import {
  confidenceLabel,
  formatTimestamp,
  type DecisionWorkspaceController,
} from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function AssumptionsSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Assumptions
          </p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Structured assumption register
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Persisted assumptions tied to the active decision. Generation runs
            against the stored decision, options, and criteria.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void controller.generateAssumptions()}
          disabled={
            !controller.canRegenerateSelectedAssumptions ||
            controller.isGeneratingAssumptions
          }
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isGeneratingAssumptions
            ? "Generating..."
            : controller.assumptions.length > 0
              ? "Regenerate Selected"
              : "Generate Assumptions"}
        </button>
      </div>

      <p className="mt-3 text-sm text-ink/65">
        {controller.assumptions.length > 0
          ? "Select the assumptions you want to replace, then regenerate only those cards."
          : "Generate an initial assumption set from the current decision, options, and criteria."}
      </p>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <MetricCard label="Options" value={controller.options.length} />
        <MetricCard label="Criteria" value={controller.criteria.length} />
        <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Prerequisites
          </p>
          <p className="mt-2 font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
            {controller.canGenerateAssumptions ? "Ready" : "Incomplete"}
          </p>
        </div>
      </div>

      {controller.activeDecision && !controller.canGenerateAssumptions ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Assumption generation requires at least one option and one criterion.
          This decision currently has {controller.options.length} options and{" "}
          {controller.criteria.length} criteria.
        </div>
      ) : null}

      {controller.assumptions.length > 0 ? (
        <div className="mt-4 flex flex-wrap items-center gap-3 text-sm text-ink/70">
          <span>
            {controller.selectedAssumptionIds.length} of{" "}
            {controller.assumptions.length} selected
          </span>
          <button
            type="button"
            onClick={controller.selectAllAssumptions}
            className="rounded-full border border-black/10 px-3 py-1 text-xs transition hover:border-ink hover:text-ink"
          >
            Select All
          </button>
          <button
            type="button"
            onClick={controller.clearAssumptionSelection}
            className="rounded-full border border-black/10 px-3 py-1 text-xs transition hover:border-ink hover:text-ink"
          >
            Clear
          </button>
        </div>
      ) : null}

      {controller.assumptionErrorMessage ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.assumptionErrorMessage}
        </div>
      ) : null}

      {controller.assumptionSuccessMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {controller.assumptionSuccessMessage}
        </div>
      ) : null}

      <div className="mt-6 grid gap-4 xl:grid-cols-2">
        {controller.isLoadingAssumptions ? (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            Loading assumptions...
          </div>
        ) : controller.assumptions.length > 0 ? (
          controller.assumptions.map((assumption) => (
            <article
              key={assumption.id}
              className="rounded-[24px] border border-black/10 bg-paper p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                    {confidenceLabel(assumption.confidence)} confidence
                  </span>
                  <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                    Updated {formatTimestamp(assumption.updated_at)}
                  </span>
                </div>
                <label className="flex items-center gap-2 text-xs text-ink/70">
                  <input
                    type="checkbox"
                    checked={controller.selectedAssumptionIds.includes(
                      assumption.id,
                    )}
                    onChange={() =>
                      controller.toggleAssumptionSelection(assumption.id)
                    }
                    className="h-4 w-4 rounded border-black/20 text-ink"
                  />
                  Select
                </label>
              </div>

              <p className="mt-4 font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                {assumption.statement}
              </p>

              <div className="mt-4 space-y-4 text-sm leading-6 text-ink/75">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Impact If False
                  </p>
                  <p className="mt-2">{assumption.impact_if_false}</p>
                </div>

                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Validation Method
                  </p>
                  <p className="mt-2">{assumption.validation_method}</p>
                </div>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            No assumptions yet. Generate a set from the persisted decision
            frame once options and criteria are ready.
          </div>
        )}
      </div>
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
