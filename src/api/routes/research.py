"""Legal Document Assistant - Research Routes."""

from fastapi import APIRouter, HTTPException
import structlog

from src.api.schemas import (
    ResearchRequest,
    ResearchResponse,
    ErrorResponse,
)
from src.agents.research_agent import LegalResearchAgent

router = APIRouter()
logger = structlog.get_logger(__name__)

# Initialize agent
research_agent = LegalResearchAgent()


@router.post(
    "/query",
    response_model=ResearchResponse,
    responses={500: {"model": ErrorResponse}},
)
async def research_query(request: ResearchRequest):
    """
    Perform legal research based on a query.
    
    Research types:
    - general: Comprehensive search across all sources
    - case_law: Focus on case law and precedents
    - statute: Focus on statutes and regulations
    - market_standard: Verify if a clause is market standard
    
    Returns:
    - Research findings
    - Relevant cases and statutes
    - Bluebook-formatted citations
    """
    try:
        result = await research_agent.run(
            query=request.query,
            research_type=request.research_type.value,
            jurisdiction=request.jurisdiction,
        )
        
        return result
        
    except Exception as e:
        logger.error("Research query failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/case/{case_citation}",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_case(case_citation: str):
    """
    Look up a specific case by citation.
    """
    try:
        result = await research_agent.run(
            query=f"Case: {case_citation}",
            research_type="case_law",
        )
        
        if not result.get("relevant_cases"):
            raise HTTPException(status_code=404, detail="Case not found")
        
        return {
            "citation": case_citation,
            "cases": result.get("relevant_cases", []),
            "research_confidence": result.get("confidence_score"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Case lookup failed", citation=case_citation, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statute/{statute_reference}",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_statute(statute_reference: str):
    """
    Look up a specific statute or regulation.
    """
    try:
        result = await research_agent.run(
            query=f"Statute: {statute_reference}",
            research_type="statute",
        )
        
        if not result.get("relevant_statutes"):
            raise HTTPException(status_code=404, detail="Statute not found")
        
        return {
            "reference": statute_reference,
            "statutes": result.get("relevant_statutes", []),
            "research_confidence": result.get("confidence_score"),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Statute lookup failed", reference=statute_reference, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/market-standard",
    responses={500: {"model": ErrorResponse}},
)
async def check_market_standard(
    clause_text: str,
    clause_type: str,
):
    """
    Check if a clause is market standard.
    
    Returns assessment of whether the clause matches typical market practice.
    """
    try:
        result = await research_agent.verify_market_standard(
            clause_text=clause_text,
            clause_type=clause_type,
        )
        
        market_assessment = result.get("market_standard_assessment", {})
        
        return {
            "clause_type": clause_type,
            "is_market_standard": market_assessment.get("is_standard"),
            "explanation": market_assessment.get("explanation"),
            "typical_variations": market_assessment.get("typical_variations", []),
            "confidence": result.get("confidence_score"),
        }
        
    except Exception as e:
        logger.error("Market standard check failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/knowledge-base/case-law",
    responses={500: {"model": ErrorResponse}},
)
async def add_case_law(
    case_name: str,
    citation: str,
    holding: str,
    full_text: str,
):
    """
    Add case law to the knowledge base for future RAG searches.
    
    Requires:
    - case_name: Name of the case
    - citation: Legal citation (Bluebook format preferred)
    - holding: Key holding of the case
    - full_text: Full text of the case or relevant excerpts
    """
    try:
        success = await research_agent.add_case_law(
            case_name=case_name,
            citation=citation,
            holding=holding,
            full_text=full_text,
        )
        
        if success:
            return {
                "status": "added",
                "case_name": case_name,
                "citation": citation,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to add case law to knowledge base",
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Add case law failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/knowledge-base/clause",
    responses={500: {"model": ErrorResponse}},
)
async def add_approved_clause(
    clause_type: str,
    clause_text: str,
    notes: str | None = None,
):
    """
    Add an approved clause to the clause library.
    
    Pre-approved clauses are used by the Redlining Agent to suggest
    standardized language.
    """
    try:
        success = await research_agent.add_approved_clause(
            clause_type=clause_type,
            clause_text=clause_text,
            notes=notes,
        )
        
        if success:
            return {
                "status": "added",
                "clause_type": clause_type,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to add clause to library",
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Add clause failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
