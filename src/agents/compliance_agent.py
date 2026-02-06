"""Legal Document Assistant - Compliance Agent.

This agent handles regulatory compliance checking:
- GDPR / CCPA data protection compliance
- SOC2 alignment verification
- Industry-specific regulatory benchmarks
- Regulatory mapping (clause to regulation)
"""

from typing import Any
from datetime import datetime
import json

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import BaseAgent
from src.config import get_settings


class ComplianceAgent(BaseAgent):
    """
    Compliance Agent for regulatory alignment verification.
    
    Responsibilities:
    - GDPR compliance checking
    - CCPA compliance verification
    - SOC2 alignment assessment
    - Regulatory mapping (clauses to regulations)
    - Industry-specific compliance checks
    """

    # Regulatory frameworks supported
    SUPPORTED_FRAMEWORKS = [
        "gdpr",      # EU General Data Protection Regulation
        "ccpa",      # California Consumer Privacy Act
        "hipaa",     # Health Insurance Portability and Accountability Act
        "soc2",      # Service Organization Control 2
        "pci_dss",   # Payment Card Industry Data Security Standard
        "sox",       # Sarbanes-Oxley Act
        "ferpa",     # Family Educational Rights and Privacy Act
        "glba",      # Gramm-Leach-Bliley Act
    ]

    # Key compliance areas to check
    COMPLIANCE_AREAS = {
        "gdpr": [
            "lawful_basis_processing",
            "data_subject_rights",
            "data_protection_officer",
            "privacy_by_design",
            "data_breach_notification",
            "cross_border_transfer",
            "consent_requirements",
            "data_retention",
        ],
        "ccpa": [
            "right_to_know",
            "right_to_delete",
            "right_to_opt_out",
            "non_discrimination",
            "privacy_notice",
            "service_provider_requirements",
        ],
        "hipaa": [
            "protected_health_information",
            "minimum_necessary_standard",
            "business_associate_agreement",
            "security_safeguards",
            "breach_notification",
        ],
        "soc2": [
            "security",
            "availability",
            "processing_integrity",
            "confidentiality",
            "privacy",
        ],
    }

    def __init__(self):
        super().__init__(
            name="Compliance Agent",
            description="Regulatory compliance specialist verifying alignment with GDPR, CCPA, SOC2, and other frameworks"
        )
        self.settings = get_settings()

    async def run(
        self,
        document: dict,
        frameworks: list[str] | None = None,
        industry: str | None = None,
        jurisdiction: str | None = None,
    ) -> dict:
        """
        Perform compliance assessment on a document.
        
        Args:
            document: Processed document from IntakeAgent
            frameworks: List of regulatory frameworks to check (default: all applicable)
            industry: Industry context for specialized checks
            jurisdiction: Primary jurisdiction for the document
            
        Returns:
            Comprehensive compliance assessment with gaps and recommendations
        """
        text = document.get("text_content", "")
        
        # Determine applicable frameworks
        if not frameworks:
            frameworks = await self._identify_applicable_frameworks(
                text, industry, jurisdiction
            )
        
        self.logger.info(
            "Starting compliance assessment",
            document_id=document.get("document_id"),
            frameworks=frameworks,
        )
        
        # Perform compliance checks for each framework
        framework_results = {}
        for framework in frameworks:
            if framework.lower() in self.SUPPORTED_FRAMEWORKS:
                framework_results[framework] = await self._check_framework_compliance(
                    text, framework.lower()
                )
        
        # Generate regulatory mapping
        regulatory_mapping = await self._generate_regulatory_mapping(text, frameworks)
        
        # Calculate overall compliance score
        overall_score = self._calculate_overall_score(framework_results)
        
        # Generate recommendations
        recommendations = await self._generate_compliance_recommendations(
            framework_results
        )
        
        result = {
            "document_id": document.get("document_id"),
            "assessed_at": datetime.utcnow().isoformat(),
            "jurisdiction": jurisdiction,
            "industry": industry,
            "frameworks_checked": frameworks,
            "overall_compliance_score": overall_score["score"],
            "compliance_level": overall_score["level"],
            "framework_results": framework_results,
            "regulatory_mapping": regulatory_mapping,
            "gaps_identified": self._extract_all_gaps(framework_results),
            "recommendations": recommendations,
            "required_actions": [
                r for r in recommendations
                if r.get("priority") in ["critical", "high"]
            ],
            "audit_trail": self._create_audit_entry("compliance_assessment", {
                "document_id": document.get("document_id"),
                "frameworks": frameworks,
                "overall_score": overall_score["score"],
            }),
        }
        
        self.logger.info(
            "Compliance assessment complete",
            document_id=document.get("document_id"),
            overall_score=overall_score["score"],
            gaps_found=len(result["gaps_identified"]),
        )
        
        return result

    async def _identify_applicable_frameworks(
        self,
        text: str,
        industry: str | None,
        jurisdiction: str | None,
    ) -> list[str]:
        """Identify which regulatory frameworks apply to this document."""
        prompt = f"""Analyze this legal document and identify which regulatory frameworks apply.

DOCUMENT EXCERPT (first 2000 chars):
{text[:2000]}

INDUSTRY: {industry or "Not specified"}
JURISDICTION: {jurisdiction or "Not specified"}

Consider these frameworks:
- GDPR (EU data protection)
- CCPA (California privacy)
- HIPAA (US healthcare)
- SOC2 (service organization controls)
- PCI-DSS (payment card security)
- SOX (US financial reporting)
- FERPA (US education privacy)
- GLBA (US financial privacy)

Return as JSON:
{{
    "applicable_frameworks": ["list of applicable framework codes"],
    "rationale": {{
        "framework_code": "why it applies"
    }},
    "uncertain": ["frameworks that might apply but unclear"]
}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            result = self._parse_json_response(response.content)
            return result.get("applicable_frameworks", ["gdpr", "ccpa"])
            
        except Exception as e:
            self.logger.warning(f"Framework identification failed: {e}")
            # Default to common frameworks
            return ["gdpr", "ccpa"]

    async def _check_framework_compliance(
        self,
        text: str,
        framework: str,
    ) -> dict:
        """Check compliance against a specific regulatory framework."""
        compliance_areas = self.COMPLIANCE_AREAS.get(framework, [])
        
        prompt = f"""Perform a {framework.upper()} compliance assessment on this document.

DOCUMENT:
{text[:5000]}

COMPLIANCE AREAS TO CHECK:
{json.dumps(compliance_areas, indent=2)}

For each compliance area, assess:
1. Whether the document addresses this requirement
2. If addressed, whether it's compliant
3. Specific gaps or issues found
4. Required remediation

Return as JSON:
{{
    "framework": "{framework}",
    "overall_status": "compliant/partially_compliant/non_compliant",
    "score": 0-100,
    "areas": [
        {{
            "area": "compliance area name",
            "status": "compliant/partially_compliant/non_compliant/not_addressed",
            "findings": "what was found",
            "gaps": ["specific gaps"],
            "remediation": "required fixes"
        }}
    ],
    "critical_gaps": ["most serious compliance gaps"],
    "strengths": ["areas of strong compliance"]
}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            return self._parse_json_response(response.content)
            
        except Exception as e:
            self.logger.error(f"{framework} compliance check failed: {e}")
            return {
                "framework": framework,
                "overall_status": "unknown",
                "score": 0,
                "areas": [],
                "critical_gaps": ["Assessment failed"],
                "strengths": [],
            }

    async def _generate_regulatory_mapping(
        self,
        text: str,
        frameworks: list[str],
    ) -> list[dict]:
        """Map document clauses to specific regulatory requirements."""
        prompt = f"""Map clauses in this document to specific regulatory requirements.

DOCUMENT:
{text[:4000]}

FRAMEWORKS TO MAP:
{', '.join(frameworks)}

For each significant clause, identify:
1. The clause content (summarized)
2. Which regulation(s) it relates to
3. The specific regulatory requirement
4. Whether it satisfies the requirement

Return as JSON array:
[
    {{
        "clause_summary": "brief description of the clause",
        "clause_location": "approximate location in document",
        "regulations": [
            {{
                "framework": "GDPR/CCPA/etc",
                "requirement": "specific requirement reference",
                "article_section": "Article X / Section Y",
                "satisfaction_status": "meets/partially_meets/does_not_meet",
                "notes": "additional context"
            }}
        ]
    }}
]"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            mapping = self._parse_json_response(response.content)
            return mapping if isinstance(mapping, list) else []
            
        except Exception as e:
            self.logger.error(f"Regulatory mapping failed: {e}")
            return []

    def _calculate_overall_score(self, framework_results: dict) -> dict:
        """Calculate overall compliance score from framework results."""
        if not framework_results:
            return {"score": 0, "level": "unknown"}
        
        scores = []
        for framework, result in framework_results.items():
            if isinstance(result, dict) and "score" in result:
                scores.append(result["score"])
        
        if not scores:
            return {"score": 0, "level": "unknown"}
        
        avg_score = sum(scores) / len(scores)
        
        if avg_score >= 80:
            level = "compliant"
        elif avg_score >= 60:
            level = "partially_compliant"
        else:
            level = "non_compliant"
        
        return {
            "score": round(avg_score, 1),
            "level": level,
        }

    def _extract_all_gaps(self, framework_results: dict) -> list[dict]:
        """Extract all compliance gaps from framework results."""
        gaps = []
        
        for framework, result in framework_results.items():
            if not isinstance(result, dict):
                continue
            
            # Add critical gaps
            for gap in result.get("critical_gaps", []):
                gaps.append({
                    "framework": framework,
                    "severity": "critical",
                    "description": gap,
                })
            
            # Add area-specific gaps
            for area in result.get("areas", []):
                for gap in area.get("gaps", []):
                    gaps.append({
                        "framework": framework,
                        "area": area.get("area"),
                        "severity": "high" if area.get("status") == "non_compliant" else "medium",
                        "description": gap,
                        "remediation": area.get("remediation"),
                    })
        
        return gaps

    async def _generate_compliance_recommendations(
        self,
        framework_results: dict,
    ) -> list[dict]:
        """Generate prioritized compliance recommendations."""
        recommendations = []
        
        for framework, result in framework_results.items():
            if not isinstance(result, dict):
                continue
            
            # Critical gaps get highest priority
            for gap in result.get("critical_gaps", []):
                recommendations.append({
                    "framework": framework,
                    "priority": "critical",
                    "issue": gap,
                    "recommendation": f"Immediately address {gap} to ensure {framework.upper()} compliance",
                    "timeline": "Immediate - before contract execution",
                })
            
            # Non-compliant areas
            for area in result.get("areas", []):
                if area.get("status") == "non_compliant":
                    recommendations.append({
                        "framework": framework,
                        "priority": "high",
                        "issue": f"{area.get('area')} not compliant",
                        "recommendation": area.get("remediation", f"Review and update {area.get('area')} provisions"),
                        "timeline": "Within 30 days",
                    })
                elif area.get("status") == "partially_compliant":
                    recommendations.append({
                        "framework": framework,
                        "priority": "medium",
                        "issue": f"{area.get('area')} partially compliant",
                        "recommendation": area.get("remediation", f"Strengthen {area.get('area')} provisions"),
                        "timeline": "Within 60 days",
                    })
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda x: priority_order.get(x.get("priority", "low"), 4))
        
        return recommendations

    async def check_specific_regulation(
        self,
        text: str,
        regulation: str,
        article_or_section: str,
    ) -> dict:
        """Check compliance against a specific regulation article/section."""
        prompt = f"""Check this document against a specific regulatory requirement.

DOCUMENT:
{text[:3000]}

REGULATION: {regulation}
SPECIFIC REQUIREMENT: {article_or_section}

Analyze:
1. Does the document address this requirement?
2. If so, is it compliant?
3. What specific language addresses or fails to address this?
4. What changes would be needed for compliance?

Return as JSON:
{{
    "regulation": "{regulation}",
    "requirement": "{article_or_section}",
    "addressed": true/false,
    "compliant": true/false/null,
    "relevant_text": "document text that addresses this",
    "analysis": "detailed compliance analysis",
    "required_changes": ["list of changes needed for compliance"]
}}"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            return self._parse_json_response(response.content)
            
        except Exception as e:
            self.logger.error(f"Specific regulation check failed: {e}")
            return {
                "regulation": regulation,
                "requirement": article_or_section,
                "addressed": None,
                "compliant": None,
                "analysis": "Check failed",
                "required_changes": [],
            }

    def _parse_json_response(self, content: str) -> Any:
        """Parse JSON from LLM response."""
        content = content.strip()
        
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            if content.startswith("json"):
                content = content[4:].strip()
        
        return json.loads(content)
