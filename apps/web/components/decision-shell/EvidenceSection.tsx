import type { FormEvent } from "react";

import type { DecisionWorkspaceController } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function EvidenceSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">Evidence</p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Evidence register
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Capture source-backed facts, research notes, or validation inputs
            that support or challenge the current decision. AI generation adds
            evidence leads with concrete source directions, not verified
            retrieval.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 rounded-full border border-black/10 bg-paper px-3 py-2 text-xs text-ink/70">
            <span>Count</span>
            <input
              type="number"
              min={1}
              max={7}
              value={controller.evidenceGenerationCount}
              onChange={(event) =>
                controller.setEvidenceGenerationCount(event.target.value)
              }
              disabled={!controller.activeDecision || controller.isGeneratingEvidence}
              className="w-12 bg-transparent text-right outline-none"
            />
          </label>

          <button
            type="button"
            onClick={() => void controller.generateEvidence()}
            disabled={
              !controller.canGenerateEvidence || controller.isGeneratingEvidence
            }
            className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
          >
            {controller.isGeneratingEvidence
              ? "Generating..."
              : controller.evidence.length > 0
                ? "Add AI Evidence"
                : "Generate Evidence"}
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-2xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
        Web research uses a free HTML search provider by default. It is useful
        for local work, but results can be brittle and still need verification.
      </div>

      {controller.evidenceSuccessMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {controller.evidenceSuccessMessage}
        </div>
      ) : null}

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
                  {evidence.source_url ? (
                    <>
                      <p className="mt-3 text-xs uppercase tracking-[0.2em] text-steel">
                        URL
                      </p>
                      <a
                        href={evidence.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="mt-1 block break-all text-sm text-ink underline underline-offset-4"
                      >
                        {evidence.source_url}
                      </a>
                    </>
                  ) : null}
                  {evidence.source_query ? (
                    <>
                      <p className="mt-3 text-xs uppercase tracking-[0.2em] text-steel">
                        Query
                      </p>
                      <p className="mt-1 text-sm text-ink/70">{evidence.source_query}</p>
                    </>
                  ) : null}
                  {evidence.excerpt ? (
                    <>
                      <p className="mt-3 text-xs uppercase tracking-[0.2em] text-steel">
                        Excerpt
                      </p>
                      <p className="mt-1 text-sm leading-6 text-ink/75">
                        {evidence.excerpt}
                      </p>
                    </>
                  ) : null}
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

        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Research Focus
          </span>
          <textarea
            value={controller.evidenceResearchFocus}
            onChange={(event) => controller.setEvidenceResearchFocus(event.target.value)}
            disabled={!controller.activeDecision || controller.isGeneratingEvidence}
            rows={2}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="What should the web research validate or compare?"
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Seed URLs
          </span>
          <textarea
            value={controller.evidenceSeedUrlsText}
            onChange={(event) => controller.setEvidenceSeedUrlsText(event.target.value)}
            disabled={!controller.activeDecision || controller.isGeneratingEvidence}
            rows={3}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="One URL per line if you want the backend to read specific sources first."
          />
        </label>

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
