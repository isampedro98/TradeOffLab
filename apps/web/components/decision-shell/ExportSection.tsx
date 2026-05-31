import type { DecisionWorkspaceController } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
};

export function ExportSection({ controller }: Props) {
  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-steel">Export</p>
          <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
            Decision dossier export
          </h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
            Export the current decision state as structured JSON or readable
            Markdown. Evidence is kept explicit in the dossier and currently
            exports as an empty section until the register is wired.
          </p>
        </div>

        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => void controller.exportJson()}
            disabled={!controller.activeDecision || controller.isExportingJson}
            className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
          >
            {controller.isExportingJson ? "Exporting JSON..." : "Export JSON"}
          </button>
          <button
            type="button"
            onClick={() => void controller.exportMarkdown()}
            disabled={!controller.activeDecision || controller.isExportingMarkdown}
            className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
          >
            {controller.isExportingMarkdown
              ? "Exporting Markdown..."
              : "Export Markdown"}
          </button>
        </div>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-4">
        <StatCard
          label="Options"
          value={controller.activeDecision ? String(controller.options.length) : "..."}
          description="Candidate options in the current dossier."
        />
        <StatCard
          label="Criteria"
          value={controller.activeDecision ? String(controller.criteria.length) : "..."}
          description="Evaluation criteria captured so far."
        />
        <StatCard
          label="Assumptions"
          value={
            controller.activeDecision ? String(controller.assumptions.length) : "..."
          }
          description="Structured assumptions included in the dossier."
        />
        <StatCard
          label="Evidence"
          value="0"
          description="Reserved in the export schema even before the register exists."
        />
      </div>

      {controller.exportErrorMessage ? (
        <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
          {controller.exportErrorMessage}
        </div>
      ) : null}

      {controller.exportSuccessMessage ? (
        <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
          {controller.exportSuccessMessage}
        </div>
      ) : null}

      <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm leading-7 text-ink/65">
        The export bundle includes `Decision`, `Options`, `Criteria`,
        `Assumptions`, `TradeoffMatrix`, `AdversarialReview`, and
        `RecommendationMemo`. `Evidence` remains present as an explicit empty
        list so the dossier format does not forget it.
      </div>
    </section>
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
      <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
        {value}
      </p>
      <p className="mt-2 text-sm text-ink/70">{description}</p>
    </div>
  );
}
