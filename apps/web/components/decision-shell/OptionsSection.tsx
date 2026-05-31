import type { FormEvent } from "react";

import type { DecisionWorkspaceController } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function OptionsSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">Options</p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Candidate options
          </h3>
        </div>
        <span className="rounded-full bg-black/[0.04] px-3 py-1 text-xs text-ink/70">
          {controller.options.length}
        </span>
      </div>

      <div className="mt-5 space-y-3">
        {controller.isLoadingOptions ? (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            Loading options...
          </div>
        ) : controller.options.length > 0 ? (
          controller.options.map((option) => (
            <article
              key={option.id}
              className="rounded-2xl border border-black/10 bg-paper p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                    {option.name}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-ink/75">
                    {option.description}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void controller.deleteOption(option.id)}
                  className="rounded-full border border-black/10 px-3 py-1 text-xs text-ink/65 transition hover:border-ink hover:text-ink"
                >
                  Delete
                </button>
              </div>
            </article>
          ))
        ) : (
          <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
            No options yet. Add the alternatives you want to compare.
          </div>
        )}
      </div>

      <form
        onSubmit={(event: FormEvent<HTMLFormElement>) => {
          event.preventDefault();
          void controller.createOption();
        }}
        className="mt-5 space-y-4"
      >
        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Option Name
          </span>
          <input
            value={controller.optionDraft.name}
            onChange={(event) =>
              controller.setOptionDraft((current) => ({
                ...current,
                name: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="PostgreSQL"
          />
        </label>

        <label className="block">
          <span className="text-xs uppercase tracking-[0.3em] text-steel">
            Description
          </span>
          <textarea
            value={controller.optionDraft.description}
            onChange={(event) =>
              controller.setOptionDraft((current) => ({
                ...current,
                description: event.target.value,
              }))
            }
            required
            disabled={!controller.activeDecision}
            rows={3}
            className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
            placeholder="Summarize why this option belongs in the decision set."
          />
        </label>

        {controller.optionErrorMessage ? (
          <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            {controller.optionErrorMessage}
          </div>
        ) : null}

        <button
          type="submit"
          disabled={!controller.activeDecision || controller.isSubmittingOption}
          className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
        >
          {controller.isSubmittingOption ? "Saving..." : "Add Option"}
        </button>
      </form>
    </section>
  );
}
