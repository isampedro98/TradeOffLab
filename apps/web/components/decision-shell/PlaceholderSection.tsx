import type { DecisionWorkspaceController, WorkspaceSection } from "./model";

type Props = {
  controller: DecisionWorkspaceController;
  section: Exclude<WorkspaceSection, "Overview" | "Options" | "Criteria" | "Assumptions" | "Tradeoffs" | "Adversarial Review" | "Recommendation">;
};

const copyBySection: Record<Props["section"], { title: string; description: string }> = {
  Evidence: {
    title: "Evidence register",
    description:
      "This section is reserved for source-backed evidence, claims, and validation artifacts. The MVP data model is not wired yet.",
  },
  Export: {
    title: "Decision export",
    description:
      "Markdown and JSON export are the next closing step for the MVP. The workflow artifacts are now ready to feed that output.",
  },
};

export function PlaceholderSection({ controller, section }: Props) {
  const copy = copyBySection[section];

  return (
    <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-steel">{section}</p>
        <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
          {copy.title}
        </h3>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
          {copy.description}
        </p>
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <StatCard label="Decision" value={controller.activeDecision?.title ?? "None"} />
        <StatCard label="Options" value={String(controller.options.length)} />
        <StatCard label="Criteria" value={String(controller.criteria.length)} />
      </div>

      <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
        {section === "Export"
          ? "Export is intentionally deferred until the recommendation flow is stable."
          : "Evidence is intentionally deferred until the MVP synthesis flow is complete."}
      </div>
    </section>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-black/10 bg-paper p-5">
      <p className="text-xs uppercase tracking-[0.3em] text-steel">{label}</p>
      <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
        {value}
      </p>
    </div>
  );
}
