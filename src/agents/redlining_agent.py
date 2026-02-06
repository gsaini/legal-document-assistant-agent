"""Legal Document Assistant - Redlining Agent.

This agent generates contract redlines and suggested edits:
- One-click redlining with track changes
- Clause library comparison
- Tone and language alignment
- Variation detection from standard language
"""

from typing import Any
from datetime import datetime
import json
from difflib import unified_diff, SequenceMatcher

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from src.agents.base import BaseAgent
from src.config import get_settings


class RedliningAgent(BaseAgent):
    """
    Redlining Agent for contract editing suggestions.
    
    Responsibilities:
    - Generate redline suggestions based on risk analysis
    - Compare clauses against pre-approved library
    - Suggest alternative language from standard templates
    - Track all suggested changes with justifications
    """

    def __init__(self):
        super().__init__(
            name="Redlining Agent",
            description="Contract drafting specialist generating precise redline suggestions and standardized language"
        )
        self.settings = get_settings()

    async def run(
        self,
        document: dict,
        analysis: dict,
        clause_library: dict | None = None,
        style_guide: dict | None = None,
    ) -> dict:
        """
        Generate redline suggestions for a document.
        
        Args:
            document: Processed document from IntakeAgent
            analysis: Analysis results from ContractAnalysisAgent
            clause_library: Pre-approved clause library to use
            style_guide: Institutional style guide for tone alignment
            
        Returns:
            Redline suggestions with track changes markup
        """
        text = document.get("text_content", "")
        
        self.logger.info(
            "Generating redline suggestions",
            document_id=document.get("document_id"),
            high_risk_items=len(analysis.get("high_risk_items", [])),
        )
        
        # Generate suggestions for high-risk items
        risk_suggestions = await self._generate_risk_suggestions(
            text, analysis.get("high_risk_items", [])
        )
        
        # Generate suggestions for unfavorable clauses
        clause_suggestions = await self._generate_clause_suggestions(
            text, analysis.get("clauses", []), clause_library
        )
        
        # Check for style guide compliance
        style_suggestions = []
        if style_guide:
            style_suggestions = await self._check_style_compliance(
                text, style_guide
            )
        
        # Combine all suggestions
        all_suggestions = risk_suggestions + clause_suggestions + style_suggestions
        
        # Sort by position in document
        all_suggestions.sort(key=lambda x: x.get("position", 0))
        
        # Generate unified diff view
        redline_diff = self._generate_diff_view(text, all_suggestions)
        
        result = {
            "document_id": document.get("document_id"),
            "generated_at": datetime.utcnow().isoformat(),
            "total_suggestions": len(all_suggestions),
            "suggestions": all_suggestions,
            "by_priority": {
                "critical": [s for s in all_suggestions if s.get("priority") == "critical"],
                "high": [s for s in all_suggestions if s.get("priority") == "high"],
                "medium": [s for s in all_suggestions if s.get("priority") == "medium"],
                "low": [s for s in all_suggestions if s.get("priority") == "low"],
            },
            "by_category": self._group_by_category(all_suggestions),
            "redline_diff": redline_diff,
            "summary": await self._generate_summary(all_suggestions),
            "audit_trail": self._create_audit_entry("redline_generation", {
                "document_id": document.get("document_id"),
                "suggestions_count": len(all_suggestions),
            }),
        }
        
        self.logger.info(
            "Redline generation complete",
            document_id=document.get("document_id"),
            total_suggestions=len(all_suggestions),
        )
        
        return result

    async def _generate_risk_suggestions(
        self,
        text: str,
        high_risk_items: list[dict],
    ) -> list[dict]:
        """Generate redline suggestions for high-risk items."""
        suggestions = []
        
        for item in high_risk_items:
            clause_text = item.get("clause_text", "")
            if not clause_text:
                continue
            
            # Find position in document
            position = text.find(clause_text)
            
            prompt = f"""Generate a redline suggestion for this problematic clause.

ORIGINAL CLAUSE:
{clause_text}

ISSUE: {item.get("concern", "Risk identified")}
CATEGORY: {item.get("category", "general")}
SEVERITY: {item.get("severity", "medium")}

Provide:
1. Suggested replacement text that addresses the concern
2. Brief explanation of what changed and why
3. Any negotiation talking points

Return as JSON:
{{
    "suggested_text": "the improved clause text",
    "changes_made": ["list of specific changes"],
    "rationale": "why these changes help",
    "negotiation_points": ["talking points if pushback expected"],
    "risk_reduction": "how this reduces risk"
}}"""

            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt),
                ])
                
                suggestion_data = self._parse_json_response(response.content)
                
                suggestions.append({
                    "id": f"risk_{len(suggestions)}",
                    "type": "risk_mitigation",
                    "category": item.get("category", "general"),
                    "priority": "critical" if item.get("severity") == "high" else "high",
                    "position": position if position >= 0 else None,
                    "original_text": clause_text,
                    "suggested_text": suggestion_data.get("suggested_text", ""),
                    "changes_made": suggestion_data.get("changes_made", []),
                    "rationale": suggestion_data.get("rationale", ""),
                    "negotiation_points": suggestion_data.get("negotiation_points", []),
                    "risk_reduction": suggestion_data.get("risk_reduction", ""),
                    "source": "risk_analysis",
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to generate suggestion for risk item: {e}")
        
        return suggestions

    async def _generate_clause_suggestions(
        self,
        text: str,
        clauses: list[dict],
        clause_library: dict | None,
    ) -> list[dict]:
        """Generate suggestions for unfavorable clauses."""
        suggestions = []
        
        unfavorable_clauses = [
            c for c in clauses
            if c.get("favorability") == "unfavorable"
        ]
        
        for clause in unfavorable_clauses:
            clause_text = clause.get("full_text", clause.get("summary", ""))
            clause_type = clause.get("clause_type", "general")
            
            # Check if we have a pre-approved alternative
            approved_alternative = None
            if clause_library and clause_type in clause_library:
                approved_alternative = clause_library[clause_type]
            
            position = text.find(clause_text[:100]) if clause_text else -1
            
            prompt = f"""Generate a redline suggestion for this unfavorable clause.

ORIGINAL CLAUSE ({clause_type}):
{clause_text}

CLAUSE TYPE: {clause_type}
NOTES: {clause.get("notes", "No specific notes")}

{"APPROVED ALTERNATIVE (use this as basis):" + approved_alternative if approved_alternative else "Generate a balanced alternative."}

Provide:
1. Suggested replacement that is more balanced/favorable
2. Explanation of key changes
3. Why the original is unfavorable

Return as JSON:
{{
    "suggested_text": "the improved clause text",
    "changes_made": ["list of specific changes"],
    "rationale": "why original is unfavorable and how this helps",
    "based_on_library": true/false
}}"""

            try:
                response = await self.llm.ainvoke([
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt),
                ])
                
                suggestion_data = self._parse_json_response(response.content)
                
                suggestions.append({
                    "id": f"clause_{len(suggestions)}",
                    "type": "clause_improvement",
                    "category": clause_type,
                    "priority": "high",
                    "position": position if position >= 0 else None,
                    "original_text": clause_text,
                    "suggested_text": suggestion_data.get("suggested_text", ""),
                    "changes_made": suggestion_data.get("changes_made", []),
                    "rationale": suggestion_data.get("rationale", ""),
                    "based_on_library": suggestion_data.get("based_on_library", False),
                    "source": "clause_analysis",
                })
                
            except Exception as e:
                self.logger.warning(f"Failed to generate clause suggestion: {e}")
        
        return suggestions

    async def _check_style_compliance(
        self,
        text: str,
        style_guide: dict,
    ) -> list[dict]:
        """Check document against institutional style guide."""
        suggestions = []
        
        prompt = f"""Review this document against the style guide and identify deviations.

DOCUMENT (first 3000 chars):
{text[:3000]}

STYLE GUIDE REQUIREMENTS:
{json.dumps(style_guide, indent=2)}

Identify:
1. Terms that should be replaced per the style guide
2. Formatting issues
3. Tone inconsistencies
4. Required language that is missing

Return as JSON array:
[
    {{
        "issue_type": "terminology/formatting/tone/missing",
        "original_text": "the problematic text",
        "suggested_text": "the corrected text",
        "style_rule": "which rule this violates",
        "priority": "high/medium/low"
    }}
]"""

        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt),
            ])
            
            style_issues = self._parse_json_response(response.content)
            
            for i, issue in enumerate(style_issues if isinstance(style_issues, list) else []):
                position = text.find(issue.get("original_text", "")[:50])
                
                suggestions.append({
                    "id": f"style_{i}",
                    "type": "style_compliance",
                    "category": issue.get("issue_type", "style"),
                    "priority": issue.get("priority", "low"),
                    "position": position if position >= 0 else None,
                    "original_text": issue.get("original_text", ""),
                    "suggested_text": issue.get("suggested_text", ""),
                    "changes_made": [f"Style rule: {issue.get('style_rule', '')}"],
                    "rationale": f"Style guide compliance: {issue.get('style_rule', '')}",
                    "source": "style_guide",
                })
                
        except Exception as e:
            self.logger.warning(f"Style compliance check failed: {e}")
        
        return suggestions

    def _generate_diff_view(
        self,
        original_text: str,
        suggestions: list[dict],
    ) -> list[dict]:
        """Generate unified diff view for all suggestions."""
        diff_items = []
        
        for suggestion in suggestions:
            original = suggestion.get("original_text", "")
            suggested = suggestion.get("suggested_text", "")
            
            if original and suggested:
                # Generate unified diff
                diff = list(unified_diff(
                    original.splitlines(keepends=True),
                    suggested.splitlines(keepends=True),
                    fromfile="original",
                    tofile="suggested",
                    lineterm="",
                ))
                
                # Calculate similarity
                similarity = SequenceMatcher(None, original, suggested).ratio()
                
                diff_items.append({
                    "suggestion_id": suggestion.get("id"),
                    "diff_lines": diff,
                    "diff_text": "".join(diff),
                    "similarity": round(similarity, 2),
                    "change_magnitude": "minor" if similarity > 0.8 else "moderate" if similarity > 0.5 else "major",
                })
        
        return diff_items

    def _group_by_category(self, suggestions: list[dict]) -> dict:
        """Group suggestions by category."""
        grouped = {}
        
        for suggestion in suggestions:
            category = suggestion.get("category", "other")
            if category not in grouped:
                grouped[category] = []
            grouped[category].append(suggestion)
        
        return grouped

    async def _generate_summary(self, suggestions: list[dict]) -> dict:
        """Generate executive summary of redline suggestions."""
        critical_count = len([s for s in suggestions if s.get("priority") == "critical"])
        high_count = len([s for s in suggestions if s.get("priority") == "high"])
        
        categories = {}
        for s in suggestions:
            cat = s.get("category", "other")
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_suggestions": len(suggestions),
            "critical_issues": critical_count,
            "high_priority_issues": high_count,
            "categories_affected": categories,
            "estimated_negotiation_complexity": (
                "high" if critical_count > 2 else
                "medium" if critical_count > 0 or high_count > 3 else
                "low"
            ),
            "recommendation": (
                "Immediate review required - critical risks identified"
                if critical_count > 0 else
                "Review recommended - significant improvements suggested"
                if high_count > 2 else
                "Minor improvements suggested"
            ),
        }

    async def apply_suggestions(
        self,
        original_text: str,
        suggestions: list[dict],
        suggestion_ids: list[str] | None = None,
    ) -> str:
        """Apply selected suggestions to generate revised document."""
        revised_text = original_text
        
        # Filter suggestions if specific IDs provided
        to_apply = suggestions
        if suggestion_ids:
            to_apply = [s for s in suggestions if s.get("id") in suggestion_ids]
        
        # Sort by position (reverse order to maintain positions)
        to_apply.sort(key=lambda x: x.get("position", 0) or 0, reverse=True)
        
        for suggestion in to_apply:
            original = suggestion.get("original_text", "")
            suggested = suggestion.get("suggested_text", "")
            
            if original and suggested:
                revised_text = revised_text.replace(original, suggested, 1)
        
        return revised_text

    def _parse_json_response(self, content: str) -> Any:
        """Parse JSON from LLM response."""
        content = content.strip()
        
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
            if content.startswith("json"):
                content = content[4:].strip()
        
        return json.loads(content)
