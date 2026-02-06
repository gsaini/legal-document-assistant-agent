"""Legal Document Assistant - Analysis Routes."""

from fastapi import APIRouter, HTTPException
import structlog

from src.api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    RedlineRequest,
    RedlineResponse,
    ApplySuggestionsRequest,
    ErrorResponse,
)
from src.agents.analysis_agent import ContractAnalysisAgent
from src.agents.redlining_agent import RedliningAgent

# Import document store from documents route
from src.api.routes.documents import document_store

router = APIRouter()
logger = structlog.get_logger(__name__)

# Initialize agents
analysis_agent = ContractAnalysisAgent()
redlining_agent = RedliningAgent()

# Store analysis results
analysis_store: dict = {}


@router.post(
    "/contract",
    response_model=AnalysisResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def analyze_contract(request: AnalysisRequest):
    """
    Analyze a contract for risks, clauses, and obligations.
    
    Returns:
    - Overall risk score and level
    - High-risk items with mitigation suggestions
    - Clause classification
    - Extracted obligations and deadlines
    """
    document_id = request.document_id
    
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    try:
        result = await analysis_agent.run(
            document=doc_info,
            focus_areas=request.focus_areas,
            comparison_standard=request.comparison_standard,
        )
        
        # Store analysis result
        analysis_id = f"analysis_{document_id}"
        analysis_store[analysis_id] = result
        
        return result
        
    except Exception as e:
        logger.error("Contract analysis failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/risks/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_risk_report(document_id: str):
    """
    Get a detailed risk report for a document.
    
    Returns the risk heatmap, high-risk items, and risk score.
    """
    analysis_id = f"analysis_{document_id}"
    
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run contract analysis first.",
        )
    
    analysis = analysis_store[analysis_id]
    
    return {
        "document_id": document_id,
        "overall_risk_score": analysis.get("overall_risk_score"),
        "risk_level": analysis.get("risk_level"),
        "risk_summary": analysis.get("risk_summary"),
        "risk_heatmap": analysis.get("risk_heatmap", []),
        "high_risk_items": analysis.get("high_risk_items", []),
        "recommendations": [
            r for r in analysis.get("recommendations", [])
            if r.get("category") == "risk"
        ],
    }


@router.post(
    "/redline/suggest",
    response_model=RedlineResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def generate_redlines(request: RedlineRequest):
    """
    Generate redline suggestions for a document.
    
    Based on risk analysis, generates suggested changes with:
    - Original text and suggested replacement
    - Priority level (critical/high/medium/low)
    - Rationale for each change
    """
    document_id = request.document_id
    
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    # Get analysis if available
    analysis_id = request.analysis_id or f"analysis_{document_id}"
    analysis = analysis_store.get(analysis_id)
    
    if not analysis:
        # Run analysis first
        analysis = await analysis_agent.run(document=doc_info)
        analysis_store[analysis_id] = analysis
    
    try:
        result = await redlining_agent.run(
            document=doc_info,
            analysis=analysis,
            clause_library=request.clause_library,
            style_guide=request.style_guide,
        )
        
        return result
        
    except Exception as e:
        logger.error("Redline generation failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/redline/apply",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def apply_redlines(request: ApplySuggestionsRequest):
    """
    Apply selected redline suggestions to generate revised document.
    
    Returns the revised document text with selected suggestions applied.
    """
    document_id = request.document_id
    
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    original_text = doc_info.get("text_content", "")
    
    # Get the redline suggestions (would normally be stored)
    # For now, regenerate them
    analysis_id = f"analysis_{document_id}"
    analysis = analysis_store.get(analysis_id)
    
    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run contract analysis first.",
        )
    
    try:
        redline_result = await redlining_agent.run(
            document=doc_info,
            analysis=analysis,
        )
        
        # Apply suggestions
        revised_text = await redlining_agent.apply_suggestions(
            original_text=original_text,
            suggestions=redline_result.get("suggestions", []),
            suggestion_ids=request.suggestion_ids,
        )
        
        return {
            "document_id": document_id,
            "original_length": len(original_text),
            "revised_length": len(revised_text),
            "suggestions_applied": len(request.suggestion_ids),
            "revised_text": revised_text,
        }
        
    except Exception as e:
        logger.error("Apply redlines failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/clauses/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_clauses(document_id: str):
    """
    Get all identified clauses from a document.
    """
    analysis_id = f"analysis_{document_id}"
    
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run contract analysis first.",
        )
    
    analysis = analysis_store[analysis_id]
    
    return {
        "document_id": document_id,
        "clauses": analysis.get("clauses", []),
        "clause_count": len(analysis.get("clauses", [])),
    }


@router.get(
    "/obligations/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_obligations(document_id: str):
    """
    Get all extracted obligations from a document.
    """
    analysis_id = f"analysis_{document_id}"
    
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run contract analysis first.",
        )
    
    analysis = analysis_store[analysis_id]
    
    obligations = analysis.get("obligations", [])
    
    return {
        "document_id": document_id,
        "obligations": obligations,
        "obligation_count": len(obligations),
        "by_priority": {
            "critical": [o for o in obligations if o.get("priority") == "critical"],
            "important": [o for o in obligations if o.get("priority") == "important"],
            "standard": [o for o in obligations if o.get("priority") == "standard"],
        },
    }


@router.get(
    "/entities/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_entities(document_id: str):
    """
    Get all extracted entities from a document.
    """
    analysis_id = f"analysis_{document_id}"
    
    if analysis_id not in analysis_store:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found. Run contract analysis first.",
        )
    
    analysis = analysis_store[analysis_id]
    
    return {
        "document_id": document_id,
        "entities": analysis.get("entities", {}),
    }
