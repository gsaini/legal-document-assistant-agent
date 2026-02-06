"""Legal Document Assistant - Orchestrator Agent.

This is the main coordinating agent that orchestrates the multi-agent workflow
for comprehensive legal document processing using LangGraph.
"""

from datetime import datetime
from typing import Any, TypedDict
import uuid

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END

import structlog

from src.agents.base import BaseAgent
from src.agents.intake_agent import IntakeAgent
from src.agents.analysis_agent import ContractAnalysisAgent
from src.agents.research_agent import LegalResearchAgent
from src.agents.redlining_agent import RedliningAgent
from src.agents.compliance_agent import ComplianceAgent


class DocumentState(TypedDict):
    """State passed between agents in the workflow."""
    
    # Document information
    document_id: str
    file_path: str
    
    # Processing state
    stage: str
    error: str | None
    
    # Agent outputs
    intake_result: dict | None
    analysis_result: dict | None
    research_result: dict | None
    redline_result: dict | None
    compliance_result: dict | None
    
    # Final output
    final_report: dict | None
    
    # Configuration
    config: dict


class LegalDocumentOrchestrator(BaseAgent):
    """
    Orchestrator agent that coordinates all specialized legal agents.
    
    Responsibilities:
    - Multi-agent workflow management using LangGraph
    - Conflict resolution between agents
    - Progress tracking and state management
    - Final report generation
    """

    def __init__(self):
        super().__init__(
            name="Legal Document Orchestrator",
            description="Master coordinator orchestrating the multi-agent legal document review workflow"
        )
        
        # Initialize specialized agents
        self.intake_agent = IntakeAgent()
        self.analysis_agent = ContractAnalysisAgent()
        self.research_agent = LegalResearchAgent()
        self.redlining_agent = RedliningAgent()
        self.compliance_agent = ComplianceAgent()
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        
        self.logger.info("Orchestrator initialized with all specialized agents")

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow for multi-agent coordination."""
        workflow = StateGraph(DocumentState)
        
        # Add nodes for each agent
        workflow.add_node("intake", self._intake_node)
        workflow.add_node("analysis", self._analysis_node)
        workflow.add_node("research", self._research_node)
        workflow.add_node("compliance", self._compliance_node)
        workflow.add_node("redlining", self._redlining_node)
        workflow.add_node("final_report", self._final_report_node)
        
        # Define the workflow edges
        workflow.set_entry_point("intake")
        
        workflow.add_edge("intake", "analysis")
        workflow.add_edge("analysis", "research")
        workflow.add_edge("research", "compliance")
        workflow.add_edge("compliance", "redlining")
        workflow.add_edge("redlining", "final_report")
        workflow.add_edge("final_report", END)
        
        return workflow.compile()

    async def run(
        self,
        file_path: str,
        config: dict | None = None,
    ) -> dict:
        """
        Process a legal document through the complete workflow.
        
        Args:
            file_path: Path to the document to process
            config: Optional configuration for the workflow
                - detect_pii: bool (default: True)
                - redact_pii: bool (default: False)
                - compliance_frameworks: list[str] (default: auto-detect)
                - jurisdiction: str (default: None)
                - clause_library: dict (default: None)
                - style_guide: dict (default: None)
                
        Returns:
            Comprehensive legal document review report
        """
        document_id = str(uuid.uuid4())[:8]
        
        self.logger.info(
            "Starting legal document processing",
            document_id=document_id,
            file_path=file_path,
        )
        
        # Initialize state
        initial_state: DocumentState = {
            "document_id": document_id,
            "file_path": file_path,
            "stage": "intake",
            "error": None,
            "intake_result": None,
            "analysis_result": None,
            "research_result": None,
            "redline_result": None,
            "compliance_result": None,
            "final_report": None,
            "config": config or {},
        }
        
        try:
            # Run the workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            self.logger.info(
                "Document processing complete",
                document_id=document_id,
                stage=final_state.get("stage"),
            )
            
            return final_state.get("final_report", {})
            
        except Exception as e:
            self.logger.error(
                "Document processing failed",
                document_id=document_id,
                error=str(e),
            )
            
            return {
                "document_id": document_id,
                "status": "failed",
                "error": str(e),
                "stage": initial_state.get("stage"),
            }

    async def _intake_node(self, state: DocumentState) -> DocumentState:
        """Process document through Intake Agent."""
        self.logger.info("Stage: Intake", document_id=state["document_id"])
        
        try:
            config = state.get("config", {})
            
            result = await self.intake_agent.run(
                file_path=state["file_path"],
                detect_pii=config.get("detect_pii", True),
                redact_pii=config.get("redact_pii", False),
            )
            
            state["intake_result"] = result
            state["stage"] = "intake_complete"
            
        except Exception as e:
            self.logger.error(f"Intake failed: {e}")
            state["error"] = str(e)
            state["stage"] = "intake_failed"
        
        return state

    async def _analysis_node(self, state: DocumentState) -> DocumentState:
        """Process document through Analysis Agent."""
        self.logger.info("Stage: Analysis", document_id=state["document_id"])
        
        if state.get("error"):
            return state
        
        try:
            config = state.get("config", {})
            
            result = await self.analysis_agent.run(
                document=state["intake_result"],
                focus_areas=config.get("focus_areas"),
                comparison_standard=config.get("comparison_standard"),
            )
            
            state["analysis_result"] = result
            state["stage"] = "analysis_complete"
            
        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            state["error"] = str(e)
            state["stage"] = "analysis_failed"
        
        return state

    async def _research_node(self, state: DocumentState) -> DocumentState:
        """Perform legal research based on analysis findings."""
        self.logger.info("Stage: Research", document_id=state["document_id"])
        
        if state.get("error"):
            return state
        
        try:
            analysis = state.get("analysis_result", {})
            config = state.get("config", {})
            
            # Research high-risk items
            high_risk_items = analysis.get("high_risk_items", [])
            
            research_queries = []
            for item in high_risk_items[:3]:  # Limit to top 3 risks
                research_queries.append({
                    "query": item.get("clause_text", "")[:200],
                    "category": item.get("category", "general"),
                })
            
            # Perform research for each query
            research_results = []
            for query_info in research_queries:
                result = await self.research_agent.run(
                    query=f"Legal research for {query_info['category']}: {query_info['query']}",
                    research_type="general",
                    jurisdiction=config.get("jurisdiction"),
                    document_context=analysis,
                )
                research_results.append(result)
            
            state["research_result"] = {
                "queries_performed": len(research_queries),
                "results": research_results,
                "consolidated_findings": self._consolidate_research(research_results),
            }
            state["stage"] = "research_complete"
            
        except Exception as e:
            self.logger.error(f"Research failed: {e}")
            state["error"] = str(e)
            state["stage"] = "research_failed"
        
        return state

    async def _compliance_node(self, state: DocumentState) -> DocumentState:
        """Check regulatory compliance."""
        self.logger.info("Stage: Compliance", document_id=state["document_id"])
        
        if state.get("error"):
            return state
        
        try:
            config = state.get("config", {})
            
            result = await self.compliance_agent.run(
                document=state["intake_result"],
                frameworks=config.get("compliance_frameworks"),
                industry=config.get("industry"),
                jurisdiction=config.get("jurisdiction"),
            )
            
            state["compliance_result"] = result
            state["stage"] = "compliance_complete"
            
        except Exception as e:
            self.logger.error(f"Compliance check failed: {e}")
            state["error"] = str(e)
            state["stage"] = "compliance_failed"
        
        return state

    async def _redlining_node(self, state: DocumentState) -> DocumentState:
        """Generate redline suggestions."""
        self.logger.info("Stage: Redlining", document_id=state["document_id"])
        
        if state.get("error"):
            return state
        
        try:
            config = state.get("config", {})
            
            result = await self.redlining_agent.run(
                document=state["intake_result"],
                analysis=state["analysis_result"],
                clause_library=config.get("clause_library"),
                style_guide=config.get("style_guide"),
            )
            
            state["redline_result"] = result
            state["stage"] = "redlining_complete"
            
        except Exception as e:
            self.logger.error(f"Redlining failed: {e}")
            state["error"] = str(e)
            state["stage"] = "redlining_failed"
        
        return state

    async def _final_report_node(self, state: DocumentState) -> DocumentState:
        """Generate the final comprehensive report."""
        self.logger.info("Stage: Final Report", document_id=state["document_id"])
        
        try:
            intake = state.get("intake_result", {})
            analysis = state.get("analysis_result", {})
            research = state.get("research_result", {})
            compliance = state.get("compliance_result", {})
            redline = state.get("redline_result", {})
            
            # Generate executive summary
            executive_summary = await self._generate_executive_summary(
                analysis, compliance, redline
            )
            
            final_report = {
                "document_id": state["document_id"],
                "generated_at": datetime.utcnow().isoformat(),
                "status": "complete" if not state.get("error") else "partial",
                "error": state.get("error"),
                
                # Executive Summary
                "executive_summary": executive_summary,
                
                # Document Overview
                "document_overview": {
                    "file_name": intake.get("file_name"),
                    "file_type": intake.get("file_type"),
                    "page_count": intake.get("page_count"),
                    "word_count": intake.get("word_count"),
                    "document_type": intake.get("metadata", {}).get("document_type"),
                    "parties": intake.get("metadata", {}).get("parties", []),
                },
                
                # Risk Assessment
                "risk_assessment": {
                    "overall_score": analysis.get("overall_risk_score"),
                    "risk_level": analysis.get("risk_level"),
                    "risk_summary": analysis.get("risk_summary"),
                    "high_risk_items": analysis.get("high_risk_items", []),
                    "risk_heatmap": analysis.get("risk_heatmap", []),
                },
                
                # Contract Analysis
                "contract_analysis": {
                    "clauses": analysis.get("clauses", []),
                    "entities": analysis.get("entities", {}),
                    "obligations": analysis.get("obligations", []),
                },
                
                # Legal Research
                "legal_research": {
                    "queries_performed": research.get("queries_performed", 0),
                    "consolidated_findings": research.get("consolidated_findings", {}),
                },
                
                # Compliance Assessment
                "compliance_assessment": {
                    "overall_score": compliance.get("overall_compliance_score"),
                    "compliance_level": compliance.get("compliance_level"),
                    "frameworks_checked": compliance.get("frameworks_checked", []),
                    "gaps_identified": compliance.get("gaps_identified", []),
                    "regulatory_mapping": compliance.get("regulatory_mapping", []),
                },
                
                # Redline Suggestions
                "redline_suggestions": {
                    "total_suggestions": redline.get("total_suggestions", 0),
                    "by_priority": redline.get("by_priority", {}),
                    "suggestions": redline.get("suggestions", []),
                    "summary": redline.get("summary", {}),
                },
                
                # Consolidated Recommendations
                "recommendations": self._consolidate_recommendations(
                    analysis, compliance, redline
                ),
                
                # Audit Trail
                "audit_trail": {
                    "processing_stages": [
                        {"stage": "intake", "status": "complete" if intake else "failed"},
                        {"stage": "analysis", "status": "complete" if analysis else "failed"},
                        {"stage": "research", "status": "complete" if research else "failed"},
                        {"stage": "compliance", "status": "complete" if compliance else "failed"},
                        {"stage": "redlining", "status": "complete" if redline else "failed"},
                    ],
                    "document_hash": intake.get("hash"),
                    "pii_detected": bool(intake.get("pii_findings")),
                    "pii_redacted": intake.get("pii_redacted", False),
                },
            }
            
            state["final_report"] = final_report
            state["stage"] = "complete"
            
        except Exception as e:
            self.logger.error(f"Final report generation failed: {e}")
            state["error"] = str(e)
            state["stage"] = "report_failed"
        
        return state

    async def _generate_executive_summary(
        self,
        analysis: dict,
        compliance: dict,
        redline: dict,
    ) -> dict:
        """Generate executive summary for decision-makers."""
        risk_level = analysis.get("risk_level", "unknown")
        compliance_level = compliance.get("compliance_level", "unknown")
        total_suggestions = redline.get("total_suggestions", 0)
        critical_suggestions = len(redline.get("by_priority", {}).get("critical", []))
        
        # Determine overall recommendation
        if risk_level == "high" or compliance_level == "non_compliant":
            overall_recommendation = "DO NOT EXECUTE - Significant issues require resolution"
            urgency = "critical"
        elif risk_level == "medium" or compliance_level == "partially_compliant":
            overall_recommendation = "NEGOTIATE CHANGES - Address issues before execution"
            urgency = "high"
        else:
            overall_recommendation = "REVIEW SUGGESTIONS - Minor improvements recommended"
            urgency = "standard"
        
        return {
            "overall_recommendation": overall_recommendation,
            "urgency": urgency,
            "risk_level": risk_level,
            "compliance_level": compliance_level,
            "key_findings": {
                "high_risk_items": len(analysis.get("high_risk_items", [])),
                "compliance_gaps": len(compliance.get("gaps_identified", [])),
                "suggested_changes": total_suggestions,
                "critical_changes": critical_suggestions,
            },
            "action_required": [
                item.get("concern")
                for item in analysis.get("high_risk_items", [])[:3]
                if item.get("severity") == "high"
            ],
            "estimated_negotiation_complexity": redline.get("summary", {}).get(
                "estimated_negotiation_complexity", "unknown"
            ),
        }

    def _consolidate_research(self, research_results: list[dict]) -> dict:
        """Consolidate findings from multiple research queries."""
        all_cases = []
        all_statutes = []
        all_citations = []
        
        for result in research_results:
            all_cases.extend(result.get("relevant_cases", []))
            all_statutes.extend(result.get("relevant_statutes", []))
            all_citations.extend(result.get("citations", []))
        
        return {
            "cases": all_cases[:10],  # Top 10 cases
            "statutes": all_statutes[:10],
            "citations": all_citations[:15],
            "total_sources": len(all_cases) + len(all_statutes),
        }

    def _consolidate_recommendations(
        self,
        analysis: dict,
        compliance: dict,
        redline: dict,
    ) -> list[dict]:
        """Consolidate recommendations from all agents."""
        all_recommendations = []
        
        # From analysis
        all_recommendations.extend(analysis.get("recommendations", []))
        
        # From compliance
        all_recommendations.extend(compliance.get("recommendations", []))
        
        # From redline (convert suggestions to recommendations)
        for suggestion in redline.get("suggestions", [])[:10]:
            if suggestion.get("priority") in ["critical", "high"]:
                all_recommendations.append({
                    "priority": suggestion.get("priority"),
                    "category": suggestion.get("category"),
                    "issue": f"Contract language issue in {suggestion.get('category', 'clause')}",
                    "recommendation": suggestion.get("rationale"),
                    "action_required": True,
                })
        
        # Sort by priority and deduplicate
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        all_recommendations.sort(
            key=lambda x: priority_order.get(x.get("priority", "low"), 4)
        )
        
        return all_recommendations[:20]  # Top 20 recommendations

    async def quick_review(
        self,
        file_path: str,
    ) -> dict:
        """
        Perform a quick review (intake + analysis only).
        
        Use for fast initial assessments.
        """
        self.logger.info("Starting quick review", file_path=file_path)
        
        # Intake
        intake_result = await self.intake_agent.run(
            file_path=file_path,
            detect_pii=True,
            redact_pii=False,
        )
        
        # Analysis
        analysis_result = await self.analysis_agent.run(
            document=intake_result,
        )
        
        return {
            "document_id": intake_result.get("document_id"),
            "quick_review": True,
            "document_type": intake_result.get("metadata", {}).get("document_type"),
            "page_count": intake_result.get("page_count"),
            "risk_score": analysis_result.get("overall_risk_score"),
            "risk_level": analysis_result.get("risk_level"),
            "risk_summary": analysis_result.get("risk_summary"),
            "high_risk_count": len(analysis_result.get("high_risk_items", [])),
            "top_risks": analysis_result.get("high_risk_items", [])[:3],
            "recommendation": (
                "Full review recommended"
                if analysis_result.get("risk_level") in ["high", "medium"]
                else "Low risk - standard review sufficient"
            ),
        }
