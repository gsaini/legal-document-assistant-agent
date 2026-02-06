"""Legal Document Assistant - API Schemas using Pydantic."""

from datetime import datetime
from typing import Any
from enum import Enum

from pydantic import BaseModel, Field


# Enums
class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplianceLevel(str, Enum):
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class Priority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ResearchType(str, Enum):
    GENERAL = "general"
    CASE_LAW = "case_law"
    STATUTE = "statute"
    MARKET_STANDARD = "market_standard"


# Request Models
class DocumentUploadConfig(BaseModel):
    """Configuration for document upload and processing."""
    
    detect_pii: bool = Field(default=True, description="Enable PII detection")
    redact_pii: bool = Field(default=False, description="Redact detected PII")
    compliance_frameworks: list[str] | None = Field(
        default=None,
        description="Specific compliance frameworks to check (auto-detect if not specified)"
    )
    jurisdiction: str | None = Field(
        default=None,
        description="Primary jurisdiction for the document"
    )
    industry: str | None = Field(
        default=None,
        description="Industry context for specialized checks"
    )
    focus_areas: list[str] | None = Field(
        default=None,
        description="Specific areas to focus analysis on"
    )


class AnalysisRequest(BaseModel):
    """Request for document analysis."""
    
    document_id: str = Field(..., description="ID of the uploaded document")
    focus_areas: list[str] | None = Field(
        default=None,
        description="Specific areas to focus on"
    )
    comparison_standard: str | None = Field(
        default=None,
        description="Standard template to compare against"
    )


class ResearchRequest(BaseModel):
    """Request for legal research."""
    
    query: str = Field(..., description="Research query")
    research_type: ResearchType = Field(
        default=ResearchType.GENERAL,
        description="Type of legal research"
    )
    jurisdiction: str | None = Field(default=None)
    document_id: str | None = Field(
        default=None,
        description="Associated document for context"
    )


class ComplianceCheckRequest(BaseModel):
    """Request for compliance check."""
    
    document_id: str = Field(..., description="ID of the uploaded document")
    frameworks: list[str] | None = Field(
        default=None,
        description="Frameworks to check (auto-detect if not specified)"
    )
    jurisdiction: str | None = Field(default=None)
    industry: str | None = Field(default=None)


class RedlineRequest(BaseModel):
    """Request for redline generation."""
    
    document_id: str = Field(..., description="ID of the uploaded document")
    analysis_id: str | None = Field(
        default=None,
        description="ID of previous analysis (if available)"
    )
    clause_library: dict | None = Field(
        default=None,
        description="Pre-approved clause library"
    )
    style_guide: dict | None = Field(
        default=None,
        description="Institutional style guide"
    )


class ApplySuggestionsRequest(BaseModel):
    """Request to apply redline suggestions."""
    
    document_id: str = Field(...)
    suggestion_ids: list[str] = Field(
        ...,
        description="IDs of suggestions to apply"
    )


# Response Models
class DocumentMetadata(BaseModel):
    """Document metadata extracted from processing."""
    
    document_type: str | None = None
    parties: list[str] = Field(default_factory=list)
    effective_date: str | None = None
    governing_law: str | None = None
    key_terms: list[str] = Field(default_factory=list)
    estimated_risk_level: str | None = None


class PIIFinding(BaseModel):
    """PII detection result."""
    
    entity_type: str
    start: int
    end: int
    score: float
    text_snippet: str


class DocumentUploadResponse(BaseModel):
    """Response from document upload."""
    
    document_id: str
    file_name: str
    file_type: str
    file_size_bytes: int
    processed_at: str
    page_count: int
    word_count: int
    metadata: DocumentMetadata
    pii_findings_count: int = 0
    pii_redacted: bool = False
    status: str = "processed"


class RiskItem(BaseModel):
    """High-risk item identified in analysis."""
    
    clause_text: str
    category: str
    severity: str
    concern: str
    mitigation: str | None = None


class ClauseAnalysis(BaseModel):
    """Analyzed clause from the document."""
    
    clause_type: str
    summary: str
    full_text: str | None = None
    key_terms: list[str] = Field(default_factory=list)
    favorability: str
    location: str | None = None
    notes: str | None = None


class Obligation(BaseModel):
    """Extracted obligation from the document."""
    
    obligated_party: str
    obligation: str
    deadline: str | None = None
    recurrence: str
    consequences: str | None = None
    priority: str
    location: str | None = None


class AnalysisResponse(BaseModel):
    """Response from contract analysis."""
    
    document_id: str
    analyzed_at: str
    overall_risk_score: int
    risk_level: RiskLevel
    risk_summary: str
    high_risk_items: list[RiskItem] = Field(default_factory=list)
    clauses: list[ClauseAnalysis] = Field(default_factory=list)
    obligations: list[Obligation] = Field(default_factory=list)
    recommendations: list[dict] = Field(default_factory=list)


class Citation(BaseModel):
    """Legal citation."""
    
    type: str
    bluebook: str
    short_form: str | None = None
    pin_cite: str | None = None


class ResearchFinding(BaseModel):
    """Legal research finding."""
    
    finding: str
    significance: str
    source: str | None = None


class ResearchResponse(BaseModel):
    """Response from legal research."""
    
    query: str
    research_type: str
    researched_at: str
    findings: list[ResearchFinding] = Field(default_factory=list)
    relevant_cases: list[dict] = Field(default_factory=list)
    relevant_statutes: list[dict] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    confidence_score: float
    sources_count: int


class ComplianceGap(BaseModel):
    """Identified compliance gap."""
    
    framework: str
    area: str | None = None
    severity: str
    description: str
    remediation: str | None = None


class RegulatoryMapping(BaseModel):
    """Mapping of clause to regulation."""
    
    clause_summary: str
    clause_location: str | None = None
    regulations: list[dict] = Field(default_factory=list)


class ComplianceResponse(BaseModel):
    """Response from compliance assessment."""
    
    document_id: str
    assessed_at: str
    overall_compliance_score: float
    compliance_level: ComplianceLevel
    frameworks_checked: list[str]
    gaps_identified: list[ComplianceGap] = Field(default_factory=list)
    regulatory_mapping: list[RegulatoryMapping] = Field(default_factory=list)
    recommendations: list[dict] = Field(default_factory=list)


class RedlineSuggestion(BaseModel):
    """Redline suggestion."""
    
    id: str
    type: str
    category: str
    priority: Priority
    original_text: str
    suggested_text: str
    changes_made: list[str] = Field(default_factory=list)
    rationale: str


class RedlineResponse(BaseModel):
    """Response from redline generation."""
    
    document_id: str
    generated_at: str
    total_suggestions: int
    suggestions: list[RedlineSuggestion] = Field(default_factory=list)
    by_priority: dict = Field(default_factory=dict)
    summary: dict = Field(default_factory=dict)


class ExecutiveSummary(BaseModel):
    """Executive summary for decision-makers."""
    
    overall_recommendation: str
    urgency: str
    risk_level: str
    compliance_level: str
    key_findings: dict
    action_required: list[str] = Field(default_factory=list)


class FullReviewResponse(BaseModel):
    """Complete legal document review response."""
    
    document_id: str
    generated_at: str
    status: str
    executive_summary: ExecutiveSummary
    document_overview: dict
    risk_assessment: dict
    contract_analysis: dict
    compliance_assessment: dict
    redline_suggestions: dict
    recommendations: list[dict] = Field(default_factory=list)
    audit_trail: dict


class QuickReviewResponse(BaseModel):
    """Quick review response for fast assessments."""
    
    document_id: str
    document_type: str | None = None
    page_count: int
    risk_score: int
    risk_level: RiskLevel
    risk_summary: str
    high_risk_count: int
    top_risks: list[RiskItem] = Field(default_factory=list)
    recommendation: str


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: str
    detail: str | None = None
    status_code: int
