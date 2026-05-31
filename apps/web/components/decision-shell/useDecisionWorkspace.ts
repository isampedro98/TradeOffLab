"use client";

import { startTransition, useEffect, useState } from "react";

import {
  apiUrl,
  initialCriterionDraft,
  initialDecisionDraft,
  initialOptionDraft,
  normalizeText,
  type Assumption,
  type CreateCriterionPayload,
  type CreateDecisionPayload,
  type CreateOptionPayload,
  type CriterionRecord,
  type Decision,
  type DecisionWorkspaceController,
  type OptionRecord,
  type TradeoffMatrix,
} from "./model";

export function useDecisionWorkspace(): DecisionWorkspaceController {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [options, setOptions] = useState<OptionRecord[]>([]);
  const [criteria, setCriteria] = useState<CriterionRecord[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [selectedAssumptionIds, setSelectedAssumptionIds] = useState<string[]>(
    [],
  );
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
  const [isCreateDecisionOpen, setIsCreateDecisionOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [isLoadingCriteria, setIsLoadingCriteria] = useState(false);
  const [isLoadingAssumptions, setIsLoadingAssumptions] = useState(false);
  const [isLoadingTradeoffMatrix, setIsLoadingTradeoffMatrix] = useState(false);
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [isSubmittingOption, setIsSubmittingOption] = useState(false);
  const [isSubmittingCriterion, setIsSubmittingCriterion] = useState(false);
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
  const canRegenerateSelectedAssumptions =
    canGenerateAssumptions &&
    (assumptions.length === 0 || selectedAssumptionIds.length > 0);
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
      setSelectedAssumptionIds([]);
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
      const response = await fetch(apiUrl(`/api/v1/decisions/${decisionId}/criteria`), {
        cache: "no-store",
      });

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
      setSelectedAssumptionIds((current) =>
        current.filter((assumptionId) =>
          payload.some((assumption) => assumption.id === assumptionId),
        ),
      );
    } catch (error) {
      setAssumptions([]);
      setSelectedAssumptionIds([]);
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

  function openCreateDecisionModal() {
    setDecisionErrorMessage(null);
    setDecisionDraft(initialDecisionDraft);
    setIsCreateDecisionOpen(true);
  }

  function closeCreateDecisionModal() {
    setDecisionErrorMessage(null);
    setDecisionDraft(initialDecisionDraft);
    setIsCreateDecisionOpen(false);
  }

  async function createDecision() {
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
      setIsCreateDecisionOpen(false);
    } catch (error) {
      setIsSubmittingDecision(false);
      setDecisionErrorMessage(
        error instanceof Error ? error.message : "Failed to create decision.",
      );
    }
  }

  async function deleteDecision() {
    if (!activeDecisionId || !activeDecision) {
      return;
    }

    const confirmed = window.confirm(
      `Delete decision "${activeDecision.title}"? This removes its options, criteria, assumptions, and tradeoff matrix.`,
    );
    if (!confirmed) {
      return;
    }

    setDecisionErrorMessage(null);

    try {
      const response = await fetch(apiUrl(`/api/v1/decisions/${activeDecisionId}`), {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Failed to delete decision (${response.status})`);
      }

      await loadDecisions();
    } catch (error) {
      setDecisionErrorMessage(
        error instanceof Error ? error.message : "Failed to delete decision.",
      );
    }
  }

  async function createOption() {
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

  async function deleteOption(optionId: string) {
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

  async function createCriterion() {
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

  async function deleteCriterion(criterionId: string) {
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

  async function generateAssumptions() {
    if (!activeDecisionId || !canRegenerateSelectedAssumptions) {
      return;
    }

    setIsGeneratingAssumptions(true);
    setAssumptionErrorMessage(null);
    setAssumptionSuccessMessage(null);

    try {
      const selectedCount = selectedAssumptionIds.length;
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/assumptions/generate`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            count: assumptions.length === 0 ? 4 : selectedCount,
            replace_existing: assumptions.length === 0,
            assumption_ids: selectedAssumptionIds,
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
        assumptions: Assumption[];
      };
      setAssumptions(payload.assumptions);
      setSelectedAssumptionIds([]);
      setAssumptionSuccessMessage(
        assumptions.length === 0
          ? `Generated ${payload.assumptions.length} assumptions.`
          : `Regenerated ${selectedCount} selected assumptions.`,
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

  function toggleAssumptionSelection(assumptionId: string) {
    setSelectedAssumptionIds((current) =>
      current.includes(assumptionId)
        ? current.filter((id) => id !== assumptionId)
        : [...current, assumptionId],
    );
  }

  function selectAllAssumptions() {
    setSelectedAssumptionIds(assumptions.map((assumption) => assumption.id));
  }

  function clearAssumptionSelection() {
    setSelectedAssumptionIds([]);
  }

  async function generateTradeoffMatrix() {
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

  return {
    decisions,
    options,
    criteria,
    assumptions,
    selectedAssumptionIds,
    tradeoffMatrix,
    activeDecisionId,
    activeDecision,
    optionMap,
    decisionDraft,
    optionDraft,
    criterionDraft,
    isCreateDecisionOpen,
    isLoading,
    isLoadingOptions,
    isLoadingCriteria,
    isLoadingAssumptions,
    isLoadingTradeoffMatrix,
    isSubmittingDecision,
    isSubmittingOption,
    isSubmittingCriterion,
    isGeneratingAssumptions,
    isGeneratingTradeoffMatrix,
    decisionErrorMessage,
    optionErrorMessage,
    criterionErrorMessage,
    assumptionErrorMessage,
    tradeoffMatrixErrorMessage,
    assumptionSuccessMessage,
    tradeoffMatrixSuccessMessage,
    canGenerateAssumptions,
    canRegenerateSelectedAssumptions,
    canGenerateTradeoffMatrix,
    showDecisionBrief,
    showDecisionQuestion,
    setActiveDecisionId,
    setDecisionDraft,
    setOptionDraft,
    setCriterionDraft,
    openCreateDecisionModal,
    closeCreateDecisionModal,
    createDecision,
    deleteDecision,
    createOption,
    deleteOption,
    createCriterion,
    deleteCriterion,
    generateAssumptions,
    toggleAssumptionSelection,
    selectAllAssumptions,
    clearAssumptionSelection,
    generateTradeoffMatrix,
  };
}
