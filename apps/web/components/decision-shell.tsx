"use client";

import { startTransition, useEffect, useState, type FormEvent } from "react";

const sections = [
  "Overview",
  "Options",
  "Criteria",
  "Assumptions",
  "Evidence",
  "Tradeoffs",
  "Adversarial Review",
  "Recommendation",
  "Export",
];

const decisionTypes = [
  { value: "erp_adoption", label: "ERP Adoption" },
  { value: "architecture", label: "Architecture" },
  { value: "cloud_provider", label: "Cloud Provider" },
  { value: "build_vs_buy", label: "Build vs Buy" },
  { value: "procurement_automation", label: "Procurement Automation" },
  { value: "software_stack", label: "Software Stack" },
  { value: "strategic_technical", label: "Strategic Technical" },
] as const;

type DecisionType = (typeof decisionTypes)[number]["value"];
type DecisionStatus = "draft" | "in_review" | "recommended" | "archived";

type Decision = {
  id: string;
  title: string;
  decision_brief: string;
  question: string;
  context: string;
  type: DecisionType;
  status: DecisionStatus;
  created_at: string;
  updated_at: string;
};

type CreateDecisionPayload = {
  title: string;
  decision_brief: string;
  question: string;
  context: string;
  type: DecisionType;
  status: DecisionStatus;
};

const traceNotes = [
  "Persisted decisions now come from the FastAPI API backed by Postgres.",
  "The ERP bootstrap example can be seeded once and then reused across runs.",
  "This workspace remains structured-first: stored records, explicit fields, no chat transcript.",
];

const initialDraft: CreateDecisionPayload = {
  title: "",
  decision_brief: "",
  question: "",
  context: "",
  type: "erp_adoption",
  status: "draft",
};

function apiUrl(path: string): string {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return `${baseUrl}${path}`;
}

function formatTimestamp(timestamp: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

function typeLabel(type: DecisionType): string {
  return decisionTypes.find((item) => item.value === type)?.label ?? type;
}

function statusClasses(status: DecisionStatus): string {
  switch (status) {
    case "recommended":
      return "bg-emerald-100 text-emerald-900";
    case "in_review":
      return "bg-amber-100 text-amber-900";
    case "archived":
      return "bg-slate-200 text-slate-700";
    default:
      return "bg-sky-100 text-sky-900";
  }
}

export function DecisionShell() {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [activeDecisionId, setActiveDecisionId] = useState<string | null>(null);
  const [draft, setDraft] = useState<CreateDecisionPayload>(initialDraft);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const activeDecision =
    decisions.find((decision) => decision.id === activeDecisionId) ?? null;

  async function loadDecisions(preferredDecisionId?: string) {
    setErrorMessage(null);

    try {
      const response = await fetch(apiUrl("/api/v1/decisions"), {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Failed to load decisions (${response.status})`);
      }

      const payload = (await response.json()) as Decision[];

      startTransition(() => {
        setDecisions(payload);

        if (payload.length === 0) {
          setActiveDecisionId(null);
          return;
        }

        if (
          preferredDecisionId &&
          payload.some((decision) => decision.id === preferredDecisionId)
        ) {
          setActiveDecisionId(preferredDecisionId);
          return;
        }

        if (
          activeDecisionId &&
          payload.some((decision) => decision.id === activeDecisionId)
        ) {
          return;
        }

        setActiveDecisionId(payload[0]?.id ?? null);
      });
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to load decisions.",
      );
    } finally {
      setIsLoading(false);
      setIsSubmitting(false);
      setIsSeeding(false);
    }
  }

  useEffect(() => {
    void loadDecisions();
    // We only want the initial bootstrap fetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleCreateDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setErrorMessage(null);

    try {
      const response = await fetch(apiUrl("/api/v1/decisions"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(draft),
      });

      if (!response.ok) {
        throw new Error(`Failed to create decision (${response.status})`);
      }

      const created = (await response.json()) as Decision;
      setDraft(initialDraft);
      await loadDecisions(created.id);
    } catch (error) {
      setIsSubmitting(false);
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to create decision.",
      );
    }
  }

  async function handleSeedBootstrap() {
    setIsSeeding(true);
    setErrorMessage(null);

    try {
      const response = await fetch(apiUrl("/api/v1/decisions/seed/bootstrap-example"), {
        method: "POST",
      });

      if (!response.ok) {
        throw new Error(`Failed to seed bootstrap decision (${response.status})`);
      }

      const seeded = (await response.json()) as Decision;
      await loadDecisions(seeded.id);
    } catch (error) {
      setIsSeeding(false);
      setErrorMessage(
        error instanceof Error ? error.message : "Failed to seed decision.",
      );
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[260px_minmax(0,1fr)_340px]">
        <aside className="rounded-[28px] border border-black/10 bg-white/70 p-5 shadow-panel backdrop-blur">
          <div className="mb-6">
            <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.35em] text-steel">
              TradeOffLab
            </p>
            <h1 className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
              Decision Lab
            </h1>
          </div>

          <nav className="space-y-2">
            {sections.map((section, index) => (
              <div
                key={section}
                className={`rounded-2xl px-4 py-3 text-sm ${
                  index === 0
                    ? "bg-ink text-paper"
                    : "bg-black/[0.03] text-ink/80"
                }`}
              >
                {section}
              </div>
            ))}
          </nav>

          <div className="mt-6 border-t border-black/10 pt-5">
            <div className="mb-3 flex items-center justify-between">
              <p className="text-xs uppercase tracking-[0.3em] text-steel">
                Decisions
              </p>
              <span className="rounded-full bg-black/[0.04] px-2 py-1 text-xs text-ink/70">
                {decisions.length}
              </span>
            </div>

            <div className="space-y-2">
              {decisions.map((decision) => {
                const isActive = decision.id === activeDecisionId;

                return (
                  <button
                    key={decision.id}
                    type="button"
                    onClick={() => setActiveDecisionId(decision.id)}
                    className={`w-full rounded-2xl border px-3 py-3 text-left transition ${
                      isActive
                        ? "border-ink bg-ink text-paper"
                        : "border-black/10 bg-white/60 text-ink hover:bg-black/[0.03]"
                    }`}
                  >
                    <p className="font-[family-name:var(--font-heading)] text-sm font-semibold">
                      {decision.title}
                    </p>
                    <p
                      className={`mt-2 line-clamp-2 text-xs ${
                        isActive ? "text-paper/75" : "text-ink/65"
                      }`}
                    >
                      {decision.decision_brief}
                    </p>
                  </button>
                );
              })}

              {!isLoading && decisions.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-black/15 px-3 py-4 text-sm text-ink/65">
                  No persisted decisions yet.
                </div>
              ) : null}
            </div>
          </div>
        </aside>

        <section className="rounded-[32px] border border-black/10 bg-white/75 p-6 shadow-panel backdrop-blur">
          <div className="flex flex-col gap-6">
            <div className="rounded-[28px] bg-ink p-6 text-paper">
              <div className="flex flex-wrap items-center gap-3">
                <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.35em] text-paper/60">
                  Active Decision
                </p>
                {activeDecision ? (
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${statusClasses(
                      activeDecision.status,
                    )}`}
                  >
                    {activeDecision.status.replace("_", " ")}
                  </span>
                ) : null}
              </div>

              <h2 className="mt-3 max-w-3xl font-[family-name:var(--font-heading)] text-3xl font-semibold leading-tight md:text-4xl">
                {activeDecision?.decision_brief ??
                  "Create or seed a decision to start the workspace."}
              </h2>

              <p className="mt-4 max-w-2xl text-sm text-paper/75">
                {activeDecision?.question ??
                  "The frontend is now tied to persisted records in Postgres through the API. Seed the ERP example or create a fresh decision frame from structured fields."}
              </p>

              {activeDecision ? (
                <div className="mt-5 flex flex-wrap gap-2 text-xs text-paper/70">
                  <span className="rounded-full border border-paper/15 px-3 py-1">
                    {typeLabel(activeDecision.type)}
                  </span>
                  <span className="rounded-full border border-paper/15 px-3 py-1">
                    {activeDecision.id}
                  </span>
                  <span className="rounded-full border border-paper/15 px-3 py-1">
                    {formatTimestamp(activeDecision.created_at)}
                  </span>
                  <span className="rounded-full border border-paper/15 px-3 py-1">
                    Updated {formatTimestamp(activeDecision.updated_at)}
                  </span>
                </div>
              ) : null}
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[24px] border border-black/10 bg-paper p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Persistence
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  Postgres
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  Decisions are now stored through the API, not embedded in the
                  UI shell.
                </p>
              </div>
              <div className="rounded-[24px] border border-black/10 bg-paper p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Workspace Count
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  {isLoading ? "..." : decisions.length}
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  Persisted decision records currently available to the lab.
                </p>
              </div>
              <div className="rounded-[24px] border border-black/10 bg-paper p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Output Mode
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  Structured
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  Stored records today, schema-validated generation next.
                </p>
              </div>
            </div>

            <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
              <div className="rounded-[28px] border border-black/10 bg-white/65 p-6">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Create Decision
                    </p>
                    <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                      Persist a new workspace entry
                    </h3>
                  </div>
                  <button
                    type="button"
                    onClick={handleSeedBootstrap}
                    disabled={isSeeding}
                    className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSeeding ? "Seeding..." : "Seed ERP Example"}
                  </button>
                </div>

                <form onSubmit={handleCreateDecision} className="mt-6 space-y-4">
                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Title
                    </span>
                    <input
                      value={draft.title}
                      onChange={(event) =>
                        setDraft((current) => ({
                          ...current,
                          title: event.target.value,
                        }))
                      }
                      required
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                      placeholder="ERPNext vs Tango vs Bejerman"
                    />
                  </label>

                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Decision Brief
                    </span>
                    <textarea
                      value={draft.decision_brief}
                      onChange={(event) =>
                        setDraft((current) => ({
                          ...current,
                          decision_brief: event.target.value,
                        }))
                      }
                      required
                      rows={2}
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                      placeholder="Short summary of the decision and what is being evaluated."
                    />
                  </label>

                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Question
                    </span>
                    <textarea
                      value={draft.question}
                      onChange={(event) =>
                        setDraft((current) => ({
                          ...current,
                          question: event.target.value,
                        }))
                      }
                      required
                      rows={3}
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                      placeholder="Should we adopt ERPNext instead of Tango or Bejerman?"
                    />
                  </label>

                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Context
                    </span>
                    <textarea
                      value={draft.context}
                      onChange={(event) =>
                        setDraft((current) => ({
                          ...current,
                          context: event.target.value,
                        }))
                      }
                      required
                      rows={4}
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                      placeholder="Describe the decision environment, constraints, and success criteria."
                    />
                  </label>

                  <div className="grid gap-4 md:grid-cols-2">
                    <label className="block">
                      <span className="text-xs uppercase tracking-[0.3em] text-steel">
                        Type
                      </span>
                      <select
                        value={draft.type}
                        onChange={(event) =>
                          setDraft((current) => ({
                            ...current,
                            type: event.target.value as DecisionType,
                          }))
                        }
                        className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                      >
                        {decisionTypes.map((type) => (
                          <option key={type.value} value={type.value}>
                            {type.label}
                          </option>
                        ))}
                      </select>
                    </label>

                    <label className="block">
                      <span className="text-xs uppercase tracking-[0.3em] text-steel">
                        Status
                      </span>
                      <select
                        value={draft.status}
                        onChange={(event) =>
                          setDraft((current) => ({
                            ...current,
                            status: event.target.value as DecisionStatus,
                          }))
                        }
                        className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink"
                      >
                        <option value="draft">Draft</option>
                        <option value="in_review">In Review</option>
                        <option value="recommended">Recommended</option>
                        <option value="archived">Archived</option>
                      </select>
                    </label>
                  </div>

                  {errorMessage ? (
                    <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                      {errorMessage}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="rounded-full bg-ember px-5 py-3 text-sm font-semibold text-paper transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSubmitting ? "Saving..." : "Create Decision"}
                  </button>
                </form>
              </div>

              <div className="rounded-[28px] border border-dashed border-black/15 bg-white/65 p-6">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Active Record
                </p>

                {activeDecision ? (
                  <div className="mt-4 space-y-4 text-sm text-ink/80">
                    <div>
                      <p className="font-[family-name:var(--font-heading)] text-xl font-semibold text-ink">
                        {activeDecision.title}
                      </p>
                      <p className="mt-2 leading-6">{activeDecision.decision_brief}</p>
                      <p className="mt-3 leading-6 text-ink/70">
                        {activeDecision.question}
                      </p>
                    </div>

                    <div className="rounded-2xl bg-black/[0.03] p-4">
                      <p className="text-xs uppercase tracking-[0.3em] text-steel">
                        Context
                      </p>
                      <p className="mt-3 leading-6">{activeDecision.context}</p>
                    </div>
                  </div>
                ) : (
                  <p className="mt-4 text-sm text-ink/65">
                    Nothing selected yet. Seed the ERP example or create a new
                    decision record from the form.
                  </p>
                )}
              </div>
            </div>
          </div>
        </section>

        <aside className="rounded-[28px] border border-black/10 bg-white/70 p-5 shadow-panel backdrop-blur">
          <div className="rounded-[24px] bg-ember px-4 py-5 text-paper">
            <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.3em] text-paper/75">
              Decision Trace
            </p>
            <p className="mt-3 text-sm leading-6">
              The UI is now grounded in persisted records. The next layer is not
              more chat, it is traceable generation over stored decision state.
            </p>
          </div>

          <div className="mt-5 space-y-3">
            {traceNotes.map((note) => (
              <div
                key={note}
                className="rounded-2xl border border-black/10 bg-black/[0.03] p-4 text-sm text-ink/80"
              >
                {note}
              </div>
            ))}
          </div>
        </aside>
      </div>
    </main>
  );
}
