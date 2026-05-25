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

const traceNotes = [
  "Decision frame must be editable after generation.",
  "Assumptions require confidence and validation method.",
  "Tradeoff analysis should remain schema-driven and reproducible.",
];

export function DecisionShell() {
  return (
    <main className="min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[240px_minmax(0,1fr)_320px]">
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
        </aside>

        <section className="rounded-[32px] border border-black/10 bg-white/75 p-6 shadow-panel backdrop-blur">
          <div className="flex flex-col gap-6">
            <div className="rounded-[28px] bg-ink p-6 text-paper">
              <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.35em] text-paper/60">
                Active Decision
              </p>
              <h2 className="mt-3 max-w-3xl font-[family-name:var(--font-heading)] text-3xl font-semibold leading-tight md:text-4xl">
                Should we adopt ERPNext instead of Tango or Bejerman?
              </h2>
              <p className="mt-4 max-w-2xl text-sm text-paper/75">
                TradeOffLab structures the question, exposes assumptions,
                compares options, and produces a traceable recommendation memo
                instead of a chat transcript.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-[24px] border border-black/10 bg-paper p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Options
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  3
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  ERPNext, Tango, Bejerman
                </p>
              </div>
              <div className="rounded-[24px] border border-black/10 bg-paper p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Criteria
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  Weighted
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  Cost, fit, implementation risk, local support
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
                  Schema-validated JSON and exportable markdown
                </p>
              </div>
            </div>

            <div className="rounded-[28px] border border-dashed border-black/15 bg-white/65 p-6">
              <p className="text-xs uppercase tracking-[0.3em] text-steel">
                Workspace Intent
              </p>
              <div className="mt-4 grid gap-3 text-sm text-ink/80 md:grid-cols-2">
                <p>
                  Structured editing replaces free-form prompting as the primary
                  interaction model.
                </p>
                <p>
                  Each generation step should be reproducible, independently
                  rerunnable, and attributable to a specific schema and model.
                </p>
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
              A recommendation is only useful if its reasoning can be inspected,
              challenged, and exported.
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

