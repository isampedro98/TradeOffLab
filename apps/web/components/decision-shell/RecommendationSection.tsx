import {
  formatTimestamp,
  recommendationConfidenceLabel,
  type DecisionWorkspaceController,
} from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function RecommendationSection({ controller }: Props) {
  const recommendedOption = controller.recommendationMemo
    ? controller.optionMap.get(controller.recommendationMemo.recommended_option_id)
    : null;
  const fallbackOption =
    controller.recommendationMemo?.fallback_option_id != null
      ? controller.optionMap.get(controller.recommendationMemo.fallback_option_id)
      : null;

  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Recommendation
          </p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Conditional recommendation memo
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Synthesize the tradeoff matrix and adversarial critique into a
            conditional recommendation with a fallback path.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void controller.generateRecommendationMemo()}
          disabled={
            !controller.canGenerateRecommendationMemo ||
            controller.isGeneratingRecommendationMemo
          }
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isGeneratingRecommendationMemo
            ? "Generating..."
            : "Generate Recommendation Memo"}
        </button>
      </div>

      <p className="mt-3 text-sm text-ink/65">
        Generate Recommendation Memo replaces the current memo for this
        decision.
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
            {controller.canGenerateRecommendationMemo ? "Ready" : "Incomplete"}
          </p>
        </div>
      </div>

      {controller.activeDecision && !controller.canGenerateRecommendationMemo ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Recommendation memo generation requires a completed adversarial
          review in addition to the tradeoff matrix, options, criteria, and
          assumptions.
        </div>
      ) : null}

      {controller.recommendationMemoErrorMessage ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.recommendationMemoErrorMessage}
        </div>
      ) : null}

      {controller.recommendationMemoSuccessMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {controller.recommendationMemoSuccessMessage}
        </div>
      ) : null}

      {controller.isLoadingRecommendationMemo ? (
        <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
          Loading recommendation memo...
        </div>
      ) : controller.recommendationMemo ? (
        <div className="mt-6 space-y-5">
          <div className="rounded-2xl border border-black/10 bg-paper p-5">
            <div className="flex flex-wrap items-center gap-2">
              <p className="font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                {recommendedOption?.name ?? controller.recommendationMemo.recommended_option_id}
              </p>
              <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                {recommendationConfidenceLabel(controller.recommendationMemo.confidence)} confidence
              </span>
              {fallbackOption ? (
                <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                  Fallback {fallbackOption.name}
                </span>
              ) : null}
            </div>

            <p className="mt-4 text-sm leading-7 text-ink/80">
              {controller.recommendationMemo.rationale}
            </p>

            <div className="mt-4 flex flex-wrap gap-2 text-xs text-ink/65">
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Model {controller.recommendationMemo.model}
              </span>
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Updated {formatTimestamp(controller.recommendationMemo.updated_at)}
              </span>
            </div>
          </div>

          <div className="rounded-2xl border border-black/10 bg-paper p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-steel">
              Conditions
            </p>
            <div className="mt-4 space-y-3">
              {controller.recommendationMemo.conditions.map((condition) => (
                <div
                  key={condition.id}
                  className="rounded-2xl border border-black/10 bg-white/70 px-4 py-4 text-sm leading-6 text-ink/75"
                >
                  {condition.statement}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
          No recommendation memo yet. Generate one once the decision has an
          adversarial review.
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
