"use client";

import { startTransition, useEffect, useState } from "react";

import {
  apiUrl,
  initialCriterionDraft,
  initialDecisionDraft,
  initialEvidenceDraft,
  initialOptionDraft,
  normalizeText,
  type Assumption,
  type AdversarialReview,
  type CreateCriterionPayload,
  type CreateDecisionPayload,
  type CreateEvidencePayload,
  type CreateOptionPayload,
  type CriterionRecord,
  type Decision,
  type DecisionWorkspaceController,
  type EvidenceRecord,
  type OptionRecord,
  type RecommendationMemo,
  type TradeoffMatrix,
  type WorkspaceSection,
} from "./model";

export function useDecisionWorkspace(): DecisionWorkspaceController {
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [options, setOptions] = useState<OptionRecord[]>([]);
  const [criteria, setCriteria] = useState<CriterionRecord[]>([]);
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [evidence, setEvidence] = useState<EvidenceRecord[]>([]);
  const [selectedAssumptionIds, setSelectedAssumptionIds] = useState<string[]>(
    [],
  );
  const [tradeoffMatrix, setTradeoffMatrix] = useState<TradeoffMatrix | null>(
    null,
  );
  const [adversarialReview, setAdversarialReview] =
    useState<AdversarialReview | null>(null);
  const [recommendationMemo, setRecommendationMemo] =
    useState<RecommendationMemo | null>(null);
  const [activeSection, setActiveSection] =
    useState<WorkspaceSection>("Overview");
  const [activeDecisionId, setActiveDecisionId] = useState<string | null>(null);
  const [decisionDraft, setDecisionDraft] =
    useState<CreateDecisionPayload>(initialDecisionDraft);
  const [optionDraft, setOptionDraft] =
    useState<CreateOptionPayload>(initialOptionDraft);
  const [criterionDraft, setCriterionDraft] =
    useState<CreateCriterionPayload>(initialCriterionDraft);
  const [evidenceDraft, setEvidenceDraft] =
    useState<CreateEvidencePayload>(initialEvidenceDraft);
  const [isCreateDecisionOpen, setIsCreateDecisionOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingOptions, setIsLoadingOptions] = useState(false);
  const [isLoadingCriteria, setIsLoadingCriteria] = useState(false);
  const [isLoadingAssumptions, setIsLoadingAssumptions] = useState(false);
  const [isLoadingEvidence, setIsLoadingEvidence] = useState(false);
  const [isLoadingTradeoffMatrix, setIsLoadingTradeoffMatrix] = useState(false);
  const [isLoadingAdversarialReview, setIsLoadingAdversarialReview] =
    useState(false);
  const [isLoadingRecommendationMemo, setIsLoadingRecommendationMemo] =
    useState(false);
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);
  const [isSubmittingOption, setIsSubmittingOption] = useState(false);
  const [isSubmittingCriterion, setIsSubmittingCriterion] = useState(false);
  const [isSubmittingEvidence, setIsSubmittingEvidence] = useState(false);
  const [isGeneratingAssumptions, setIsGeneratingAssumptions] = useState(false);
  const [isGeneratingTradeoffMatrix, setIsGeneratingTradeoffMatrix] =
    useState(false);
  const [isGeneratingAdversarialReview, setIsGeneratingAdversarialReview] =
    useState(false);
  const [isGeneratingRecommendationMemo, setIsGeneratingRecommendationMemo] =
    useState(false);
  const [isExportingJson, setIsExportingJson] = useState(false);
  const [isExportingMarkdown, setIsExportingMarkdown] = useState(false);
  const [decisionErrorMessage, setDecisionErrorMessage] = useState<string | null>(
    null,
  );
  const [optionErrorMessage, setOptionErrorMessage] = useState<string | null>(
    null,
  );
  const [criterionErrorMessage, setCriterionErrorMessage] = useState<
    string | null
  >(null);
  const [evidenceErrorMessage, setEvidenceErrorMessage] = useState<
    string | null
  >(null);
  const [assumptionErrorMessage, setAssumptionErrorMessage] = useState<
    string | null
  >(null);
  const [tradeoffMatrixErrorMessage, setTradeoffMatrixErrorMessage] = useState<
    string | null
  >(null);
  const [adversarialReviewErrorMessage, setAdversarialReviewErrorMessage] =
    useState<string | null>(null);
  const [recommendationMemoErrorMessage, setRecommendationMemoErrorMessage] =
    useState<string | null>(null);
  const [exportErrorMessage, setExportErrorMessage] = useState<string | null>(
    null,
  );
  const [assumptionSuccessMessage, setAssumptionSuccessMessage] = useState<
    string | null
  >(null);
  const [tradeoffMatrixSuccessMessage, setTradeoffMatrixSuccessMessage] =
    useState<string | null>(null);
  const [adversarialReviewSuccessMessage, setAdversarialReviewSuccessMessage] =
    useState<string | null>(null);
  const [recommendationMemoSuccessMessage, setRecommendationMemoSuccessMessage] =
    useState<string | null>(null);
  const [exportSuccessMessage, setExportSuccessMessage] = useState<string | null>(
    null,
  );

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
  const canGenerateAdversarialReview =
    canGenerateTradeoffMatrix && tradeoffMatrix !== null;
  const canGenerateRecommendationMemo =
    canGenerateAdversarialReview && adversarialReview !== null;
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
      setEvidence([]);
      setSelectedAssumptionIds([]);
      setTradeoffMatrix(null);
      setAdversarialReview(null);
      setRecommendationMemo(null);
      setOptionErrorMessage(null);
      setCriterionErrorMessage(null);
      setEvidenceErrorMessage(null);
      setAssumptionErrorMessage(null);
      setTradeoffMatrixErrorMessage(null);
      setAdversarialReviewErrorMessage(null);
      setRecommendationMemoErrorMessage(null);
      setExportErrorMessage(null);
      setExportSuccessMessage(null);
      return;
    }

    void Promise.all([
      loadOptions(activeDecisionId),
      loadCriteria(activeDecisionId),
      loadAssumptions(activeDecisionId),
      loadEvidence(activeDecisionId),
      loadTradeoffMatrix(activeDecisionId),
      loadAdversarialReview(activeDecisionId),
      loadRecommendationMemo(activeDecisionId),
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

  async function loadEvidence(decisionId: string) {
    setIsLoadingEvidence(true);
    setEvidenceErrorMessage(null);

    try {
      const response = await fetch(apiUrl(`/api/v1/decisions/${decisionId}/evidence`), {
        cache: "no-store",
      });

      if (!response.ok) {
        throw new Error(`Failed to load evidence (${response.status})`);
      }

      const payload = (await response.json()) as EvidenceRecord[];
      setEvidence(payload);
    } catch (error) {
      setEvidence([]);
      setEvidenceErrorMessage(
        error instanceof Error ? error.message : "Failed to load evidence.",
      );
    } finally {
      setIsLoadingEvidence(false);
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

  async function loadAdversarialReview(decisionId: string) {
    setIsLoadingAdversarialReview(true);
    setAdversarialReviewErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${decisionId}/adversarial-review`),
        {
          cache: "no-store",
        },
      );

      if (response.status === 404) {
        setAdversarialReview(null);
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to load adversarial review (${response.status})`);
      }

      const payload = (await response.json()) as AdversarialReview;
      setAdversarialReview(payload);
    } catch (error) {
      setAdversarialReview(null);
      setAdversarialReviewErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to load adversarial review.",
      );
    } finally {
      setIsLoadingAdversarialReview(false);
    }
  }

  async function loadRecommendationMemo(decisionId: string) {
    setIsLoadingRecommendationMemo(true);
    setRecommendationMemoErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${decisionId}/recommendation-memo`),
        {
          cache: "no-store",
        },
      );

      if (response.status === 404) {
        setRecommendationMemo(null);
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to load recommendation memo (${response.status})`);
      }

      const payload = (await response.json()) as RecommendationMemo;
      setRecommendationMemo(payload);
    } catch (error) {
      setRecommendationMemo(null);
      setRecommendationMemoErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to load recommendation memo.",
      );
    } finally {
      setIsLoadingRecommendationMemo(false);
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

  async function createEvidence() {
    if (!activeDecisionId) {
      return;
    }

    setIsSubmittingEvidence(true);
    setEvidenceErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/evidence`),
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(evidenceDraft),
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to create evidence (${response.status})`);
      }

      setEvidenceDraft(initialEvidenceDraft);
      await loadEvidence(activeDecisionId);
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setIsSubmittingEvidence(false);
      setEvidenceErrorMessage(
        error instanceof Error ? error.message : "Failed to create evidence.",
      );
    } finally {
      setIsSubmittingEvidence(false);
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

  async function deleteEvidence(evidenceId: string) {
    if (!activeDecisionId) {
      return;
    }

    setEvidenceErrorMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/evidence/${evidenceId}`),
        {
          method: "DELETE",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to delete evidence (${response.status})`);
      }

      await loadEvidence(activeDecisionId);
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setEvidenceErrorMessage(
        error instanceof Error ? error.message : "Failed to delete evidence.",
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
      setTradeoffMatrix(null);
      setAdversarialReview(null);
      setRecommendationMemo(null);
      setTradeoffMatrixSuccessMessage(null);
      setAdversarialReviewSuccessMessage(null);
      setRecommendationMemoSuccessMessage(null);
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
      setAdversarialReview(null);
      setRecommendationMemo(null);
      setAdversarialReviewSuccessMessage(null);
      setRecommendationMemoSuccessMessage(null);
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

  async function generateAdversarialReview() {
    if (!activeDecisionId || !canGenerateAdversarialReview) {
      return;
    }

    setIsGeneratingAdversarialReview(true);
    setAdversarialReviewErrorMessage(null);
    setAdversarialReviewSuccessMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/adversarial-review/generate`),
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
        let detail = `Failed to generate adversarial review (${response.status})`;

        try {
          const payload = (await response.json()) as { detail?: string };
          if (payload.detail) {
            detail = payload.detail;
          }
        } catch {
          // Fall back to generic status error.
        }

        throw new Error(detail);
      }

      const payload = (await response.json()) as {
        replaced_existing: boolean;
        review: AdversarialReview;
      };
      setAdversarialReview(payload.review);
      setRecommendationMemo(null);
      setRecommendationMemoSuccessMessage(null);
      setAdversarialReviewSuccessMessage(
        payload.replaced_existing
          ? "Generated adversarial review and replaced the previous version."
          : "Generated adversarial review.",
      );
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setAdversarialReviewErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to generate adversarial review.",
      );
    } finally {
      setIsGeneratingAdversarialReview(false);
    }
  }

  async function generateRecommendationMemo() {
    if (!activeDecisionId || !canGenerateRecommendationMemo) {
      return;
    }

    setIsGeneratingRecommendationMemo(true);
    setRecommendationMemoErrorMessage(null);
    setRecommendationMemoSuccessMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/recommendation-memo/generate`),
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
        let detail = `Failed to generate recommendation memo (${response.status})`;

        try {
          const payload = (await response.json()) as { detail?: string };
          if (payload.detail) {
            detail = payload.detail;
          }
        } catch {
          // Fall back to generic status error.
        }

        throw new Error(detail);
      }

      const payload = (await response.json()) as {
        replaced_existing: boolean;
        memo: RecommendationMemo;
      };
      setRecommendationMemo(payload.memo);
      setRecommendationMemoSuccessMessage(
        payload.replaced_existing
          ? "Generated recommendation memo and replaced the previous version."
          : "Generated recommendation memo.",
      );
      await loadDecisions(activeDecisionId);
    } catch (error) {
      setRecommendationMemoErrorMessage(
        error instanceof Error
          ? error.message
          : "Failed to generate recommendation memo.",
      );
    } finally {
      setIsGeneratingRecommendationMemo(false);
    }
  }

  async function exportJson() {
    if (!activeDecisionId || !activeDecision) {
      return;
    }

    setIsExportingJson(true);
    setExportErrorMessage(null);
    setExportSuccessMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/export/json`),
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to export JSON (${response.status})`);
      }

      const payload = await response.json();
      const blob = new Blob([JSON.stringify(payload, null, 2)], {
        type: "application/json",
      });
      downloadBlob(blob, `${activeDecision.id}.json`);
      setExportSuccessMessage("Exported decision dossier as JSON.");
    } catch (error) {
      setExportErrorMessage(
        error instanceof Error ? error.message : "Failed to export JSON.",
      );
    } finally {
      setIsExportingJson(false);
    }
  }

  async function exportMarkdown() {
    if (!activeDecisionId || !activeDecision) {
      return;
    }

    setIsExportingMarkdown(true);
    setExportErrorMessage(null);
    setExportSuccessMessage(null);

    try {
      const response = await fetch(
        apiUrl(`/api/v1/decisions/${activeDecisionId}/export/markdown`),
        {
          cache: "no-store",
        },
      );

      if (!response.ok) {
        throw new Error(`Failed to export Markdown (${response.status})`);
      }

      const content = await response.text();
      const blob = new Blob([content], {
        type: "text/markdown;charset=utf-8",
      });
      downloadBlob(blob, `${activeDecision.id}.md`);
      setExportSuccessMessage("Exported decision dossier as Markdown.");
    } catch (error) {
      setExportErrorMessage(
        error instanceof Error ? error.message : "Failed to export Markdown.",
      );
    } finally {
      setIsExportingMarkdown(false);
    }
  }

  return {
    decisions,
    options,
    criteria,
    assumptions,
    evidence,
    selectedAssumptionIds,
    tradeoffMatrix,
    adversarialReview,
    recommendationMemo,
    activeSection,
    activeDecisionId,
    activeDecision,
    optionMap,
    decisionDraft,
    optionDraft,
    criterionDraft,
    evidenceDraft,
    isCreateDecisionOpen,
    isLoading,
    isLoadingOptions,
    isLoadingCriteria,
    isLoadingAssumptions,
    isLoadingEvidence,
    isLoadingTradeoffMatrix,
    isLoadingAdversarialReview,
    isLoadingRecommendationMemo,
    isSubmittingDecision,
    isSubmittingOption,
    isSubmittingCriterion,
    isSubmittingEvidence,
    isGeneratingAssumptions,
    isGeneratingTradeoffMatrix,
    isGeneratingAdversarialReview,
    isGeneratingRecommendationMemo,
    isExportingJson,
    isExportingMarkdown,
    decisionErrorMessage,
    optionErrorMessage,
    criterionErrorMessage,
    evidenceErrorMessage,
    assumptionErrorMessage,
    tradeoffMatrixErrorMessage,
    adversarialReviewErrorMessage,
    recommendationMemoErrorMessage,
    exportErrorMessage,
    assumptionSuccessMessage,
    tradeoffMatrixSuccessMessage,
    adversarialReviewSuccessMessage,
    recommendationMemoSuccessMessage,
    exportSuccessMessage,
    canGenerateAssumptions,
    canRegenerateSelectedAssumptions,
    canGenerateTradeoffMatrix,
    canGenerateAdversarialReview,
    canGenerateRecommendationMemo,
    showDecisionBrief,
    showDecisionQuestion,
    setActiveDecisionId,
    setActiveSection,
    setDecisionDraft,
    setOptionDraft,
    setCriterionDraft,
    setEvidenceDraft,
    openCreateDecisionModal,
    closeCreateDecisionModal,
    createDecision,
    deleteDecision,
    createOption,
    deleteOption,
    createCriterion,
    deleteCriterion,
    createEvidence,
    deleteEvidence,
    generateAssumptions,
    toggleAssumptionSelection,
    selectAllAssumptions,
    clearAssumptionSelection,
    generateTradeoffMatrix,
    generateAdversarialReview,
    generateRecommendationMemo,
    exportJson,
    exportMarkdown,
  };
}

function downloadBlob(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  window.URL.revokeObjectURL(url);
}
