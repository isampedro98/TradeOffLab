import type { FormEvent } from "react";

import {
  criterionMeasurementTypes,
  measurementTypeLabel,
  type DecisionWorkspaceController,
} from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function CriteriaSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">
            Criteria
          </p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Evaluation criteria
          </h3>
        </div>
        <span className="rounded-full bg-black/[0.04] px-3 py-1 text-xs text-ink/70">
          {controller.criteria.length}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {controller.isLoadingCriteria ? (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            Loading criteria...
          </div>
        ) : controller.criteria.length > 0 ? (
          controller.criteria.map((criterion) => (
            <article
              key={criterion.id}
              className="rounded-2xl border border-black/10 bg-paper p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex flex-wrap gap-2">
                    <p className="font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                      {criterion.name}
                    </p>
                    <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                      Weight {criterion.weight}
                    </span>
                    <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                      {measurementTypeLabel(criterion.measurement_type)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-ink/75">
                    {criterion.description}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void controller.deleteCriterion(criterion.id)}
                  className="rounded-full border border-black/10 px-3 py-1 text-xs text-ink/65 transition hover:border-ink hover:text-ink"
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            No criteria yet. Add the dimensions that will drive the tradeoff.
          </div>
        )}
      </div>

      <form
        onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          void controller.createCriterion();
        }}
        className="mt-5 space-y-4"
      >
        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Criterion Name
          </span>
          <input
            value={controller.criterionDraft.name}
            onChange={(event) =>
              controller.setCriterionDraft((current) => ({
                ...current,
                name: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="Implementation Risk"
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Description
          </span>
          <textarea
            value={controller.criterionDraft.description}
            onChange={(event) =>
              controller.setCriterionDraft((current) => ({
                ...current,
                description: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            rows={3}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="Explain how this criterion should be evaluated."
          />
        </label>

        <div className="grid gap-4 md:grid-cols-2">
          <label className="block">
            <span className="text-xs uppercase tracking-[0.3em] text-steel">
              Weight
            </span>
            <input
              value={controller.criterionDraft.weight}
              onChange={(event) =>
                controller.setCriterionDraft((current) => ({
                  ...current,
                  weight: event.target.value,
                }))
              }
              required
              disabled={!controller.activeDecision}
              inputMode="decimal"
              className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
              placeholder="0.20"
            />
          </label>

          <label className="block">
            <span className="text-xs uppercase tracking-[0.3em] text-steel">
              Measurement
            </span>
            <select
              value={controller.criterionDraft.measurement_type}
              onChange={(event) =>
                controller.setCriterionDraft((current) => ({
                  ...current,
                  measurement_type: event.target.value as typeof current.measurement_type,
                }))
              }
              disabled={!controller.activeDecision}
              className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            >
              {criterionMeasurementTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        {controller.criterionErrorMessage ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {controller.criterionErrorMessage}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={
            !controller.activeDecision || controller.isSubmittingCriterion
          }
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isSubmittingCriterion ? "Saving..." : "Add Criterion"}
        </button>
      </form>
    </section>
  );
}
