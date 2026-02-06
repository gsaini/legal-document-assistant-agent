"""Legal Document Assistant - Legal Research Agent.

This agent performs legal research using RAG (Retrieval Augmented Generation):
- Case law lookup and citation
- Statute and regulation search
- Legal precedent research
- Citation auto-generation (Bluebook format)

Uses ChromaDB (open source) for vector storage.
"""

from typing import Any
from datetime import datetime
import json
from pathlib import Path

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.agents.base import BaseAgent
from src.config import get_settings


class LegalResearchAgent(BaseAgent):
    """
    Legal Research Agent for case law and statute research.
    
    Responsibilities:
    - Autonomous RAG across legal databases
    - Case law lookup and analysis
    - Statute and regulation verification
    - Citation auto-generation (Bluebook format)
    - Market standard verification
    """

    def __init__(self):
        super().__init__(
            name="Legal Research Agent",
            description="Legal researcher specializing in case law, statutes, and regulatory compliance"
        )
        self.settings = get_settings()
        self._init_vector_store()
        self._init_embeddings()

    def _init_embeddings(self) -> None:
        """Initialize embeddings model (open source)."""
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
            # Using open source sentence-transformers model
            self.embeddings = HuggingFaceEmbeddings(
                model_name="all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},
            )
            self.logger.info("HuggingFace embeddings initialized")
        except Exception as e:
            self.logger.warning(f"HuggingFace embeddings not available: {e}")
            self.embeddings = None

    def _init_vector_store(self) -> None:
        """Initialize ChromaDB vector store (open source)."""
        try:
            import chromadb
            from chromadb.config import Settings as ChromaSettings
            
            self.chroma_client = chromadb.Client(ChromaSettings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.settings.chroma_path),
                anonymized_telemetry=False,
            ))
            
            # Create collections for different legal content
            self.case_law_collection = self.chroma_client.get_or_create_collection(
                name=self.settings.chroma_case_law_collection,
                metadata={"description": "Case law and legal precedents"}
            )
            
            self.clauses_collection = self.chroma_client.get_or_create_collection(
                name=self.settings.chroma_clauses_collection,
                metadata={"description": "Pre-approved clause library"}
            )
            
            self.logger.info("ChromaDB initialized")
        except Exception as e:
            self.logger.error(f"ChromaDB initialization failed: {e}")
            self.chroma_client = None

    async def run(
        self,
        query: str,
        research_type: str = "general",
        jurisdiction: str | None = None,
        document_context: dict | None = None,
    ) -> dict:
        """
        Perform legal research based on query.
        
        Args:
            query: Research query or clause to verify
            research_type: Type of research (case_law, statute, market_standard, general)
            jurisdiction: Relevant jurisdiction for the research
            document_context: Context from the document being reviewed
            
        Returns:
            Research findings with citations and analysis
        """
        self.logger.info(
            "Starting legal research",
            query=query[:100],
            research_type=research_type,
            jurisdiction=jurisdiction,
        )
        
        # Perform RAG search
        rag_results = await self._perform_rag_search(query, research_type)
        
        # Analyze findings with LLM
        analysis = await self._analyze_findings(query, rag_results, jurisdiction)
        
        # Generate citations
        citations = self._generate_citations(rag_results, analysis)
        
        result = {
            "query": query,
            "research_type": research_type,
            "jurisdiction": jurisdiction,
            "researched_at": datetime.utcnow().isoformat(),
            "findings": analysis.get("findings", []),
            "relevant_cases": analysis.get("cases", []),
            "relevant_statutes": analysis.get("statutes", []),
            "market_standard_assessment": analysis.get("market_standard", {}),
            "citations": citations,
            "recommendations": analysis.get("recommendations", []),
            "confidence_score": analysis.get("confidence", 0.0),
            "sources_count": len(rag_results),
            "audit_trail": self._create_audit_entry("legal_research", {
                "query": query[:100],
                "research_type": research_type,
                "sources_found": len(rag_results),
            }),
        }
        
        self.logger.info(
            "Legal research complete",
            sources_found=len(rag_results),
            confidence=analysis.get("confidence", 0.0),
        )
        
        return result

    async def _perform_rag_search(
        self,
        query: str,
        research_type: str,
    ) -> list[dict]:
        """Perform RAG search across legal knowledge base."""
        results = []
        
        if not self.chroma_client or not self.embeddings:
            self.logger.warning("Vector store not available, using LLM knowledge only")
            return results
        
        try:
            # Get embeddings for query
            query_embedding = self.embeddings.embed_query(query)
            
            # Search case law collection
            if research_type in ["case_law", "general"]:
                case_results = self.case_law_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5,
                )
                
                for i, doc in enumerate(case_results.get("documents", [[]])[0]):
                    results.append({
                        "type": "case_law",
                        "content": doc,
                        "metadata": case_results.get("metadatas", [[]])[0][i] if case_results.get("metadatas") else {},
                        "relevance": 1.0 - (case_results.get("distances", [[]])[0][i] if case_results.get("distances") else 0),
                    })
            
            # Search clauses collection for market standard
            if research_type in ["market_standard", "general"]:
                clause_results = self.clauses_collection.query(
                    query_embeddings=[query_embedding],
                    n_results=5,
                )
                
                for i, doc in enumerate(clause_results.get("documents", [[]])[0]):
                    results.append({
                        "type": "clause_library",
                        "content": doc,
                        "metadata": clause_results.get("metadatas", [[]])[0][i] if clause_results.get("metadatas") else {},
                        "relevance": 1.0 - (clause_results.get("distances", [[]])[0][i] if clause_results.get("distances") else 0),
                    })
                    
        except Exception as e:
            self.logger.error(f"RAG search failed: {e}")
        
        return results

    async def _analyze_findings(
        self,
        query: str,
        rag_results: list[dict],
        jurisdiction: str | None,
    ) -> dict:
        """Analyze research findings with LLM."""
        # Prepare context from RAG results
        context = ""
        if rag_results:
            context = "\n\n".join([
                f"Source ({r['type']}): {r['content'][:500]}"
                for r in rag_results[:5]
            ])
        
        prompt = f"""Perform legal research analysis for the following query.

QUERY: {query}

JURISDICTION: {jurisdiction or "Not specified - provide general analysis"}

RETRIEVED SOURCES:
{context if context else "No specific sources available - use general legal knowledge"}

Provide comprehensive legal research findings:

1. FINDINGS: Key findings relevant to the query
2. CASES: Relevant case law (real or hypothetical examples based on legal principles)
3. STATUTES: Relevant statutes or regulations
4. MARKET STANDARD: Whether this is standard market practice
5. RECOMMENDATIONS: Actionable recommendations

Return as JSON:
{{
    "findings": [
        {{"finding": "description", "significance": "high/medium/low", "source": "source reference"}}
    ],
    "cases": [
        {{"name": "case name", "citation": "citation", "holding": "key holding", "relevance": "why relevant"}}
    ],
    "statutes": [
        {{"name": "statute name", "citation": "citation", "provision": "relevant provision"}}
    ],
    "market_standard": {{
        "is_standard": true/false,
        "explanation": "why or why not",
        "typical_variations": ["common alternatives"]
    }},
    "recommendations": [
        {{"action": "recommended action", "priority": "high/medium/low", "rationale": "why"}}
    ],
    "confidence": 0.0-1.0
}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            return self._parse_json_response(response.content)
            
        except Exception as e:
            self.logger.error(f"Research analysis failed: {e}")
            return {
                "findings": [],
                "cases": [],
                "statutes": [],
                "market_standard": {"is_standard": None, "explanation": "Analysis failed"},
                "recommendations": [],
                "confidence": 0.0,
            }

    def _generate_citations(
        self,
        rag_results: list[dict],
        analysis: dict,
    ) -> list[dict]:
        """Generate properly formatted legal citations (Bluebook style)."""
        citations = []
        
        # Citations from cases in analysis
        for case in analysis.get("cases", []):
            citation = case.get("citation", "")
            if citation:
                citations.append({
                    "type": "case",
                    "bluebook": citation,
                    "short_form": case.get("name", ""),
                    "pin_cite": None,
                })
        
        # Citations from statutes
        for statute in analysis.get("statutes", []):
            citation = statute.get("citation", "")
            if citation:
                citations.append({
                    "type": "statute",
                    "bluebook": citation,
                    "short_form": statute.get("name", ""),
                    "pin_cite": None,
                })
        
        return citations

    async def add_case_law(
        self,
        case_name: str,
        citation: str,
        holding: str,
        full_text: str,
        metadata: dict | None = None,
    ) -> bool:
        """Add case law to the knowledge base."""
        if not self.chroma_client or not self.embeddings:
            self.logger.error("Vector store not available")
            return False
        
        try:
            # Split text into chunks
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
            )
            chunks = splitter.split_text(full_text)
            
            # Generate embeddings and add to collection
            for i, chunk in enumerate(chunks):
                embedding = self.embeddings.embed_query(chunk)
                
                self.case_law_collection.add(
                    embeddings=[embedding],
                    documents=[chunk],
                    metadatas=[{
                        "case_name": case_name,
                        "citation": citation,
                        "holding": holding,
                        "chunk_index": i,
                        **(metadata or {}),
                    }],
                    ids=[f"{citation.replace(' ', '_')}_{i}"],
                )
            
            self.logger.info(f"Added case law: {case_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add case law: {e}")
            return False

    async def add_approved_clause(
        self,
        clause_type: str,
        clause_text: str,
        notes: str | None = None,
        metadata: dict | None = None,
    ) -> bool:
        """Add an approved clause to the clause library."""
        if not self.chroma_client or not self.embeddings:
            self.logger.error("Vector store not available")
            return False
        
        try:
            embedding = self.embeddings.embed_query(clause_text)
            
            clause_id = f"{clause_type}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            self.clauses_collection.add(
                embeddings=[embedding],
                documents=[clause_text],
                metadatas=[{
                    "clause_type": clause_type,
                    "notes": notes or "",
                    "added_at": datetime.utcnow().isoformat(),
                    **(metadata or {}),
                }],
                ids=[clause_id],
            )
            
            self.logger.info(f"Added approved clause: {clause_type}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add clause: {e}")
            return False

    async def verify_market_standard(
        self,
        clause_text: str,
        clause_type: str,
    ) -> dict:
        """Verify if a clause matches market standard practice."""
        return await self.run(
            query=f"Is this {clause_type} clause market standard: {clause_text}",
            research_type="market_standard",
        )

    def _parse_json_response(self, content: str) -> Any:
        """Parse JSON from LLM response."""
        content = content.strip()
        
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            if content.startswith("json"):
                content = content[4:].strip()
        
        return json.loads(content)
