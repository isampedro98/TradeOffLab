from __future__ import annotations

import json

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.domain.assumption import Assumption
from app.domain.criterion import Criterion
from app.domain.decision import Decision
from app.domain.evidence import Evidence, EvidenceCreate, EvidenceSourceType
from app.domain.option import Option
from app.persistence.assumption_repository import AssumptionRepository
from app.persistence.criterion_repository import CriterionRepository
from app.persistence.decision_repository import DecisionRepository
from app.persistence.evidence_repository import EvidenceRepository
from app.persistence.option_repository import OptionRepository
from app.services.litellm_client import LiteLLMClient
from app.services.web_research import (
    PageFetcher,
    RetrievedDocument,
    SearchProvider,
    WebResearchError,
    build_page_fetcher,
    build_search_provider,
)


class EvidenceGenerationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    count: int = Field(default=4, ge=1, le=7)
    replace_existing: bool = False
    research_focus: str | None = Field(default=None, max_length=500)
    seed_urls: list[str] = Field(default_factory=list, max_length=10)
    allow_web_search: bool = True
    max_queries: int = Field(default=3, ge=1, le=5)
    max_results_per_query: int = Field(default=2, ge=1, le=5)
    max_sources: int = Field(default=6, ge=1, le=10)


class PlannedResearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str
    reason: str


class EvidenceResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    gaps: list[str] = Field(default_factory=list, max_length=5)
    queries: list[PlannedResearchQuery] = Field(default_factory=list, max_length=5)
    target_urls: list[str] = Field(default_factory=list, max_length=10)


class SourcePacket(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    url: str
    excerpt: str
    query: str | None = None
    provider: str
    rank: int | None = None
    retrieved_at: str


class GeneratedEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: list[EvidenceCreate] = Field(min_length=1, max_length=7)


class ReviewedEvidencePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence: list[EvidenceCreate] = Field(min_length=1, max_length=7)


class EvidenceGenerationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision_id: str
    replaced_existing: bool
    model: str
    agents_run: list[str]
    used_web_research: bool
    web_queries: list[str]
    web_sources_consulted: int
    evidence: list[Evidence]


class EvidenceGenerationService:
    def __init__(
        self,
        session: Session,
        *,
        client: LiteLLMClient | None = None,
        search_provider: SearchProvider | None = None,
        page_fetcher: PageFetcher | None = None,
    ) -> None:
        self.session = session
        self.client = client or LiteLLMClient()
        self.search_provider = search_provider or build_search_provider()
        self.page_fetcher = page_fetcher or build_page_fetcher()
        self.assumption_repository = AssumptionRepository(session)
        self.criterion_repository = CriterionRepository(session)
        self.decision_repository = DecisionRepository(session)
        self.evidence_repository = EvidenceRepository(session)
        self.option_repository = OptionRepository(session)

    def generate_for_decision(
        self,
        decision_id: str,
        request: EvidenceGenerationRequest,
    ) -> EvidenceGenerationResponse:
        decision = self.decision_repository.get(decision_id)
        if decision is None:
            raise ValueError(f"Decision '{decision_id}' was not found.")

        options = self.option_repository.list_for_decision(decision_id)
        criteria = self.criterion_repository.list_for_decision(decision_id)
        assumptions = self.assumption_repository.list_for_decision(decision_id)
        existing_evidence = self.evidence_repository.list_for_decision(decision_id)

        if not request.allow_web_search and not request.seed_urls:
            raise ValueError("Evidence research requires web search or at least one seed URL.")

        plan = self._plan_research(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            existing_evidence=existing_evidence,
            request=request,
        )
        documents = self._collect_documents(plan=plan, request=request)
        if not documents:
            raise ValueError("Evidence research did not return any readable external sources.")

        synthesized = self._synthesize_evidence(
            decision=decision,
            options=options,
            criteria=criteria,
            assumptions=assumptions,
            existing_evidence=existing_evidence,
            documents=documents,
            request=request,
        )
        reviewed = self._criticize_evidence(
            decision=decision,
            existing_evidence=existing_evidence,
            documents=documents,
            generated=synthesized,
            request=request,
        )
        self._validate_generated_evidence(
            reviewed.evidence,
            expected_count=request.count,
            documents=documents,
        )

        replaced_existing = False
        if request.replace_existing:
            evidence = self.evidence_repository.replace_for_decision(
                decision_id,
                reviewed.evidence,
            )
            replaced_existing = bool(existing_evidence)
        else:
            self.evidence_repository.create_many(decision_id, reviewed.evidence)
            evidence = self.evidence_repository.list_for_decision(decision_id)

        return EvidenceGenerationResponse(
            decision_id=decision_id,
            replaced_existing=replaced_existing,
            model=self.client.model,
            agents_run=["planner", "researcher", "synthesizer", "critic"],
            used_web_research=True,
            web_queries=[query.query for query in plan.queries],
            web_sources_consulted=len(documents),
            evidence=evidence,
        )

    def _plan_research(
        self,
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        assumptions: list[Assumption],
        existing_evidence: list[Evidence],
        request: EvidenceGenerationRequest,
    ) -> EvidenceResearchPlan:
        decision_snapshot = {
            "decision": {
                "title": decision.title,
                "decision_brief": _truncate_text(decision.decision_brief, limit=180),
                "question": _truncate_text(decision.question, limit=220),
                "context_summary": _truncate_text(decision.context, limit=320),
            },
            "options": [
                {
                    "name": option.name,
                    "description": _truncate_text(option.description, limit=120),
                }
                for option in options
            ],
            "criteria": [
                {
                    "name": criterion.name,
                    "weight": criterion.weight,
                }
                for criterion in criteria
            ],
            "assumptions": [
                _truncate_text(assumption.statement, limit=140) for assumption in assumptions[:6]
            ],
            "existing_evidence_titles": [
                _truncate_text(evidence.title, limit=100) for evidence in existing_evidence[:6]
            ],
            "research_focus": request.research_focus,
            "seed_urls": request.seed_urls,
        }
        plan = self.client.generate_structured(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the planner agent for TradeOffLab web research. "
                        "Identify the highest-value missing facts and propose a bounded search plan. "
                        "Prefer highly specific search queries over broad ones. "
                        "Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Plan a web research pass for this decision. "
                        f"Return at most {request.max_queries} search queries and at most {len(request.seed_urls)} direct URLs from the provided seed set. "
                        "If research_focus is set, prioritize it. "
                        "Use target_urls only when a specific URL should definitely be fetched.\n\n"
                        f"{json.dumps(decision_snapshot, indent=2)}"
                    ),
                },
            ],
            response_model=EvidenceResearchPlan,
            temperature=0.1,
            max_tokens=320,
        )

        heuristic_queries = self._build_heuristic_queries(
            decision=decision,
            options=options,
            request=request,
        )
        merged_queries = _deduplicate_queries([*plan.queries, *heuristic_queries])[: request.max_queries]
        plan = plan.model_copy(update={"queries": merged_queries})

        if request.seed_urls:
            merged_urls = _deduplicate_preserve_order([*request.seed_urls, *plan.target_urls])
            plan = plan.model_copy(update={"target_urls": merged_urls[: len(request.seed_urls)]})

        if request.allow_web_search and not plan.queries:
            fallback_query = request.research_focus or decision.question or decision.title
            plan = plan.model_copy(
                update={
                    "queries": [
                        PlannedResearchQuery(
                            query=fallback_query,
                            reason="Fallback query derived from the active decision frame.",
                        )
                    ]
                }
            )
        return plan

    def _collect_documents(
        self,
        *,
        plan: EvidenceResearchPlan,
        request: EvidenceGenerationRequest,
    ) -> list[RetrievedDocument]:
        documents: list[RetrievedDocument] = []
        seen_urls: set[str] = set()

        for target_url in plan.target_urls:
            try:
                document = self.page_fetcher.fetch(url=target_url)
            except WebResearchError:
                continue
            if document.url in seen_urls:
                continue
            seen_urls.add(document.url)
            documents.append(document)
            if len(documents) >= request.max_sources:
                return documents

        if request.allow_web_search:
            for planned_query in plan.queries[: request.max_queries]:
                try:
                    results = self.search_provider.search(
                        query=planned_query.query,
                        max_results=request.max_results_per_query,
                    )
                except WebResearchError:
                    continue
                for result in results:
                    try:
                        document = self.page_fetcher.fetch(
                            url=result.url,
                            query=result.query,
                            rank=result.rank,
                        )
                    except WebResearchError:
                        continue
                    if document.url in seen_urls:
                        continue
                    seen_urls.add(document.url)
                    documents.append(document)
                    if len(documents) >= request.max_sources:
                        return documents
        return documents

    def _synthesize_evidence(
        self,
        *,
        decision: Decision,
        options: list[Option],
        criteria: list[Criterion],
        assumptions: list[Assumption],
        existing_evidence: list[Evidence],
        documents: list[RetrievedDocument],
        request: EvidenceGenerationRequest,
    ) -> GeneratedEvidencePayload:
        synthesis_snapshot = {
            "decision": {
                "title": decision.title,
                "question": _truncate_text(decision.question, limit=220),
            },
            "options": [option.name for option in options],
            "criteria": [criterion.name for criterion in criteria],
            "assumptions": [
                _truncate_text(assumption.statement, limit=120) for assumption in assumptions[:6]
            ],
            "existing_evidence_titles": [
                _truncate_text(evidence.title, limit=100) for evidence in existing_evidence[:6]
            ],
            "sources": [self._to_source_packet(document).model_dump(mode="json") for document in documents],
            "research_focus": request.research_focus,
        }
        return self.client.generate_structured(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the synthesizer agent for TradeOffLab. "
                        "Convert fetched external sources into evidence records grounded in the provided excerpts. "
                        "Each evidence item must be traceable to one fetched source. "
                        "Set source_type to web_capture, copy the chosen URL into source_url, "
                        "store the supporting excerpt, and set retrieval_agent to researcher. "
                        "Do not invent facts outside the excerpts. Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Generate exactly {request.count} evidence items from these fetched sources. "
                        "Each item must be decision-relevant, concise, and source-backed. "
                        "Use the source field for a human-readable citation label.\n\n"
                        f"{json.dumps(synthesis_snapshot, indent=2)}"
                    ),
                },
            ],
            response_model=GeneratedEvidencePayload,
            temperature=0.1,
            max_tokens=900,
        )

    def _criticize_evidence(
        self,
        *,
        decision: Decision,
        existing_evidence: list[Evidence],
        documents: list[RetrievedDocument],
        generated: GeneratedEvidencePayload,
        request: EvidenceGenerationRequest,
    ) -> ReviewedEvidencePayload:
        review_snapshot = {
            "decision": {
                "title": decision.title,
                "question": _truncate_text(decision.question, limit=220),
            },
            "existing_evidence_titles": [
                _truncate_text(evidence.title, limit=100) for evidence in existing_evidence[:6]
            ],
            "sources": [self._to_source_packet(document).model_dump(mode="json") for document in documents],
            "draft_evidence": [evidence.model_dump(mode="json") for evidence in generated.evidence],
            "research_focus": request.research_focus,
        }
        return self.client.generate_structured(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are the critic agent for TradeOffLab evidence research. "
                        "Tighten the draft evidence set, remove weak or duplicate items, and ensure every item stays grounded in the provided sources. "
                        "Do not add unsupported claims. Keep exactly the requested number of evidence items. "
                        "Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Review and correct this draft evidence set. Keep exactly {request.count} items. "
                        "Every item must cite one of the fetched source URLs, keep source_type as web_capture, "
                        "and preserve concise excerpts.\n\n"
                        f"{json.dumps(review_snapshot, indent=2)}"
                    ),
                },
            ],
            response_model=ReviewedEvidencePayload,
            temperature=0.1,
            max_tokens=900,
        )

    @staticmethod
    def _build_heuristic_queries(
        *,
        decision: Decision,
        options: list[Option],
        request: EvidenceGenerationRequest,
    ) -> list[PlannedResearchQuery]:
        query_candidates = [
            request.research_focus or "",
            decision.title,
            decision.question,
        ]
        query_candidates.extend(f"{option.name} official documentation" for option in options[:2])
        query_candidates.extend(
            f"{keyword} official documentation"
            for keyword in _extract_topic_keywords(decision.title, decision.question)
        )
        queries: list[PlannedResearchQuery] = []
        for candidate in query_candidates:
            normalized = _normalize_query(candidate)
            if not normalized:
                continue
            queries.append(
                PlannedResearchQuery(
                    query=normalized,
                    reason="Deterministic fallback query derived from the decision frame.",
                )
            )
        return queries

    @staticmethod
    def _validate_generated_evidence(
        evidence: list[EvidenceCreate],
        *,
        expected_count: int,
        documents: list[RetrievedDocument],
    ) -> None:
        if len(evidence) != expected_count:
            raise ValueError(
                f"Generated evidence count mismatch: expected {expected_count}, received {len(evidence)}."
            )

        normalized_titles = {item.title.strip().lower() for item in evidence}
        if len(normalized_titles) != len(evidence):
            raise ValueError("Generated evidence titles must be unique.")

        available_urls = {document.url for document in documents}
        for item in evidence:
            if item.source_type != EvidenceSourceType.WEB_CAPTURE:
                raise ValueError("Web research evidence must use source_type='web_capture'.")
            if not item.source_url or item.source_url not in available_urls:
                raise ValueError("Every generated evidence item must reference a fetched source URL.")
            if not item.excerpt:
                raise ValueError("Every generated evidence item must include a supporting excerpt.")
            if item.retrieval_agent != "researcher":
                raise ValueError("Every generated evidence item must record retrieval_agent='researcher'.")

    @staticmethod
    def _to_source_packet(document: RetrievedDocument) -> SourcePacket:
        return SourcePacket(
            title=document.title,
            url=document.url,
            excerpt=document.excerpt,
            query=document.query,
            provider=document.provider,
            rank=document.rank,
            retrieved_at=document.retrieved_at.isoformat(),
        )


def _deduplicate_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduplicated: list[str] = []
    for value in values:
        normalized = value.strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(normalized)
    return deduplicated


def _deduplicate_queries(values: list[PlannedResearchQuery]) -> list[PlannedResearchQuery]:
    seen: set[str] = set()
    deduplicated: list[PlannedResearchQuery] = []
    for value in values:
        normalized = _normalize_query(value.query)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduplicated.append(value.model_copy(update={"query": normalized}))
    return deduplicated


def _extract_topic_keywords(*values: str) -> list[str]:
    keywords: list[str] = []
    for value in values:
        normalized = " ".join(value.split()).lower()
        for candidate in [
            "hyper-v",
            "ubuntu",
            "ubuntu server",
            "virtual hard disk",
            "vhdx",
            "disk resize",
            "extend disk",
        ]:
            if candidate in normalized and candidate not in keywords:
                keywords.append(candidate)
    return keywords[:3]


def _normalize_query(value: str) -> str:
    normalized = " ".join(value.split()).strip()
    if len(normalized) > 180:
        normalized = normalized[:180].rstrip()
    return normalized


def _truncate_text(value: str, *, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."
