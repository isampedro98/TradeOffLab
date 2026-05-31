import type { Dispatch, SetStateAction } from "react";

export const sections = [
  "Overview",
  "Options",
  "Criteria",
  "Assumptions",
  "Evidence",
  "Tradeoffs",
  "Adversarial Review",
  "Recommendation",
  "Export",
] as const;

export type WorkspaceSection = (typeof sections)[number];

export const criterionMeasurementTypes = [
  { value: "qualitative", label: "Qualitative" },
  { value: "numeric", label: "Numeric" },
  { value: "boolean", label: "Boolean" },
  { value: "ordinal", label: "Ordinal" },
] as const;

export type CriterionMeasurementType =
  (typeof criterionMeasurementTypes)[number]["value"];

export type Decision = {
  id: string;
  title: string;
  decision_brief: string;
  question: string;
  context: string;
  created_at: string;
  updated_at: string;
};

export type OptionRecord = {
  id: string;
  decision_id: string;
  name: string;
  description: string;
  created_at: string;
  updated_at: string;
};

export type CriterionRecord = {
  id: string;
  decision_id: string;
  name: string;
  description: string;
  weight: number;
  measurement_type: CriterionMeasurementType;
  created_at: string;
  updated_at: string;
};

export type Assumption = {
  id: string;
  decision_id: string;
  statement: string;
  confidence: "low" | "medium" | "high";
  impact_if_false: string;
  validation_method: string;
  created_at: string;
  updated_at: string;
};

export type EvidenceRecord = {
  id: string;
  decision_id: string;
  title: string;
  summary: string;
  source: string;
  created_at: string;
  updated_at: string;
};

export type TradeoffAssessment = {
  id: string;
  matrix_id: string;
  criterion_id: string;
  option_id: string;
  score: number;
  rationale: string;
  created_at: string;
  updated_at: string;
};

export type TradeoffMatrix = {
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

export type AdversarialReviewSeverity = "low" | "medium" | "high";

export type AdversarialReviewFinding = {
  id: string;
  review_id: string;
  title: string;
  severity: AdversarialReviewSeverity;
  critique: string;
  consequence: string;
  mitigation_test: string;
  created_at: string;
  updated_at: string;
};

export type AdversarialReview = {
  id: string;
  decision_id: string;
  summary: string;
  overall_risk: AdversarialReviewSeverity;
  provider: string;
  model: string;
  created_at: string;
  updated_at: string;
  findings: AdversarialReviewFinding[];
};

export type RecommendationConfidence = "low" | "medium" | "high";

export type RecommendationCondition = {
  id: string;
  memo_id: string;
  position: number;
  statement: string;
  created_at: string;
  updated_at: string;
};

export type RecommendationMemo = {
  id: string;
  decision_id: string;
  recommended_option_id: string;
  fallback_option_id: string | null;
  rationale: string;
  confidence: RecommendationConfidence;
  provider: string;
  model: string;
  created_at: string;
  updated_at: string;
  conditions: RecommendationCondition[];
};

export type DecisionDossierExport = {
  decision: Decision;
  options: OptionRecord[];
  criteria: CriterionRecord[];
  assumptions: Assumption[];
  evidence: EvidenceRecord[];
  tradeoff_matrix: TradeoffMatrix | null;
  adversarial_review: AdversarialReview | null;
  recommendation_memo: RecommendationMemo | null;
};

export type CreateDecisionPayload = {
  title: string;
  decision_brief: string;
  question: string;
  context: string;
};

export type CreateOptionPayload = {
  name: string;
  description: string;
};

export type CreateCriterionPayload = {
  name: string;
  description: string;
  weight: string;
  measurement_type: CriterionMeasurementType;
};

export type CreateEvidencePayload = {
  title: string;
  summary: string;
  source: string;
};

export const initialDecisionDraft: CreateDecisionPayload = {
  title: "",
  decision_brief: "",
  question: "",
  context: "",
};

export const initialOptionDraft: CreateOptionPayload = {
  name: "",
  description: "",
};

export const initialCriterionDraft: CreateCriterionPayload = {
  name: "",
  description: "",
  weight: "0.20",
  measurement_type: "qualitative",
};

export const initialEvidenceDraft: CreateEvidencePayload = {
  title: "",
  summary: "",
  source: "",
};

export function apiUrl(path: string): string {
  const baseUrl =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  return `${baseUrl}${path}`;
}

export function formatTimestamp(timestamp: string): string {
  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(timestamp));
}

export function measurementTypeLabel(type: CriterionMeasurementType): string {
  return (
    criterionMeasurementTypes.find((item) => item.value === type)?.label ?? type
  );
}

export function confidenceLabel(confidence: Assumption["confidence"]): string {
  return confidence.charAt(0).toUpperCase() + confidence.slice(1);
}

export function severityLabel(severity: AdversarialReviewSeverity): string {
  return severity.charAt(0).toUpperCase() + severity.slice(1);
}

export function recommendationConfidenceLabel(
  confidence: RecommendationConfidence,
): string {
  return confidence.charAt(0).toUpperCase() + confidence.slice(1);
}

export function normalizeText(value: string): string {
  return value.trim().toLowerCase();
}

export type DecisionWorkspaceController = {
  decisions: Decision[];
  options: OptionRecord[];
  criteria: CriterionRecord[];
  assumptions: Assumption[];
  evidence: EvidenceRecord[];
  selectedAssumptionIds: string[];
  tradeoffMatrix: TradeoffMatrix | null;
  adversarialReview: AdversarialReview | null;
  recommendationMemo: RecommendationMemo | null;
  activeSection: WorkspaceSection;
  activeDecisionId: string | null;
  activeDecision: Decision | null;
  optionMap: Map<string, OptionRecord>;
  decisionDraft: CreateDecisionPayload;
  optionDraft: CreateOptionPayload;
  criterionDraft: CreateCriterionPayload;
  evidenceDraft: CreateEvidencePayload;
  isCreateDecisionOpen: boolean;
  isLoading: boolean;
  isLoadingOptions: boolean;
  isLoadingCriteria: boolean;
  isLoadingAssumptions: boolean;
  isLoadingEvidence: boolean;
  isLoadingTradeoffMatrix: boolean;
  isLoadingAdversarialReview: boolean;
  isLoadingRecommendationMemo: boolean;
  isSubmittingDecision: boolean;
  isSubmittingOption: boolean;
  isSubmittingCriterion: boolean;
  isSubmittingEvidence: boolean;
  isGeneratingAssumptions: boolean;
  isGeneratingTradeoffMatrix: boolean;
  isGeneratingAdversarialReview: boolean;
  isGeneratingRecommendationMemo: boolean;
  isExportingJson: boolean;
  isExportingMarkdown: boolean;
  decisionErrorMessage: string | null;
  optionErrorMessage: string | null;
  criterionErrorMessage: string | null;
  evidenceErrorMessage: string | null;
  assumptionErrorMessage: string | null;
  tradeoffMatrixErrorMessage: string | null;
  adversarialReviewErrorMessage: string | null;
  recommendationMemoErrorMessage: string | null;
  exportErrorMessage: string | null;
  assumptionSuccessMessage: string | null;
  tradeoffMatrixSuccessMessage: string | null;
  adversarialReviewSuccessMessage: string | null;
  recommendationMemoSuccessMessage: string | null;
  exportSuccessMessage: string | null;
  canGenerateAssumptions: boolean;
  canRegenerateSelectedAssumptions: boolean;
  canGenerateTradeoffMatrix: boolean;
  canGenerateAdversarialReview: boolean;
  canGenerateRecommendationMemo: boolean;
  showDecisionBrief: boolean;
  showDecisionQuestion: boolean;
  setActiveDecisionId: Dispatch<SetStateAction<string | null>>;
  setActiveSection: Dispatch<SetStateAction<WorkspaceSection>>;
  setDecisionDraft: Dispatch<SetStateAction<CreateDecisionPayload>>;
  setOptionDraft: Dispatch<SetStateAction<CreateOptionPayload>>;
  setCriterionDraft: Dispatch<SetStateAction<CreateCriterionPayload>>;
  setEvidenceDraft: Dispatch<SetStateAction<CreateEvidencePayload>>;
  openCreateDecisionModal: () => void;
  closeCreateDecisionModal: () => void;
  createDecision: () => Promise<void>;
  deleteDecision: () => Promise<void>;
  createOption: () => Promise<void>;
  deleteOption: (optionId: string) => Promise<void>;
  createCriterion: () => Promise<void>;
  deleteCriterion: (criterionId: string) => Promise<void>;
  createEvidence: () => Promise<void>;
  deleteEvidence: (evidenceId: string) => Promise<void>;
  generateAssumptions: () => Promise<void>;
  toggleAssumptionSelection: (assumptionId: string) => void;
  selectAllAssumptions: () => void;
  clearAssumptionSelection: () => void;
  generateTradeoffMatrix: () => Promise<void>;
  generateAdversarialReview: () => Promise<void>;
  generateRecommendationMemo: () => Promise<void>;
  exportJson: () => Promise<void>;
  exportMarkdown: () => Promise<void>;
};
