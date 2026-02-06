"""Legal Document Assistant - Contract Analysis Agent.

This agent performs comprehensive contract analysis including:
- Risk assessment and scoring
- Clause identification and classification
- Entity extraction (parties, dates, amounts)
- Obligation and deadline extraction
- Deviation detection from standard terms
"""

from typing import Any
from datetime import datetime
import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser

from src.agents.base import BaseAgent


class ContractAnalysisAgent(BaseAgent):
    """
    Contract Analysis Agent for legal document review.
    
    Responsibilities:
    - Risk heatmap generation (colors code sections by favorability)
    - Entity linking (connecting references across document)
    - Obligation extraction (deadlines, financial commitments)
    - Clause classification and risk scoring
    - Deviation detection from standard terms
    """

    # Standard clause categories for legal documents
    CLAUSE_CATEGORIES = [
        "indemnification",
        "limitation_of_liability",
        "termination",
        "confidentiality",
        "intellectual_property",
        "dispute_resolution",
        "governing_law",
        "force_majeure",
        "assignment",
        "warranties",
        "payment_terms",
        "auto_renewal",
        "non_compete",
        "data_protection",
        "insurance",
    ]

    # Risk indicators for automatic flagging
    RISK_INDICATORS = [
        "unlimited liability",
        "sole discretion",
        "without cause",
        "automatic renewal",
        "perpetual license",
        "exclusive rights",
        "irrevocable",
        "waive",
        "indemnify and hold harmless",
        "consequential damages",
        "punitive damages",
        "liquidated damages",
        "non-compete",
        "no warranty",
        "as is",
    ]

    def __init__(self):
        super().__init__(
            name="Contract Analysis Agent",
            description="Legal expert specializing in contract risk analysis, clause identification, and obligation extraction"
        )

    async def run(
        self,
        document: dict,
        focus_areas: list[str] | None = None,
        comparison_standard: str | None = None,
    ) -> dict:
        """
        Analyze a legal document for risks and obligations.
        
        Args:
            document: Processed document from IntakeAgent
            focus_areas: Specific areas to focus analysis on
            comparison_standard: Standard template to compare against
            
        Returns:
            Comprehensive analysis with risks, obligations, and recommendations
        """
        text = document.get("text_content", "")
        
        if not text:
            raise ValueError("Document has no text content to analyze")
        
        self.logger.info(
            "Starting contract analysis",
            document_id=document.get("document_id"),
            word_count=document.get("word_count"),
        )
        
        # Perform parallel analysis tasks
        risk_analysis = await self._analyze_risks(text)
        clause_analysis = await self._classify_clauses(text)
        entity_extraction = await self._extract_entities(text)
        obligation_analysis = await self._extract_obligations(text)
        
        # Compute overall risk score
        overall_risk = self._compute_risk_score(risk_analysis, clause_analysis)
        
        # Check for deviations if standard provided
        deviations = []
        if comparison_standard:
            deviations = await self._detect_deviations(text, comparison_standard)
        
        result = {
            "document_id": document.get("document_id"),
            "analyzed_at": datetime.utcnow().isoformat(),
            "overall_risk_score": overall_risk["score"],
            "risk_level": overall_risk["level"],
            "risk_summary": overall_risk["summary"],
            "risk_heatmap": risk_analysis.get("heatmap", []),
            "high_risk_items": risk_analysis.get("high_risk_items", []),
            "clauses": clause_analysis,
            "entities": entity_extraction,
            "obligations": obligation_analysis,
            "deviations": deviations,
            "recommendations": await self._generate_recommendations(
                risk_analysis, clause_analysis, obligation_analysis
            ),
            "audit_trail": self._create_audit_entry("contract_analysis", {
                "document_id": document.get("document_id"),
                "risk_score": overall_risk["score"],
            }),
        }
        
        self.logger.info(
            "Contract analysis complete",
            document_id=document.get("document_id"),
            risk_level=overall_risk["level"],
            clauses_found=len(clause_analysis),
            obligations_found=len(obligation_analysis),
        )
        
        return result

    async def _analyze_risks(self, text: str) -> dict:
        """Analyze document for legal risks."""
        prompt = f"""Analyze this legal document for risks and unfavorable terms.

Document:
{text[:6000]}  # First 6000 chars for context

Identify:
1. High-risk clauses that are unfavorable to the party receiving the contract
2. Ambiguous language that could be exploited
3. Missing standard protections
4. Unusual or non-standard terms

For each risk found, provide:
- Location (approximate position in document)
- Risk category (liability, termination, indemnification, etc.)
- Severity (high/medium/low)
- Specific concern
- Suggested mitigation

Return as JSON:
{{
    "heatmap": [
        {{
            "section": "section name or description",
            "risk_level": "high/medium/low",
            "color": "red/yellow/green"
        }}
    ],
    "high_risk_items": [
        {{
            "clause_text": "the problematic text",
            "category": "risk category",
            "severity": "high/medium/low",
            "concern": "why this is concerning",
            "mitigation": "suggested fix"
        }}
    ],
    "missing_protections": ["list of standard protections not found"],
    "ambiguous_terms": ["list of ambiguous language found"]
}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            content = self._parse_json_response(response.content)
            return content
            
        except Exception as e:
            self.logger.error(f"Risk analysis failed: {e}")
            return {
                "heatmap": [],
                "high_risk_items": [],
                "missing_protections": [],
                "ambiguous_terms": [],
            }

    async def _classify_clauses(self, text: str) -> list[dict]:
        """Classify and extract all significant clauses."""
        prompt = f"""Extract and classify all significant clauses from this legal document.

Document:
{text[:6000]}

For each clause, identify:
1. Clause type (from: {', '.join(self.CLAUSE_CATEGORIES)})
2. The actual clause text (summarized if very long)
3. Key terms and conditions
4. Favorability assessment (favorable/neutral/unfavorable)
5. Page/section location if identifiable

Return as JSON array:
[
    {{
        "clause_type": "type from list above",
        "summary": "brief summary of the clause",
        "full_text": "the clause text",
        "key_terms": ["important terms"],
        "favorability": "favorable/neutral/unfavorable",
        "location": "section or page reference",
        "notes": "any important observations"
    }}
]"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            clauses = self._parse_json_response(response.content)
            return clauses if isinstance(clauses, list) else []
            
        except Exception as e:
            self.logger.error(f"Clause classification failed: {e}")
            return []

    async def _extract_entities(self, text: str) -> dict:
        """Extract key entities from the document."""
        prompt = f"""Extract all key entities from this legal document.

Document:
{text[:4000]}

Extract:
1. All parties (with their roles - e.g., "Buyer", "Seller", "Licensor")
2. All dates mentioned (with context - e.g., "Effective Date", "Termination Date")
3. All monetary amounts (with context)
4. All jurisdictions/governing laws
5. All addresses/locations
6. All key defined terms

Return as JSON:
{{
    "parties": [
        {{"name": "party name", "role": "their role", "aliases": ["other names used"]}}
    ],
    "dates": [
        {{"date": "the date", "context": "what this date represents"}}
    ],
    "monetary_amounts": [
        {{"amount": "the amount", "currency": "USD/EUR/etc", "context": "what this is for"}}
    ],
    "jurisdictions": ["list of jurisdictions mentioned"],
    "locations": ["list of addresses/locations"],
    "defined_terms": [
        {{"term": "the defined term", "definition": "its definition"}}
    ]
}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            return self._parse_json_response(response.content)
            
        except Exception as e:
            self.logger.error(f"Entity extraction failed: {e}")
            return {
                "parties": [],
                "dates": [],
                "monetary_amounts": [],
                "jurisdictions": [],
                "locations": [],
                "defined_terms": [],
            }

    async def _extract_obligations(self, text: str) -> list[dict]:
        """Extract all obligations, deadlines, and commitments."""
        prompt = f"""Extract all obligations, deadlines, and commitments from this legal document.

Document:
{text[:5000]}

For each obligation, identify:
1. The obligated party
2. What they must do
3. When/deadline (if specified)
4. Consequences of non-compliance
5. Whether it's a one-time or recurring obligation

Return as JSON array:
[
    {{
        "obligated_party": "who must perform",
        "obligation": "what they must do",
        "deadline": "when (if specified)",
        "recurrence": "one-time/recurring/ongoing",
        "consequences": "what happens if not performed",
        "priority": "critical/important/standard",
        "location": "where in document"
    }}
]"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            obligations = self._parse_json_response(response.content)
            return obligations if isinstance(obligations, list) else []
            
        except Exception as e:
            self.logger.error(f"Obligation extraction failed: {e}")
            return []

    async def _detect_deviations(self, text: str, standard: str) -> list[dict]:
        """Detect deviations from standard/template language."""
        prompt = f"""Compare this contract against the standard template and identify deviations.

CONTRACT TEXT:
{text[:3000]}

STANDARD TEMPLATE:
{standard[:3000]}

For each deviation, identify:
1. The standard clause
2. The actual clause in the contract
3. The nature of the deviation
4. Risk assessment of the deviation
5. Recommendation

Return as JSON array:
[
    {{
        "standard_clause": "what the standard says",
        "actual_clause": "what the contract says",
        "deviation_type": "missing/modified/additional",
        "risk_level": "high/medium/low",
        "recommendation": "suggested action"
    }}
]"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            deviations = self._parse_json_response(response.content)
            return deviations if isinstance(deviations, list) else []
            
        except Exception as e:
            self.logger.error(f"Deviation detection failed: {e}")
            return []

    def _compute_risk_score(self, risk_analysis: dict, clause_analysis: list) -> dict:
        """Compute overall risk score from analysis results."""
        # Start with base score
        score = 50
        
        # Adjust based on high-risk items
        high_risk_count = len([
            item for item in risk_analysis.get("high_risk_items", [])
            if item.get("severity") == "high"
        ])
        medium_risk_count = len([
            item for item in risk_analysis.get("high_risk_items", [])
            if item.get("severity") == "medium"
        ])
        
        score += high_risk_count * 15
        score += medium_risk_count * 7
        
        # Adjust for missing protections
        score += len(risk_analysis.get("missing_protections", [])) * 5
        
        # Adjust for unfavorable clauses
        unfavorable_count = len([
            c for c in clause_analysis
            if c.get("favorability") == "unfavorable"
        ])
        score += unfavorable_count * 8
        
        # Cap at 100
        score = min(100, score)
        
        # Determine level
        if score >= 70:
            level = "high"
            summary = "This contract contains significant risks requiring careful review"
        elif score >= 40:
            level = "medium"
            summary = "This contract has some areas of concern that should be addressed"
        else:
            level = "low"
            summary = "This contract appears relatively balanced with standard terms"
        
        return {
            "score": score,
            "level": level,
            "summary": summary,
        }

    async def _generate_recommendations(
        self,
        risk_analysis: dict,
        clause_analysis: list,
        obligation_analysis: list,
    ) -> list[dict]:
        """Generate actionable recommendations based on analysis."""
        recommendations = []
        
        # Add recommendations for high-risk items
        for item in risk_analysis.get("high_risk_items", []):
            if item.get("severity") == "high":
                recommendations.append({
                    "priority": "high",
                    "category": item.get("category", "risk"),
                    "issue": item.get("concern", "Risk identified"),
                    "recommendation": item.get("mitigation", "Review with legal counsel"),
                    "action_required": True,
                })
        
        # Add recommendations for unfavorable clauses
        for clause in clause_analysis:
            if clause.get("favorability") == "unfavorable":
                recommendations.append({
                    "priority": "medium",
                    "category": clause.get("clause_type", "clause"),
                    "issue": f"Unfavorable {clause.get('clause_type', 'clause')} terms",
                    "recommendation": f"Negotiate modification to {clause.get('clause_type', 'this clause')}",
                    "action_required": True,
                })
        
        # Add recommendations for critical obligations
        for obligation in obligation_analysis:
            if obligation.get("priority") == "critical":
                recommendations.append({
                    "priority": "high",
                    "category": "obligation",
                    "issue": f"Critical obligation: {obligation.get('obligation', '')}",
                    "recommendation": "Ensure systems in place to meet this obligation",
                    "action_required": True,
                })
        
        return recommendations

    def _parse_json_response(self, content: str) -> Any:
        """Parse JSON from LLM response, handling markdown code blocks."""
        content = content.strip()
        
        # Handle markdown code blocks
        if content.startswith("```"):
            lines = content.split("\n")
            # Remove first and last lines (``` markers)
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            if content.startswith("json"):
                content = content[4:].strip()
        
        return json.loads(content)
