"""Legal Document Assistant - Intake & OCR Agent.

This agent handles document ingestion, OCR for scanned documents,
and structural parsing using open source tools:
- Tesseract OCR (open source)
- PyMuPDF / pdfplumber (open source)
- Unstructured.io (open source)
- Presidio (open source PII detection)
"""

from typing import Any
from pathlib import Path
from datetime import datetime
import hashlib
import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import BaseAgent
from src.config import get_settings


class IntakeAgent(BaseAgent):
    """
    Intake & OCR Agent for document ingestion and preprocessing.
    
    Responsibilities:
    - Document upload and validation
    - OCR for scanned PDFs and images (using Tesseract)
    - Structural parsing (sections, paragraphs, tables)
    - PII detection and optional redaction (using Presidio)
    - Document fingerprinting for deduplication
    """

    def __init__(self):
        super().__init__(
            name="Intake & OCR Agent",
            description="Document ingestion specialist handling OCR, parsing, and PII detection"
        )
        self.settings = get_settings()
        self._init_ocr()
        self._init_pii_detector()

    def _init_ocr(self) -> None:
        """Initialize Tesseract OCR (open source)."""
        try:
            import pytesseract
            pytesseract.pytesseract.tesseract_cmd = self.settings.tesseract_cmd
            self.ocr_available = True
            self.logger.info("Tesseract OCR initialized")
        except Exception as e:
            self.ocr_available = False
            self.logger.warning(f"Tesseract OCR not available: {e}")

    def _init_pii_detector(self) -> None:
        """Initialize Presidio for PII detection (open source)."""
        if not self.settings.pii_detection_enabled:
            self.pii_detector = None
            return
            
        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_anonymizer import AnonymizerEngine
            
            self.pii_analyzer = AnalyzerEngine()
            self.pii_anonymizer = AnonymizerEngine()
            self.logger.info("Presidio PII detector initialized")
        except Exception as e:
            self.pii_analyzer = None
            self.pii_anonymizer = None
            self.logger.warning(f"Presidio PII detector not available: {e}")

    async def run(
        self,
        file_path: str | Path,
        detect_pii: bool = True,
        redact_pii: bool = False,
    ) -> dict:
        """
        Process an uploaded document.
        
        Args:
            file_path: Path to the uploaded document
            detect_pii: Whether to detect PII in the document
            redact_pii: Whether to redact detected PII
            
        Returns:
            Structured document data with sections, entities, and metadata
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Validate file type
        extension = file_path.suffix.lower().lstrip(".")
        if extension not in self.settings.supported_formats_list:
            raise ValueError(f"Unsupported file format: {extension}")
        
        self.logger.info("Processing document", file=str(file_path))
        
        # Generate document fingerprint
        doc_hash = self._compute_hash(file_path)
        
        # Extract text based on file type
        if extension in ["pdf"]:
            text, structure = await self._process_pdf(file_path)
        elif extension in ["docx", "doc"]:
            text, structure = await self._process_docx(file_path)
        elif extension in ["png", "jpg", "jpeg"]:
            text, structure = await self._process_image(file_path)
        elif extension in ["txt"]:
            text, structure = await self._process_text(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")
        
        # Detect PII if enabled
        pii_findings = []
        if detect_pii and self.pii_analyzer:
            pii_findings = self._detect_pii(text)
            
            if redact_pii and pii_findings:
                text = self._redact_pii(text)
        
        # Use LLM to extract document metadata
        metadata = await self._extract_metadata(text, structure)
        
        result = {
            "document_id": doc_hash[:16],
            "file_name": file_path.name,
            "file_type": extension,
            "file_size_bytes": file_path.stat().st_size,
            "hash": doc_hash,
            "processed_at": datetime.utcnow().isoformat(),
            "text_content": text,
            "structure": structure,
            "metadata": metadata,
            "pii_findings": pii_findings if detect_pii else None,
            "pii_redacted": redact_pii,
            "word_count": len(text.split()),
            "page_count": structure.get("page_count", 1),
        }
        
        self.logger.info(
            "Document processed",
            document_id=result["document_id"],
            pages=result["page_count"],
            words=result["word_count"],
            pii_count=len(pii_findings),
        )
        
        return result

    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash for document fingerprinting."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def _process_pdf(self, file_path: Path) -> tuple[str, dict]:
        """
        Process PDF using open source libraries.
        
        Uses pdfplumber for text extraction and falls back to Tesseract OCR
        for scanned documents.
        """
        try:
            import pdfplumber
            
            text_parts = []
            pages = []
            
            with pdfplumber.open(file_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    
                    # If no text extracted, might be scanned - try OCR
                    if not page_text.strip() and self.ocr_available:
                        page_text = await self._ocr_page(page, i)
                    
                    text_parts.append(page_text)
                    
                    # Extract tables if present
                    tables = page.extract_tables()
                    
                    pages.append({
                        "page_number": i + 1,
                        "text": page_text,
                        "tables": tables,
                        "has_content": bool(page_text.strip()),
                    })
            
            structure = {
                "page_count": len(pages),
                "pages": pages,
                "has_tables": any(p["tables"] for p in pages),
            }
            
            return "\n\n".join(text_parts), structure
            
        except Exception as e:
            self.logger.error(f"PDF processing error: {e}")
            raise

    async def _ocr_page(self, page, page_num: int) -> str:
        """Perform OCR on a PDF page using Tesseract (open source)."""
        try:
            import pytesseract
            from PIL import Image
            import io
            
            # Convert PDF page to image
            img = page.to_image(resolution=300)
            
            # Perform OCR
            text = pytesseract.image_to_string(
                img.original,
                lang=self.settings.ocr_languages,
            )
            
            self.logger.debug(f"OCR performed on page {page_num + 1}")
            return text
            
        except Exception as e:
            self.logger.warning(f"OCR failed for page {page_num + 1}: {e}")
            return ""

    async def _process_docx(self, file_path: Path) -> tuple[str, dict]:
        """Process DOCX using python-docx (open source)."""
        try:
            from docx import Document
            
            doc = Document(file_path)
            
            paragraphs = []
            for para in doc.paragraphs:
                paragraphs.append({
                    "text": para.text,
                    "style": para.style.name if para.style else None,
                })
            
            # Extract tables
            tables = []
            for table in doc.tables:
                table_data = []
                for row in table.rows:
                    row_data = [cell.text for cell in row.cells]
                    table_data.append(row_data)
                tables.append(table_data)
            
            text = "\n".join(p["text"] for p in paragraphs)
            
            structure = {
                "page_count": 1,  # DOCX doesn't have native page info
                "paragraphs": paragraphs,
                "tables": tables,
                "has_tables": bool(tables),
            }
            
            return text, structure
            
        except Exception as e:
            self.logger.error(f"DOCX processing error: {e}")
            raise

    async def _process_image(self, file_path: Path) -> tuple[str, dict]:
        """Process image files using Tesseract OCR (open source)."""
        if not self.ocr_available:
            raise RuntimeError("Tesseract OCR not available for image processing")
        
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(file_path)
            text = pytesseract.image_to_string(
                img,
                lang=self.settings.ocr_languages,
            )
            
            structure = {
                "page_count": 1,
                "image_size": img.size,
                "image_mode": img.mode,
            }
            
            return text, structure
            
        except Exception as e:
            self.logger.error(f"Image processing error: {e}")
            raise

    async def _process_text(self, file_path: Path) -> tuple[str, dict]:
        """Process plain text files."""
        text = file_path.read_text(encoding="utf-8")
        
        lines = text.split("\n")
        structure = {
            "page_count": 1,
            "line_count": len(lines),
        }
        
        return text, structure

    def _detect_pii(self, text: str) -> list[dict]:
        """
        Detect PII using Presidio (open source).
        
        Detects: Names, emails, phone numbers, SSNs, credit cards, etc.
        """
        if not self.pii_analyzer:
            return []
        
        results = self.pii_analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "US_SSN",
                "CREDIT_CARD",
                "US_DRIVER_LICENSE",
                "US_PASSPORT",
                "LOCATION",
                "DATE_TIME",
            ],
        )
        
        return [
            {
                "entity_type": r.entity_type,
                "start": r.start,
                "end": r.end,
                "score": r.score,
                "text_snippet": text[max(0, r.start-10):min(len(text), r.end+10)],
            }
            for r in results
            if r.score >= 0.7  # Only high-confidence findings
        ]

    def _redact_pii(self, text: str) -> str:
        """Redact PII from text using Presidio (open source)."""
        if not self.pii_anonymizer or not self.pii_analyzer:
            return text
        
        results = self.pii_analyzer.analyze(text=text, language="en")
        anonymized = self.pii_anonymizer.anonymize(text=text, analyzer_results=results)
        
        return anonymized.text

    async def _extract_metadata(self, text: str, structure: dict) -> dict:
        """Use LLM to extract document metadata."""
        # Take first 2000 chars for metadata extraction
        sample_text = text[:2000] if len(text) > 2000 else text
        
        prompt = f"""Analyze this legal document excerpt and extract metadata.

Document excerpt:
{sample_text}

Extract and return as JSON:
{{
    "document_type": "contract type (e.g., NDA, MSA, Employment Agreement)",
    "parties": ["list of parties mentioned"],
    "effective_date": "if mentioned",
    "governing_law": "jurisdiction if mentioned",
    "key_terms": ["list of key legal terms found"],
    "estimated_risk_level": "low/medium/high based on complexity"
}}

Return only valid JSON, no other text."""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            # Parse JSON response
            content = response.content.strip()
            # Handle markdown code blocks
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            return json.loads(content)
            
        except Exception as e:
            self.logger.warning(f"Metadata extraction failed: {e}")
            return {
                "document_type": "unknown",
                "parties": [],
                "effective_date": None,
                "governing_law": None,
                "key_terms": [],
                "estimated_risk_level": "unknown",
            }
