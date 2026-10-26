"""
DataShield AI — GenAI Report Service
======================================
Coordinates RAG knowledge base retrieval, SHAP feature explanations,
and report generation for threats detected by the ML engine.
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional

from genai_explainer.rag_pipeline import SecurityKnowledgeBase
from genai_explainer.shap_analyzer import SHAPAnalyzer
from genai_explainer.report_generator import ThreatReportGenerator

logger = logging.getLogger("datashield.report_service")


class ReportService:
    """
    Service wrapper for threat report generation with resilient fallbacks.
    """

    def __init__(self):
        try:
            self.kb = SecurityKnowledgeBase()
            self.shap = SHAPAnalyzer()
            self.generator = ThreatReportGenerator(
                knowledge_base=self.kb,
                shap_analyzer=self.shap,
            )
            self._ready = True
            logger.info("ReportService initialized successfully.")
        except Exception as e:
            logger.error(f"ReportService initialization error: {e}")
            self.kb = None
            self.shap = None
            self.generator = None
            self._ready = False

    def generate_report(
        self,
        event_data: Dict[str, Any],
        threat_score: float,
        threat_level: str,
        shap_explanation: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Produces detailed report dictionary.
        """
        if self._ready and self.generator:
            try:
                return self.generator.generate_report(
                    event_data=event_data,
                    threat_score=threat_score,
                    threat_level=threat_level,
                    shap_explanation=shap_explanation,
                )
            except Exception as e:
                logger.error(f"Error calling report generator: {e}")

        # Fallback quick generation
        return {
            "full_report": f"Threat Level: {threat_level} (Score: {threat_score}/100)\nEvent targeting {event_data.get('table_name')} by {event_data.get('user_id')}.",
            "executive_summary": f"Detected potential threat for user {event_data.get('user_id')} with score {threat_score}.",
            "recommended_actions": ["Review user access logs", "Enforce temporary MFA re-authentication"],
            "compliance_notes": ["Log recorded for security review."],
            "risk_level": threat_level,
            "threat_score": threat_score,
            "confidence": 0.85,
            "timestamp": event_data.get("timestamp", ""),
            "generator": "Fallback-Static",
        }

    def get_service_status(self) -> Dict[str, Any]:
        return {
            "status": "online" if self._ready else "degraded",
            "rag_indexed_policies": len(self.kb.policies) if self.kb else 0,
            "rag_indexed_incidents": len(self.kb.incidents) if self.kb else 0,
            "llm_connected": bool(self.generator and (getattr(self.generator, "groq_client", None) or getattr(self.generator, "gemini_client", None))),
            "provider": getattr(self.generator, "groq_model", "Groq/Gemini") if (self.generator and getattr(self.generator, "groq_client", None)) else "fallback",
        }
