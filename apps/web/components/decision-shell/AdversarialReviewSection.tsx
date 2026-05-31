import {
  formatTimestamp,
  severityLabel,
  type DecisionWorkspaceController,
} from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function AdversarialReviewSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Adversarial Review
          </p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Structured adversarial critique
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Stress-test the current decision state, assumptions, and tradeoff
            matrix before moving toward a recommendation.
          </p>
        </div>

        <button
          type="button"
          onClick={() => void controller.generateAdversarialReview()}
          disabled={
            !controller.canGenerateAdversarialReview ||
            controller.isGeneratingAdversarialReview
          }
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isGeneratingAdversarialReview
            ? "Generating..."
            : "Generate Adversarial Review"}
        </button>
      </div>

      <p className="mt-3 text-sm text-ink/65">
        Generate Adversarial Review replaces the current critique for this
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
            {controller.canGenerateAdversarialReview ? "Ready" : "Incomplete"}
          </p>
        </div>
      </div>

      {controller.activeDecision && !controller.canGenerateAdversarialReview ? (
        <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Adversarial review generation requires a completed tradeoff matrix in
          addition to options, criteria, and assumptions.
        </div>
      ) : null}

      {controller.adversarialReviewErrorMessage ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.adversarialReviewErrorMessage}
        </div>
      ) : null}

      {controller.adversarialReviewSuccessMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {controller.adversarialReviewSuccessMessage}
        </div>
      ) : null}

      {controller.isLoadingAdversarialReview ? (
        <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
          Loading adversarial review...
        </div>
      ) : controller.adversarialReview ? (
        <div className="mt-6 space-y-5">
          <div className="rounded-2xl border border-black/10 bg-paper p-5">
            <p className="text-xs uppercase tracking-[0.3em] text-steel">
              Review Summary
            </p>
            <p className="mt-3 text-sm leading-7 text-ink/80">
              {controller.adversarialReview.summary}
            </p>
            <div className="mt-4 flex flex-wrap gap-2 text-xs text-ink/65">
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Overall risk {severityLabel(controller.adversarialReview.overall_risk)}
              </span>
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Model {controller.adversarialReview.model}
              </span>
              <span className="rounded-full bg-black/[0.05] px-3 py-1">
                Updated {formatTimestamp(controller.adversarialReview.updated_at)}
              </span>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-2">
            {controller.adversarialReview.findings.map((finding) => (
              <article
                key={finding.id}
                className="rounded-2xl border border-black/10 bg-paper p-5"
              >
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                    {finding.title}
                  </p>
                  <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                    {severityLabel(finding.severity)} severity
                  </span>
                </div>

                <div className="mt-4 space-y-4 text-sm leading-6 text-ink/75">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Critique
                    </p>
                    <p className="mt-2">{finding.critique}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Consequence
                    </p>
                    <p className="mt-2">{finding.consequence}</p>
                  </div>

                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Mitigation Test
                    </p>
                    <p className="mt-2">{finding.mitigation_test}</p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>
      ) : (
        <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
          No adversarial review yet. Generate one once the decision has a
          tradeoff matrix.
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
