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

const criterionMeasurementTypes = [
  { value: "qualitative", label: "Qualitative" },
  { value: "numeric", label: "Numeric" },
  { value: "boolean", label: "Boolean" },
  { value: "ordinal", label: "Ordinal" },
] as const;

type DecisionType = (typeof decisionTypes)[number]["value"];
type DecisionStatus = "draft" | "in_review" | "recommended" | "archived";
type CriterionMeasurementType =
  (typeof criterionMeasurementTypes)[number]["value"];

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

type OptionRecord = {
  id: string;
  decision_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
};

type CriterionRecord = {
  id: string;
  decision_id: string;
  name: string;
  description: string;
  weight: number;
  measurement_type: CriterionMeasurementType;
  created_at: string;
  updated_at: string;
};

type Assumption = {
  id: string;
  decision_id: string;
  statement: string;
  confidence: "low" | "medium" | "high";
  impact_if_false: string;
  validation_method: string;
  created_at: string;
  updated_at: string;
};

type TradeoffAssessment = {
  id: string;
  matrix_id: string;
  criterion_id: string;
  option_id: string;
  score: number;
  rationale: string;
  created_at: string;
  updated_at: string;
};

type TradeoffMatrix = {
  id: string;
  decision_id: string;
  summary: string;
  scoring_scale_label: string;
  provider: string;
  model: string;
  created_at: string;
  updated_at: string;
  assessments: TradeoffAssessment[];
};

type CreateDecisionPayload = {
  title: string;
  decision_brief: string;
  question: string;
  context: string;
  type: DecisionType;
  status: DecisionStatus;
};

type CreateOptionPayload = {
  name: string;
  description: string;
};

type CreateCriterionPayload = {
  name: string;
  description: string;
  weight: string;
  measurement_type: CriterionMeasurementType;
};

const traceNotes = [
  "Persisted decisions now come from the FastAPI API backed by Postgres.",
  "The ERP bootstrap example can be seeded once and then reused across runs.",
  "This workspace remains structured-first: stored records, explicit fields, no chat transcript.",
];

const initialDecisionDraft: CreateDecisionPayload = {
  title: "",
  decision_brief: "",
  question: "",
  context: "",
  type: "erp_adoption",
  status: "draft",
};

const initialOptionDraft: CreateOptionPayload = {
  name: "",
  description: "",
};

const initialCriterionDraft: CreateCriterionPayload = {
  name: "",
  description: "",
  weight: "0.20",
  measurement_type: "qualitative",
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

function measurementTypeLabel(type: CriterionMeasurementType): string {
  return (
    criterionMeasurementTypes.find((item) => item.value === type)?.label ?? type
  );
}

function confidenceLabel(confidence: Assumption["confidence"]): string {
  return confidence.charAt(0).toUpperCase() + confidence.slice(1);
}

function normalizeText(value: string): string {
  return value.trim().toLowerCase();
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
  const [options, setOptions] = useState<OptionRecord[]>([]);
  const [criteria, setCriteria] = useState<CriterionRecord[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [tradeoffMatrix, setTradeoffMatrix] = useState<TradeoffMatrix | null>(
    null,
  );
  const [activeDecisionId, setActiveDecisionId] = useState<string | null>(null);
  const [decisionDraft, setDecisionDraft] =
    useState<CreateDecisionPayload>(initialDecisionDraft);
  const [optionDraft, setOptionDraft] =
    useState<CreateOptionPayload>(initialOptionDraft);
  const [criterionDraft, setCriterionDraft] =
    useState<CreateCriterionPayload>(initialCriterionDraft);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [isLoadingCriteria, setIsLoadingCriteria] = useState(false);
  const [isLoadingAssumptions, setIsLoadingAssumptions] = useState(false);
  const [isLoadingTradeoffMatrix, setIsLoadingTradeoffMatrix] = useState(false);
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [isSubmittingOption, setIsSubmittingOption] = useState(false);
  const [isSubmittingCriterion, setIsSubmittingCriterion] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isGeneratingAssumptions, setIsGeneratingAssumptions] = useState(false);
  const [isGeneratingTradeoffMatrix, setIsGeneratingTradeoffMatrix] =
    useState(false);
  const [decisionErrorMessage, setDecisionErrorMessage] = useState<string | null>(
    null,
  );
  const [optionErrorMessage, setOptionErrorMessage] = useState<string | null>(
    null,
  );
  const [criterionErrorMessage, setCriterionErrorMessage] = useState<
    string | null
  >(null);
  const [assumptionErrorMessage, setAssumptionErrorMessage] = useState<
    string | null
  >(null);
  const [tradeoffMatrixErrorMessage, setTradeoffMatrixErrorMessage] = useState<
    string | null
  >(null);
  const [assumptionSuccessMessage, setAssumptionSuccessMessage] = useState<
    string | null
  >(null);
  const [tradeoffMatrixSuccessMessage, setTradeoffMatrixSuccessMessage] =
    useState<string | null>(null);

  const activeDecision =
    decisions.find((decision) => decision.id === activeDecisionId) ?? null;
  const canGenerateAssumptions =
    !!activeDecision && options.length > 0 && criteria.length > 0;
  const canGenerateTradeoffMatrix =
    !!activeDecision &&
    options.length > 0 &&
    criteria.length > 0 &&
    assumptions.length > 0;
  const optionMap = new Map(options.map((option) => [option.id, option]));
  const showDecisionBrief = activeDecision
    ? normalizeText(activeDecision.decision_brief) !==
      normalizeText(activeDecision.title)
    : false;
  const showDecisionQuestion = activeDecision
    ? ![
        normalizeText(activeDecision.title),
        normalizeText(activeDecision.decision_brief),
      ].includes(normalizeText(activeDecision.question))
    : false;

  async function loadDecisions(preferredDecisionId?: string) {
    setDecisionErrorMessage(null);

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
      setDecisionErrorMessage(
        error instanceof Error ? error.message : "Failed to load decisions.",
      );
    } finally {
      setIsLoading(false);
      setIsSubmittingDecision(false);
      setIsSeeding(false);
    }
  }

  useEffect(() => {
    void loadDecisions();
    // We only want the initial bootstrap fetch.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!activeDecisionId) {
      setOptions([]);
      setCriteria([]);
      setAssumptions([]);
      setTradeoffMatrix(null);
      setOptionErrorMessage(null);
      setCriterionErrorMessage(null);
      setAssumptionErrorMessage(null);
      setTradeoffMatrixErrorMessage(null);
      return;
    }

    void Promise.all([
      loadOptions(activeDecisionId),
      loadCriteria(activeDecisionId),
      loadAssumptions(activeDecisionId),
      loadTradeoffMatrix(activeDecisionId),
    ]);
  }, [activeDecisionId]);

  async function loadOptions(decisionId: string) {
    setIsLoadingOptions(true);
    setOptionErrorMessage(null);

    try {
      const response = await fetch(apiUrl(`/api/v1/decisions/${decisionId}/options`), {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Failed to load options (${response.status})`);
      }

      const payload = (await response.json()) as OptionRecord[];
      setOptions(payload);
    } catch (error) {
      setOptions([]);
      setOptionErrorMessage(
        error instanceof Error ? error.message : "Failed to load options.",
      );
    } finally {
      setIsLoadingOptions(false);
    }
  }

  async function loadCriteria(decisionId: string) {
    setIsLoadingCriteria(true);
    setCriterionErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${decisionId}/criteria`),
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to load criteria (${response.status})`);
      }

      const payload = (await response.json()) as CriterionRecord[];
      setCriteria(payload);
    } catch (error) {
      setCriteria([]);
      setCriterionErrorMessage(
        error instanceof Error ? error.message : "Failed to load criteria.",
      );
    } finally {
      setIsLoadingCriteria(false);
    }
  }

  async function loadAssumptions(decisionId: string) {
    setIsLoadingAssumptions(true);
    setAssumptionErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${decisionId}/assumptions`),
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to load assumptions (${response.status})`);
      }

      const payload = (await response.json()) as Assumption[];
      setAssumptions(payload);
    } catch (error) {
      setAssumptions([]);
      setAssumptionErrorMessage(
        error instanceof Error ? error.message : "Failed to load assumptions.",
      );
    } finally {
      setIsLoadingAssumptions(false);
    }
  }

  async function loadTradeoffMatrix(decisionId: string) {
    setIsLoadingTradeoffMatrix(true);
    setTradeoffMatrixErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${decisionId}/tradeoff-matrix`),
        {
          cache: "no-store",
        },
      );

      if (response.status === 404) {
        setTradeoffMatrix(null);
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to load tradeoff matrix (${response.status})`);
      }

      const payload = (await response.json()) as TradeoffMatrix;
      setTradeoffMatrix(payload);
    } catch (error) {
      setTradeoffMatrix(null);
      setTradeoffMatrixErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to load tradeoff matrix.",
      );
    } finally {
      setIsLoadingTradeoffMatrix(false);
    }
  }

  async function handleCreateDecision(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmittingDecision(true);
    setDecisionErrorMessage(null);

    try {
      const response = await fetch(apiUrl("/api/v1/decisions"), {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(decisionDraft),
      });

      if (!response.ok) {
        throw new Error(`Failed to create decision (${response.status})`);
      }

      const created = (await response.json()) as Decision;
      setDecisionDraft(initialDecisionDraft);
      await loadDecisions(created.id);
    } catch (error) {
      setIsSubmittingDecision(false);
      setDecisionErrorMessage(
        error instanceof Error ? error.message : "Failed to create decision.",
      );
    }
  }

  async function handleSeedBootstrap() {
    setIsSeeding(true);
    setDecisionErrorMessage(null);

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
      setDecisionErrorMessage(
        error instanceof Error ? error.message : "Failed to seed decision.",
      );
    }
  }

  async function handleCreateOption(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDecisionId) {
      return;
    }

    setIsSubmittingOption(true);
    setOptionErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/options`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(optionDraft),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to create option (${response.status})`);
      }

      setOptionDraft(initialOptionDraft);
      await loadOptions(activeDecisionId);
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setIsSubmittingOption(false);
      setOptionErrorMessage(
        error instanceof Error ? error.message : "Failed to create option.",
      );
    } finally {
      setIsSubmittingOption(false);
    }
  }

  async function handleDeleteOption(optionId: string) {
    if (!activeDecisionId) {
      return;
    }

    setOptionErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/options/${optionId}`),
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to delete option (${response.status})`);
      }

      await loadOptions(activeDecisionId);
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setOptionErrorMessage(
        error instanceof Error ? error.message : "Failed to delete option.",
      );
    }
  }

  async function handleCreateCriterion(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!activeDecisionId) {
      return;
    }

    setIsSubmittingCriterion(true);
    setCriterionErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/criteria`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: criterionDraft.name,
            description: criterionDraft.description,
            weight: Number(criterionDraft.weight),
            measurement_type: criterionDraft.measurement_type,
          }),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to create criterion (${response.status})`);
      }

      setCriterionDraft(initialCriterionDraft);
      await loadCriteria(activeDecisionId);
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setIsSubmittingCriterion(false);
      setCriterionErrorMessage(
        error instanceof Error ? error.message : "Failed to create criterion.",
      );
    } finally {
      setIsSubmittingCriterion(false);
    }
  }

  async function handleDeleteCriterion(criterionId: string) {
    if (!activeDecisionId) {
      return;
    }

    setCriterionErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/criteria/${criterionId}`),
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to delete criterion (${response.status})`);
      }

      await loadCriteria(activeDecisionId);
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setCriterionErrorMessage(
        error instanceof Error ? error.message : "Failed to delete criterion.",
      );
    }
  }

  async function handleGenerateAssumptions() {
    if (!activeDecisionId || !canGenerateAssumptions) {
      return;
    }

    setIsGeneratingAssumptions(true);
    setAssumptionErrorMessage(null);
    setAssumptionSuccessMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/assumptions/generate`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            count: 4,
            replace_existing: true,
          }),
        },
      );

      if (!response.ok) {
        let detail = `Failed to generate assumptions (${response.status})`;

        try {
          const payload = (await response.json()) as { detail?: string };
          if (payload.detail) {
            detail = payload.detail;
          }
        } catch {
          // Fall back to the generic HTTP status error above.
        }

        throw new Error(detail);
      }

      const payload = (await response.json()) as {
        replaced_existing: boolean;
        assumptions: Assumption[];
      };
      setAssumptions(payload.assumptions);
      setAssumptionSuccessMessage(
        payload.replaced_existing
          ? `Generated ${payload.assumptions.length} assumptions and replaced the previous set.`
          : `Generated ${payload.assumptions.length} assumptions.`,
      );
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setAssumptionErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to generate assumptions.",
      );
    } finally {
      setIsGeneratingAssumptions(false);
    }
  }

  async function handleGenerateTradeoffMatrix() {
    if (!activeDecisionId || !canGenerateTradeoffMatrix) {
      return;
    }

    setIsGeneratingTradeoffMatrix(true);
    setTradeoffMatrixErrorMessage(null);
    setTradeoffMatrixSuccessMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/tradeoff-matrix/generate`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            replace_existing: true,
          }),
        },
      );

      if (!response.ok) {
        let detail = `Failed to generate tradeoff matrix (${response.status})`;

        try {
          const payload = (await response.json()) as { detail?: string };
          if (payload.detail) {
            detail = payload.detail;
          }
        } catch {
          // Fall back to the generic HTTP status error above.
        }

        throw new Error(detail);
      }

      const payload = (await response.json()) as {
        replaced_existing: boolean;
        matrix: TradeoffMatrix;
      };
      setTradeoffMatrix(payload.matrix);
      setTradeoffMatrixSuccessMessage(
        payload.replaced_existing
          ? "Generated tradeoff matrix and replaced the previous version."
          : "Generated tradeoff matrix.",
      );
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setTradeoffMatrixErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to generate tradeoff matrix.",
      );
    } finally {
      setIsGeneratingTradeoffMatrix(false);
    }
  }

  return (
    <main className="min-h-screen px-4 py-6 md:px-8">
      <div className="mx-auto grid max-w-[1500px] gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
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
                {activeDecision?.title ??
                  "Create or seed a decision to start the workspace."}
              </h2>

              <p className="mt-4 max-w-2xl text-sm text-paper/75">
                {activeDecision?.decision_brief ??
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
                  Option Count
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  {activeDecision ? options.length : "..."}
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  Candidate options available for the current decision.
                </p>
              </div>
              <div className="rounded-[24px] border border-black/10 bg-paper p-5">
                <p className="text-xs uppercase tracking-[0.3em] text-steel">
                  Criteria Count
                </p>
                <p className="mt-3 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                  {activeDecision ? criteria.length : "..."}
                </p>
                <p className="mt-2 text-sm text-ink/70">
                  Structured evaluation criteria loaded for this decision.
                </p>
              </div>
            </div>

            <section className="rounded-[28px] border border-dashed border-black/15 bg-white/65 p-6">
              <p className="text-xs uppercase tracking-[0.3em] text-steel">
                Active Record
              </p>

              {activeDecision ? (
                <div className="mt-4 space-y-5 text-sm text-ink/80">
                  <div>
                    <p className="font-[family-name:var(--font-heading)] text-3xl font-semibold text-ink">
                      {activeDecision.title}
                    </p>
                    {showDecisionBrief ? (
                      <p className="mt-3 max-w-3xl text-lg leading-8 text-ink/80">
                        {activeDecision.decision_brief}
                      </p>
                    ) : null}
                    {showDecisionQuestion ? (
                      <p className="mt-3 max-w-3xl leading-7 text-ink/70">
                        {activeDecision.question}
                      </p>
                    ) : null}
                  </div>

                  <div className="flex flex-wrap gap-2 text-xs text-ink/65">
                    <span className="rounded-full border border-black/10 px-3 py-1">
                      {typeLabel(activeDecision.type)}
                    </span>
                    <span className="rounded-full border border-black/10 px-3 py-1">
                      {activeDecision.status.replace("_", " ")}
                    </span>
                    <span className="rounded-full border border-black/10 px-3 py-1">
                      Updated {formatTimestamp(activeDecision.updated_at)}
                    </span>
                  </div>

                  <div className="rounded-2xl bg-black/[0.03] p-5">
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Context
                    </p>
                    <p className="mt-3 max-w-4xl leading-7">
                      {activeDecision.context}
                    </p>
                  </div>
                </div>
              ) : (
                <p className="mt-4 text-sm text-ink/65">
                  Nothing selected yet. Seed the ERP example or create a new
                  decision record from the form below.
                </p>
              )}
            </section>

            <div className="grid gap-4 xl:grid-cols-2">
              <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Options
                    </p>
                    <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                      Candidate options
                    </h3>
                  </div>
                  <span className="rounded-full bg-black/[0.04] px-3 py-1 text-xs text-ink/70">
                    {options.length}
                  </span>
                </div>

                <div className="mt-5 space-y-3">
                  {isLoadingOptions ? (
                    <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
                      Loading options...
                    </div>
                  ) : options.length > 0 ? (
                    options.map((option) => (
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
                            onClick={() => handleDeleteOption(option.id)}
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

                <form onSubmit={handleCreateOption} className="mt-5 space-y-4">
                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Option Name
                    </span>
                    <input
                      value={optionDraft.name}
                      onChange={(event) =>
                        setOptionDraft((current) => ({
                          ...current,
                          name: event.target.value,
                        }))
                      }
                      required
                      disabled={!activeDecision}
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
                      placeholder="ERPNext"
                    />
                  </label>

                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Description
                    </span>
                    <textarea
                      value={optionDraft.description}
                      onChange={(event) =>
                        setOptionDraft((current) => ({
                          ...current,
                          description: event.target.value,
                        }))
                      }
                      required
                      disabled={!activeDecision}
                      rows={3}
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
                      placeholder="Summarize why this option belongs in the decision set."
                    />
                  </label>

                  {optionErrorMessage ? (
                    <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                      {optionErrorMessage}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={!activeDecision || isSubmittingOption}
                    className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSubmittingOption ? "Saving..." : "Add Option"}
                  </button>
                </form>
              </section>

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
                    {criteria.length}
                  </span>
                </div>

                <div className="mt-5 space-y-3">
                  {isLoadingCriteria ? (
                    <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
                      Loading criteria...
                    </div>
                  ) : criteria.length > 0 ? (
                    criteria.map((criterion) => (
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
                            onClick={() => handleDeleteCriterion(criterion.id)}
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

                <form onSubmit={handleCreateCriterion} className="mt-5 space-y-4">
                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Criterion Name
                    </span>
                    <input
                      value={criterionDraft.name}
                      onChange={(event) =>
                        setCriterionDraft((current) => ({
                          ...current,
                          name: event.target.value,
                        }))
                      }
                      required
                      disabled={!activeDecision}
                      className="mt-2 w-full rounded-2xl border border-black/10 bg-paper px-4 py-3 text-sm outline-none transition focus:border-ink disabled:opacity-60"
                      placeholder="Implementation Risk"
                    />
                  </label>

                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Description
                    </span>
                    <textarea
                      value={criterionDraft.description}
                      onChange={(event) =>
                        setCriterionDraft((current) => ({
                          ...current,
                          description: event.target.value,
                        }))
                      }
                      required
                      disabled={!activeDecision}
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
                        value={criterionDraft.weight}
                        onChange={(event) =>
                          setCriterionDraft((current) => ({
                            ...current,
                            weight: event.target.value,
                          }))
                        }
                        required
                        disabled={!activeDecision}
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
                        value={criterionDraft.measurement_type}
                        onChange={(event) =>
                          setCriterionDraft((current) => ({
                            ...current,
                            measurement_type:
                              event.target.value as CriterionMeasurementType,
                          }))
                        }
                        disabled={!activeDecision}
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

                  {criterionErrorMessage ? (
                    <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                      {criterionErrorMessage}
                    </div>
                  ) : null}

                  <button
                    type="submit"
                    disabled={!activeDecision || isSubmittingCriterion}
                    className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isSubmittingCriterion ? "Saving..." : "Add Criterion"}
                  </button>
                </form>
              </section>
            </div>

            <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
              <div className="grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
                <div className="rounded-[24px] bg-ember px-5 py-6 text-paper">
                  <p className="font-[family-name:var(--font-heading)] text-xs uppercase tracking-[0.3em] text-paper/75">
                    Decision Trace
                  </p>
                  <p className="mt-4 max-w-2xl text-lg leading-8">
                    The UI is now grounded in persisted records. The next layer
                    is not more chat, it is traceable generation over stored
                    decision state.
                  </p>
                </div>

                <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-1 2xl:grid-cols-3">
                  {traceNotes.map((note) => (
                    <div
                      key={note}
                      className="rounded-2xl border border-black/10 bg-black/[0.03] p-4 text-sm leading-6 text-ink/80"
                    >
                      {note}
                    </div>
                  ))}
                </div>
              </div>
            </section>

            <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Assumptions
                  </p>
                  <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    Structured assumption register
                  </h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
                    Persisted assumptions tied to the active decision. Generation
                    runs against the stored decision, options, and criteria.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleGenerateAssumptions}
                  disabled={!canGenerateAssumptions || isGeneratingAssumptions}
                  className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isGeneratingAssumptions
                    ? "Generating..."
                    : "Generate Assumptions"}
                </button>
              </div>

              <p className="mt-3 text-sm text-ink/65">
                Generate Assumptions replaces the current assumption set for this
                decision.
              </p>

              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Options
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    {options.length}
                  </p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Criteria
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    {criteria.length}
                  </p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Prerequisites
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                    {canGenerateAssumptions ? "Ready" : "Incomplete"}
                  </p>
                </div>
              </div>

              {activeDecision && !canGenerateAssumptions ? (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  Assumption generation requires at least one option and one
                  criterion. This decision currently has {options.length} options
                  and {criteria.length} criteria.
                </div>
              ) : null}

              {assumptionErrorMessage ? (
                <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  {assumptionErrorMessage}
                </div>
              ) : null}

              {assumptionSuccessMessage ? (
                <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                  {assumptionSuccessMessage}
                </div>
              ) : null}

              <div className="mt-6 grid gap-4 xl:grid-cols-2">
                {isLoadingAssumptions ? (
                  <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
                    Loading assumptions...
                  </div>
                ) : assumptions.length > 0 ? (
                  assumptions.map((assumption) => (
                    <article
                      key={assumption.id}
                      className="rounded-[24px] border border-black/10 bg-paper p-5"
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                          {confidenceLabel(assumption.confidence)} confidence
                        </span>
                        <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                          Updated {formatTimestamp(assumption.updated_at)}
                        </span>
                      </div>

                      <p className="mt-4 font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                        {assumption.statement}
                      </p>

                      <div className="mt-4 space-y-4 text-sm leading-6 text-ink/75">
                        <div>
                          <p className="text-xs uppercase tracking-[0.3em] text-steel">
                            Impact If False
                          </p>
                          <p className="mt-2">{assumption.impact_if_false}</p>
                        </div>

                        <div>
                          <p className="text-xs uppercase tracking-[0.3em] text-steel">
                            Validation Method
                          </p>
                          <p className="mt-2">{assumption.validation_method}</p>
                        </div>
                      </div>
                    </article>
                  ))
                ) : (
                  <div className="rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
                    No assumptions yet. Generate a set from the persisted decision
                    frame once options and criteria are ready.
                  </div>
                )}
              </div>
            </section>

            <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
              <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Tradeoffs
                  </p>
                  <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    Structured tradeoff matrix
                  </h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
                    Generate criterion-by-option assessments from the stored
                    decision frame, assumptions, and weighted criteria.
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleGenerateTradeoffMatrix}
                  disabled={!canGenerateTradeoffMatrix || isGeneratingTradeoffMatrix}
                  className="rounded-full border border-ink px-4 py-2 text-sm font-medium text-ink transition hover:bg-ink hover:text-paper disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isGeneratingTradeoffMatrix
                    ? "Generating..."
                    : "Generate Tradeoff Matrix"}
                </button>
              </div>

              <p className="mt-3 text-sm text-ink/65">
                Generate Tradeoff Matrix replaces the current matrix for this
                decision.
              </p>

              <div className="mt-4 grid gap-3 md:grid-cols-4">
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Options
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    {options.length}
                  </p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Criteria
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    {criteria.length}
                  </p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Assumptions
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold text-ink">
                    {assumptions.length}
                  </p>
                </div>
                <div className="rounded-2xl border border-black/10 bg-paper px-4 py-4 text-sm text-ink/75">
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    Prerequisites
                  </p>
                  <p className="mt-2 font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                    {canGenerateTradeoffMatrix ? "Ready" : "Incomplete"}
                  </p>
                </div>
              </div>

              {activeDecision && !canGenerateTradeoffMatrix ? (
                <div className="mt-4 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
                  Tradeoff matrix generation requires at least one option, one
                  criterion, and one assumption.
                </div>
              ) : null}

              {tradeoffMatrixErrorMessage ? (
                <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                  {tradeoffMatrixErrorMessage}
                </div>
              ) : null}

              {tradeoffMatrixSuccessMessage ? (
                <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-900">
                  {tradeoffMatrixSuccessMessage}
                </div>
              ) : null}

              {isLoadingTradeoffMatrix ? (
                <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
                  Loading tradeoff matrix...
                </div>
              ) : tradeoffMatrix ? (
                <div className="mt-6 space-y-5">
                  <div className="rounded-2xl border border-black/10 bg-paper p-5">
                    <p className="text-xs uppercase tracking-[0.3em] text-steel">
                      Matrix Summary
                    </p>
                    <p className="mt-3 text-sm leading-7 text-ink/80">
                      {tradeoffMatrix.summary}
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2 text-xs text-ink/65">
                      <span className="rounded-full bg-black/[0.05] px-3 py-1">
                        {tradeoffMatrix.scoring_scale_label}
                      </span>
                      <span className="rounded-full bg-black/[0.05] px-3 py-1">
                        Model {tradeoffMatrix.model}
                      </span>
                      <span className="rounded-full bg-black/[0.05] px-3 py-1">
                        Updated {formatTimestamp(tradeoffMatrix.updated_at)}
                      </span>
                    </div>
                  </div>

                  <div className="space-y-4">
                    {criteria.map((criterion) => {
                      const criterionAssessments = tradeoffMatrix.assessments.filter(
                        (assessment) => assessment.criterion_id === criterion.id,
                      );
                      if (criterionAssessments.length === 0) {
                        return null;
                      }

                      return (
                        <section
                          key={criterion.id}
                          className="rounded-2xl border border-black/10 bg-paper p-5"
                        >
                          <div className="flex flex-wrap gap-2">
                            <p className="font-[family-name:var(--font-heading)] text-xl font-semibold text-ink">
                              {criterion.name}
                            </p>
                            <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                              Weight {criterion.weight}
                            </span>
                            <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                              {measurementTypeLabel(criterion.measurement_type)}
                            </span>
                          </div>
                          <p className="mt-2 text-sm leading-6 text-ink/70">
                            {criterion.description}
                          </p>

                          <div className="mt-5 grid gap-4 xl:grid-cols-2">
                            {criterionAssessments.map((assessment) => {
                              const option = optionMap.get(assessment.option_id);
                              return (
                                <article
                                  key={assessment.id}
                                  className="rounded-2xl border border-black/10 bg-white/70 p-4"
                                >
                                  <div className="flex flex-wrap items-center gap-2">
                                    <p className="font-[family-name:var(--font-heading)] text-lg font-semibold text-ink">
                                      {option?.name ?? assessment.option_id}
                                    </p>
                                    <span className="rounded-full bg-black/[0.05] px-3 py-1 text-xs text-ink/70">
                                      Score {assessment.score.toFixed(1)}
                                    </span>
                                  </div>
                                  <p className="mt-3 text-sm leading-6 text-ink/75">
                                    {assessment.rationale}
                                  </p>
                                </article>
                              );
                            })}
                          </div>
                        </section>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <div className="mt-6 rounded-2xl border border-dashed border-black/15 px-4 py-5 text-sm text-ink/65">
                  No tradeoff matrix yet. Generate one once the decision has
                  options, criteria, and assumptions.
                </div>
              )}
            </section>

            <section className="rounded-[28px] border border-black/10 bg-white/65 p-6">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-steel">
                    New Decision
                  </p>
                  <h3 className="mt-2 font-[family-name:var(--font-heading)] text-2xl font-semibold">
                    Add another workspace entry
                  </h3>
                  <p className="mt-2 max-w-2xl text-sm leading-6 text-ink/70">
                    Keep the active analysis separate from the intake flow. Seed
                    the ERP example or create a fresh decision record here.
                  </p>
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
                <div className="grid gap-4 xl:grid-cols-2">
                  <label className="block">
                    <span className="text-xs uppercase tracking-[0.3em] text-steel">
                      Title
                    </span>
                    <input
                      value={decisionDraft.title}
                      onChange={(event) =>
                        setDecisionDraft((current) => ({
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
                    <input
                      value={decisionDraft.decision_brief}
                      onChange={(event) =>
                        setDecisionDraft((current) => ({
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
                    value={decisionDraft.question}
                    onChange={(event) =>
                      setDecisionDraft((current) => ({
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
                    value={decisionDraft.context}
                    onChange={(event) =>
                      setDecisionDraft((current) => ({
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
                      value={decisionDraft.type}
                      onChange={(event) =>
                        setDecisionDraft((current) => ({
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
                      value={decisionDraft.status}
                      onChange={(event) =>
                        setDecisionDraft((current) => ({
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

                {decisionErrorMessage ? (
                  <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
                    {decisionErrorMessage}
                  </div>
                ) : null}

                <button
                  type="submit"
                  disabled={isSubmittingDecision}
                  className="rounded-full bg-ember px-5 py-3 text-sm font-semibold text-paper transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isSubmittingDecision ? "Saving..." : "Create Decision"}
                </button>
              </form>
            </section>
          </div>
        </section>
      </div>
    </main>
  );
}
