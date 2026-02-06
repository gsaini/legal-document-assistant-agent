"""Legal Document Assistant - Compliance Routes."""

from fastapi import APIRouter, HTTPException
import structlog

from src.api.schemas import (
    ComplianceCheckRequest,
    ComplianceResponse,
    ErrorResponse,
)
from src.agents.compliance_agent import ComplianceAgent

# Import document store from documents route
from src.api.routes.documents import document_store

router = APIRouter()
logger = structlog.get_logger(__name__)

# Initialize agent
compliance_agent = ComplianceAgent()

# Store compliance results
compliance_store: dict = {}


@router.post(
    "/check",
    response_model=ComplianceResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def check_compliance(request: ComplianceCheckRequest):
    """
    Perform comprehensive compliance assessment on a document.
    
    Automatically detects applicable frameworks or checks specific ones:
    - GDPR (EU data protection)
    - CCPA (California privacy)
    - HIPAA (US healthcare)
    - SOC2 (service organization controls)
    - PCI-DSS (payment card security)
    - SOX (US financial reporting)
    - FERPA (US education privacy)
    - GLBA (US financial privacy)
    
    Returns:
    - Overall compliance score
    - Framework-specific results
    - Identified gaps and required actions
    - Regulatory clause mapping
    """
    document_id = request.document_id
    
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    try:
        result = await compliance_agent.run(
            document=doc_info,
            frameworks=request.frameworks,
            industry=request.industry,
            jurisdiction=request.jurisdiction,
        )
        
        # Store result
        compliance_store[document_id] = result
        
        return result
        
    except Exception as e:
        logger.error("Compliance check failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/gaps/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_compliance_gaps(document_id: str):
    """
    Get all identified compliance gaps for a document.
    """
    if document_id not in compliance_store:
        raise HTTPException(
            status_code=404,
            detail="Compliance assessment not found. Run compliance check first.",
        )
    
    compliance = compliance_store[document_id]
    gaps = compliance.get("gaps_identified", [])
    
    return {
        "document_id": document_id,
        "gaps": gaps,
        "gap_count": len(gaps),
        "by_severity": {
            "critical": [g for g in gaps if g.get("severity") == "critical"],
            "high": [g for g in gaps if g.get("severity") == "high"],
            "medium": [g for g in gaps if g.get("severity") == "medium"],
            "low": [g for g in gaps if g.get("severity") == "low"],
        },
        "by_framework": _group_by_framework(gaps),
    }


@router.get(
    "/mapping/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_regulatory_mapping(document_id: str):
    """
    Get regulatory clause mapping for a document.
    
    Shows which clauses map to which regulatory requirements.
    """
    if document_id not in compliance_store:
        raise HTTPException(
            status_code=404,
            detail="Compliance assessment not found. Run compliance check first.",
        )
    
    compliance = compliance_store[document_id]
    
    return {
        "document_id": document_id,
        "regulatory_mapping": compliance.get("regulatory_mapping", []),
        "frameworks_checked": compliance.get("frameworks_checked", []),
    }


@router.get(
    "/frameworks/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_framework_results(document_id: str):
    """
    Get detailed results for each compliance framework checked.
    """
    if document_id not in compliance_store:
        raise HTTPException(
            status_code=404,
            detail="Compliance assessment not found. Run compliance check first.",
        )
    
    compliance = compliance_store[document_id]
    
    return {
        "document_id": document_id,
        "overall_score": compliance.get("overall_compliance_score"),
        "overall_level": compliance.get("compliance_level"),
        "framework_results": compliance.get("framework_results", {}),
    }


@router.post(
    "/check-regulation",
    responses={500: {"model": ErrorResponse}},
)
async def check_specific_regulation(
    document_id: str,
    regulation: str,
    article_or_section: str,
):
    """
    Check compliance against a specific regulation article/section.
    
    Example:
    - regulation: "GDPR"
    - article_or_section: "Article 17 - Right to erasure"
    """
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    try:
        result = await compliance_agent.check_specific_regulation(
            text=doc_info.get("text_content", ""),
            regulation=regulation,
            article_or_section=article_or_section,
        )
        
        return {
            "document_id": document_id,
            **result,
        }
        
    except Exception as e:
        logger.error("Specific regulation check failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/recommendations/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_compliance_recommendations(document_id: str):
    """
    Get prioritized compliance recommendations for a document.
    """
    if document_id not in compliance_store:
        raise HTTPException(
            status_code=404,
            detail="Compliance assessment not found. Run compliance check first.",
        )
    
    compliance = compliance_store[document_id]
    recommendations = compliance.get("recommendations", [])
    
    return {
        "document_id": document_id,
        "recommendations": recommendations,
        "required_actions": [
            r for r in recommendations
            if r.get("priority") in ["critical", "high"]
        ],
    }


@router.get("/frameworks")
async def list_supported_frameworks():
    """
    List all supported compliance frameworks.
    """
    return {
        "frameworks": [
            {
                "code": "gdpr",
                "name": "General Data Protection Regulation",
                "jurisdiction": "European Union",
                "description": "EU data protection and privacy regulation",
            },
            {
                "code": "ccpa",
                "name": "California Consumer Privacy Act",
                "jurisdiction": "California, USA",
                "description": "California consumer privacy rights",
            },
            {
                "code": "hipaa",
                "name": "Health Insurance Portability and Accountability Act",
                "jurisdiction": "United States",
                "description": "US healthcare data privacy and security",
            },
            {
                "code": "soc2",
                "name": "Service Organization Control 2",
                "jurisdiction": "International",
                "description": "Trust service criteria for service organizations",
            },
            {
                "code": "pci_dss",
                "name": "Payment Card Industry Data Security Standard",
                "jurisdiction": "International",
                "description": "Payment card data security requirements",
            },
            {
                "code": "sox",
                "name": "Sarbanes-Oxley Act",
                "jurisdiction": "United States",
                "description": "US public company financial reporting",
            },
            {
                "code": "ferpa",
                "name": "Family Educational Rights and Privacy Act",
                "jurisdiction": "United States",
                "description": "US student education records privacy",
            },
            {
                "code": "glba",
                "name": "Gramm-Leach-Bliley Act",
                "jurisdiction": "United States",
                "description": "US financial institution privacy requirements",
            },
        ],
    }


def _group_by_framework(gaps: list) -> dict:
    """Group gaps by framework."""
    grouped = {}
    for gap in gaps:
        framework = gap.get("framework", "other")
        if framework not in grouped:
            grouped[framework] = []
        grouped[framework].append(gap)
    return grouped
