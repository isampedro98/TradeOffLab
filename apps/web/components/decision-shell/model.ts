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

export const decisionTypes = [
  { value: "erp_adoption", label: "ERP Adoption" },
  { value: "architecture", label: "Architecture" },
  { value: "cloud_provider", label: "Cloud Provider" },
  { value: "build_vs_buy", label: "Build vs Buy" },
  { value: "procurement_automation", label: "Procurement Automation" },
  { value: "software_stack", label: "Software Stack" },
  { value: "strategic_technical", label: "Strategic Technical" },
] as const;

export const criterionMeasurementTypes = [
  { value: "qualitative", label: "Qualitative" },
  { value: "numeric", label: "Numeric" },
  { value: "boolean", label: "Boolean" },
  { value: "ordinal", label: "Ordinal" },
] as const;

export type DecisionType = (typeof decisionTypes)[number]["value"];
export type DecisionStatus = "draft" | "in_review" | "recommended" | "archived";
export type CriterionMeasurementType =
  (typeof criterionMeasurementTypes)[number]["value"];

export type Decision = {
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

export type CreateDecisionPayload = {
  title: string;
  decision_brief: string;
  question: string;
  context: string;
  type: DecisionType;
  status: DecisionStatus;
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

export const initialDecisionDraft: CreateDecisionPayload = {
  title: "",
  decision_brief: "",
  question: "",
  context: "",
  type: "software_stack",
  status: "draft",
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

export function typeLabel(type: DecisionType): string {
  return decisionTypes.find((item) => item.value === type)?.label ?? type;
}

export function measurementTypeLabel(type: CriterionMeasurementType): string {
  return (
    criterionMeasurementTypes.find((item) => item.value === type)?.label ?? type
  );
}

export function confidenceLabel(confidence: Assumption["confidence"]): string {
  return confidence.charAt(0).toUpperCase() + confidence.slice(1);
}

export function normalizeText(value: string): string {
  return value.trim().toLowerCase();
}

export function statusClasses(status: DecisionStatus): string {
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

export type DecisionWorkspaceController = {
  decisions: Decision[];
  options: OptionRecord[];
  criteria: CriterionRecord[];
  assumptions: Assumption[];
  selectedAssumptionIds: string[];
  tradeoffMatrix: TradeoffMatrix | null;
  activeDecisionId: string | null;
  activeDecision: Decision | null;
  optionMap: Map<string, OptionRecord>;
  decisionDraft: CreateDecisionPayload;
  optionDraft: CreateOptionPayload;
  criterionDraft: CreateCriterionPayload;
  isCreateDecisionOpen: boolean;
  isLoading: boolean;
  isLoadingOptions: boolean;
  isLoadingCriteria: boolean;
  isLoadingAssumptions: boolean;
  isLoadingTradeoffMatrix: boolean;
  isSubmittingDecision: boolean;
  isSubmittingOption: boolean;
  isSubmittingCriterion: boolean;
  isGeneratingAssumptions: boolean;
  isGeneratingTradeoffMatrix: boolean;
  decisionErrorMessage: string | null;
  optionErrorMessage: string | null;
  criterionErrorMessage: string | null;
  assumptionErrorMessage: string | null;
  tradeoffMatrixErrorMessage: string | null;
  assumptionSuccessMessage: string | null;
  tradeoffMatrixSuccessMessage: string | null;
  canGenerateAssumptions: boolean;
  canRegenerateSelectedAssumptions: boolean;
  canGenerateTradeoffMatrix: boolean;
  showDecisionBrief: boolean;
  showDecisionQuestion: boolean;
  setActiveDecisionId: Dispatch<SetStateAction<string | null>>;
  setDecisionDraft: Dispatch<SetStateAction<CreateDecisionPayload>>;
  setOptionDraft: Dispatch<SetStateAction<CreateOptionPayload>>;
  setCriterionDraft: Dispatch<SetStateAction<CreateCriterionPayload>>;
  openCreateDecisionModal: () => void;
  closeCreateDecisionModal: () => void;
  createDecision: () => Promise<void>;
  deleteDecision: () => Promise<void>;
  createOption: () => Promise<void>;
  deleteOption: (optionId: string) => Promise<void>;
  createCriterion: () => Promise<void>;
  deleteCriterion: (criterionId: string) => Promise<void>;
  generateAssumptions: () => Promise<void>;
  toggleAssumptionSelection: (assumptionId: string) => void;
  selectAllAssumptions: () => void;
  clearAssumptionSelection: () => void;
  generateTradeoffMatrix: () => Promise<void>;
};
