import type { FormEvent } from "react";

import type { DecisionWorkspaceController } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function EvidenceSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">Evidence</p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Evidence register
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Capture source-backed facts, research notes, or validation inputs
            that support or challenge the current decision.
          </p>
        </div>
        <span className="rounded-full bg-black/[0.04] px-3 py-1 text-xs text-ink/70">
          {controller.evidence.length}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {controller.isLoadingEvidence ? (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            Loading evidence...
          </div>
        ) : controller.evidence.length > 0 ? (
          controller.evidence.map((evidence) => (
            <article
              key={evidence.id}
              className="rounded-2xl border border-black/10 bg-paper p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                    {evidence.title}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-ink/75">
                    {evidence.summary}
                  </p>
                  <p className="mt-3 text-xs uppercase tracking-[0.2em] text-steel">
                    Source
                  </p>
                  <p className="mt-1 text-sm text-ink/70">{evidence.source}</p>
                </div>
                <button
                  type="button"
                  onClick={() => void controller.deleteEvidence(evidence.id)}
                  className="rounded-full border border-black/10 px-3 py-1 text-xs text-ink/65 transition hover:border-ink hover:text-ink"
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            No evidence yet. Add short, source-backed records that can support
            the final recommendation and export.
          </div>
        )}
      </div>

      <form
        onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          void controller.createEvidence();
        }}
        className="mt-5 space-y-4"
      >
        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Evidence Title
          </span>
          <input
            value={controller.evidenceDraft.title}
            onChange={(event) =>
              controller.setEvidenceDraft((current) => ({
                ...current,
                title: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="Managed hosting maturity across major clouds"
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Summary
          </span>
          <textarea
            value={controller.evidenceDraft.summary}
            onChange={(event) =>
              controller.setEvidenceDraft((current) => ({
                ...current,
                summary: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            rows={3}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="Summarize the evidence and why it matters."
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Source
          </span>
          <input
            value={controller.evidenceDraft.source}
            onChange={(event) =>
              controller.setEvidenceDraft((current) => ({
                ...current,
                source: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="Internal architecture notes"
          />
        </label>

        {controller.evidenceErrorMessage ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {controller.evidenceErrorMessage}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={!controller.activeDecision || controller.isSubmittingEvidence}
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isSubmittingEvidence ? "Saving..." : "Add Evidence"}
        </button>
      </form>
    </section>
  );
}
