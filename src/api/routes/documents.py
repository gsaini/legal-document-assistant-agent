"""Legal Document Assistant - Document Routes."""

from pathlib import Path
from typing import Optional
import uuid
import shutil

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog

from src.config import get_settings
from src.api.schemas import (
    DocumentUploadConfig,
    DocumentUploadResponse,
    FullReviewResponse,
    QuickReviewResponse,
    ErrorResponse,
)
from src.agents.orchestrator import LegalDocumentOrchestrator
from src.agents.intake_agent import IntakeAgent

router = APIRouter()
logger = structlog.get_logger(__name__)
settings = get_settings()

# Initialize agents
orchestrator = LegalDocumentOrchestrator()
intake_agent = IntakeAgent()

# In-memory document store (replace with database in production)
document_store: dict = {}


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_document(
    file: UploadFile = File(...),
    config: DocumentUploadConfig | None = None,
):
    """
    Upload a legal document for processing.
    
    Supports PDF, DOCX, DOC, TXT, and image files (PNG, JPG, JPEG).
    The document will be processed through OCR if needed and PII detection
    will be performed.
    """
    # Validate file type
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in settings.supported_formats_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {file_ext}. Supported: {settings.supported_formats}",
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start
    
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )
    
    # Save file
    document_id = str(uuid.uuid4())[:8]
    file_path = settings.upload_path / f"{document_id}_{file.filename}"
    
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        logger.info("Document uploaded", document_id=document_id, filename=file.filename)
        
        # Process document
        config_dict = config.model_dump() if config else {}
        
        result = await intake_agent.run(
            file_path=file_path,
            detect_pii=config_dict.get("detect_pii", True),
            redact_pii=config_dict.get("redact_pii", False),
        )
        
        # Store document info
        document_store[result["document_id"]] = {
            **result,
            "file_path": str(file_path),
            "config": config_dict,
        }
        
        return DocumentUploadResponse(
            document_id=result["document_id"],
            file_name=result["file_name"],
            file_type=result["file_type"],
            file_size_bytes=result["file_size_bytes"],
            processed_at=result["processed_at"],
            page_count=result["page_count"],
            word_count=result["word_count"],
            metadata=result["metadata"],
            pii_findings_count=len(result.get("pii_findings") or []),
            pii_redacted=result.get("pii_redacted", False),
        )
        
    except Exception as e:
        logger.error("Document upload failed", error=str(e))
        # Clean up file on error
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{document_id}/full-review",
    response_model=FullReviewResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def full_review(
    document_id: str,
    background_tasks: BackgroundTasks,
):
    """
    Perform a full legal review of the uploaded document.
    
    This runs the complete multi-agent workflow:
    - Document Analysis (risk scoring, clause identification)
    - Legal Research (case law, statutes)
    - Compliance Check (GDPR, CCPA, etc.)
    - Redline Generation (suggested changes)
    """
    # Check if document exists
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    try:
        result = await orchestrator.run(
            file_path=doc_info["file_path"],
            config=doc_info.get("config", {}),
        )
        
        return result
        
    except Exception as e:
        logger.error("Full review failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/{document_id}/quick-review",
    response_model=QuickReviewResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def quick_review(document_id: str):
    """
    Perform a quick review of the uploaded document.
    
    This provides a fast initial assessment with:
    - Risk score and level
    - Top risk items
    - Recommendation for further review
    """
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    try:
        result = await orchestrator.quick_review(
            file_path=doc_info["file_path"],
        )
        
        return result
        
    except Exception as e:
        logger.error("Quick review failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def get_document(document_id: str):
    """
    Get document information and processing status.
    """
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    # Return info without sensitive data
    return {
        "document_id": document_id,
        "file_name": doc_info.get("file_name"),
        "file_type": doc_info.get("file_type"),
        "page_count": doc_info.get("page_count"),
        "word_count": doc_info.get("word_count"),
        "processed_at": doc_info.get("processed_at"),
        "metadata": doc_info.get("metadata"),
        "status": "processed",
    }


@router.delete(
    "/{document_id}",
    responses={404: {"model": ErrorResponse}},
)
async def delete_document(document_id: str):
    """
    Delete an uploaded document and its data.
    """
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    
    doc_info = document_store[document_id]
    
    # Delete file
    file_path = Path(doc_info.get("file_path", ""))
    if file_path.exists():
        file_path.unlink()
    
    # Remove from store
    del document_store[document_id]
    
    logger.info("Document deleted", document_id=document_id)
    
    return {"status": "deleted", "document_id": document_id}


@router.get("/")
async def list_documents():
    """
    List all uploaded documents.
    """
    return {
        "count": len(document_store),
        "documents": [
            {
                "document_id": doc_id,
                "file_name": info.get("file_name"),
                "file_type": info.get("file_type"),
                "processed_at": info.get("processed_at"),
            }
            for doc_id, info in document_store.items()
        ],
    }
