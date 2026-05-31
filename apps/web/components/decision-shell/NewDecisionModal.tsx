import type { FormEvent } from "react";

import type { DecisionWorkspaceController } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function NewDecisionModal({ controller }: Props) {
  if (!controller.isCreateDecisionOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-ink/45 px-4 py-8 backdrop-blur-sm">
      <div className="w-full max-w-5xl rounded-[28px] border border-black/10 bg-white p-6 shadow-panel">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-steel">
              New Decision
            </p>
            <h3 className="mt-2 font-[family-name:var(--font-heading)] text-3xl font-semibold text-ink">
              Add another workspace entry
            </h3>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
              Keep the active analysis separate from intake. Create the decision
              record here, then continue the analysis in the main workspace.
            </p>
          </div>
          <button
            type="button"
            onClick={controller.closeCreateDecisionModal}
            className="rounded-full border border-black/10 px-4 py-2 text-sm font-medium text-ink transition hover:border-ink hover:bg-ink hover:text-paper"
          >
            Close
          </button>
        </div>

        <form
          onSubmit={(event: FormEvent<HTMLFormElement>) => {
            event.preventDefault();
            void controller.createDecision();
          }}
          className="mt-6 space-y-4"
        >
          <div className="grid gap-4 xl:grid-cols-2">
            <label className="block">
              <span className="text-xs uppercase tracking-[0.3em] text-steel">
                Title
              </span>
              <input
                value={controller.decisionDraft.title}
                onChange={(event) =>
                  controller.setDecisionDraft((current) => ({
                    ...current,
                    title: event.target.value,
                  }))
                }
                required
                className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                placeholder="PostgreSQL vs MySQL vs SQL Server"
              />
            </label>

            <label className="block">
              <span className="text-xs uppercase tracking-[0.3em] text-steel">
                Decision Brief
              </span>
              <input
                value={controller.decisionDraft.decision_brief}
                onChange={(event) =>
                  controller.setDecisionDraft((current) => ({
                    ...current,
                    decision_brief: event.target.value,
                  }))
                }
                required
                className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                placeholder="Short summary of the decision and what is being evaluated."
              />
            </label>
          </div>

          <label className="block">
            <span className="text-xs uppercase tracking-[0.3em] text-steel">
              Question
            </span>
            <textarea
              value={controller.decisionDraft.question}
              onChange={(event) =>
                controller.setDecisionDraft((current) => ({
                  ...current,
                  question: event.target.value,
                }))
              }
              required
              rows={3}
              className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
              placeholder="Which primary OLTP database should we standardize on for the next product phase?"
            />
          </label>

          <label className="block">
            <span className="text-xs uppercase tracking-[0.3em] text-steel">
              Context
            </span>
            <textarea
              value={controller.decisionDraft.context}
              onChange={(event) =>
                controller.setDecisionDraft((current) => ({
                  ...current,
                  context: event.target.value,
                }))
              }
              required
              rows={4}
              className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
              placeholder="Describe the workload, operational constraints, hosting assumptions, and success criteria."
            />
          </label>

          {controller.decisionErrorMessage ? (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
              {controller.decisionErrorMessage}
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={controller.isSubmittingDecision}
              className="rounded-full bg-ember px-5 py-3 text-sm font-semibold text-paper transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {controller.isSubmittingDecision ? "Saving..." : "Create Decision"}
            </button>
            <button
              type="button"
              onClick={controller.closeCreateDecisionModal}
              className="rounded-full border border-black/10 px-5 py-3 text-sm font-medium text-ink transition hover:border-ink hover:bg-ink hover:text-paper"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
