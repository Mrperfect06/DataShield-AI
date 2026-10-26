"""
DataShield AI — Reports API Router
====================================
Dedicated endpoints for forensic report generation and knowledge-base query.
"""

from __future__ import annotations

from typing import Dict, Any, List
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

from api.models.schemas import ThreatReportResponse

router = APIRouter(prefix="/api/reports", tags=["Reports & Explainability"])


class GenerateReportRequest(BaseModel):
    event_data: Dict[str, Any]
    threat_score: float
    threat_level: str


@router.post("/generate", response_model=ThreatReportResponse)
async def generate_custom_report(payload: GenerateReportRequest, request: Request):
    """Generates an explainable forensic report for a given event and threat score."""
    report_svc = request.app.state.report_service
    res = report_svc.generate_report(
        event_data=payload.event_data,
        threat_score=payload.threat_score,
        threat_level=payload.threat_level,
    )
    return ThreatReportResponse(
        event_id=payload.event_data.get("event_id", "EVT-ON-DEMAND"),
        full_report=res.get("full_report", ""),
        executive_summary=res.get("executive_summary", ""),
        recommended_actions=res.get("recommended_actions", []),
        compliance_notes=res.get("compliance_notes", []),
        risk_level=res.get("risk_level", payload.threat_level),
        confidence=res.get("confidence", 0.90),
        threat_score=payload.threat_score,
        threat_level=payload.threat_level,
    )


@router.get("/policies")
async def list_indexed_policies(request: Request):
    """Returns corporate compliance policies indexed in RAG."""
    report_svc = request.app.state.report_service
    if report_svc and report_svc.kb:
        return {"total": len(report_svc.kb.policies), "policies": report_svc.kb.policies}
    return {"total": 0, "policies": []}
