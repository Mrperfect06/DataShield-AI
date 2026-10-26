"""
DataShield AI — Blockchain API Router
=======================================
Endpoints for querying verified on-chain events and managing threat alerts.
"""

from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Request, HTTPException

from api.models.schemas import ThreatAlertResponse

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain Audit"])


@router.get("/events")
async def get_all_events(request: Request):
    """Retrieves all immutable access event records stored in audit ledger."""
    blockchain_svc = request.app.state.blockchain_service
    events = blockchain_svc.get_events()
    return {"total": len(events), "events": events}


@router.get("/alerts")
async def get_all_alerts(request: Request):
    """Retrieves all automated threat alerts recorded on-chain."""
    blockchain_svc = request.app.state.blockchain_service
    alerts = blockchain_svc.get_alerts()
    return {"total": len(alerts), "alerts": alerts}


@router.get("/alerts/unresolved")
async def get_unresolved_alerts(request: Request):
    """Retrieves pending / active threat alerts awaiting SOC resolution."""
    blockchain_svc = request.app.state.blockchain_service
    unresolved = blockchain_svc.get_unresolved_alerts()
    return {"total": len(unresolved), "alerts": unresolved}


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: int, request: Request):
    """Resolves an on-chain threat alert."""
    blockchain_svc = request.app.state.blockchain_service
    res = blockchain_svc.resolve_alert(alert_id)
    return res


@router.get("/status")
async def get_blockchain_status(request: Request):
    """Returns connectivity and smart contract address details."""
    blockchain_svc = request.app.state.blockchain_service
    return blockchain_svc.get_service_status()
