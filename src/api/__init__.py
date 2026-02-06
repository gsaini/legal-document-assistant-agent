"""Legal Document Assistant - API Package."""

from fastapi import APIRouter

from src.api.routes import documents, analysis, research, compliance

router = APIRouter()

# Include all route modules
router.include_router(documents.router, prefix="/documents", tags=["Documents"])
router.include_router(analysis.router, prefix="/analysis", tags=["Analysis"])
router.include_router(research.router, prefix="/research", tags=["Research"])
router.include_router(compliance.router, prefix="/compliance", tags=["Compliance"])

__all__ = ["router"]
