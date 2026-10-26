"""
DataShield AI — Pydantic Request / Response Schemas
=====================================================
Defines every data model exchanged through the FastAPI layer.

These schemas handle serialisation, validation, and OpenAPI documentation
for all endpoints in the DataShield AI API.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────────────────────
# Request Models
# ──────────────────────────────────────────────────────────────────────────────

class AccessEventInput(BaseModel):
    """Incoming access-log event submitted for analysis.

    Mirrors the fields produced by ``ml_engine.data_generator`` minus the
    label columns (``is_anomalous``, ``anomaly_type``) which are unknown at
    inference time.
    """

    user_id: str = Field(..., description="Unique user identifier (e.g. 'user_001').")
    user_email: str = Field(..., description="Corporate e-mail of the user.")
    user_role: str = Field(
        ...,
        description="Organisational role — engineer, analyst, admin, intern, contractor.",
    )
    department: str = Field(..., description="Department the user belongs to.")
    action: str = Field(
        ...,
        description="Database action performed — SELECT, UPDATE, DELETE, EXPORT, DOWNLOAD.",
    )
    table_name: str = Field(..., description="Fully-qualified table name accessed.")
    columns_accessed: List[str] = Field(
        default_factory=list,
        description="List of column names accessed in this query.",
    )
    num_rows_affected: int = Field(
        ..., ge=0, description="Number of rows read or modified."
    )
    source_ip: str = Field(..., description="Source IP address of the request.")
    geo_location: str = Field(
        ..., description="Geo-location string, e.g. 'New York, US'."
    )
    session_duration_seconds: int = Field(
        ..., ge=0, description="Duration of the active session in seconds."
    )
    is_vpn: bool = Field(
        default=False, description="Whether the session originated from a VPN."
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "user_007",
                    "user_email": "jbond@shield.io",
                    "user_role": "analyst",
                    "department": "Security",
                    "action": "EXPORT",
                    "table_name": "prod.credit_cards",
                    "columns_accessed": ["credit_card", "ssn", "email"],
                    "num_rows_affected": 150000,
                    "source_ip": "185.12.44.9",
                    "geo_location": "Moscow, RU",
                    "session_duration_seconds": 120,
                    "is_vpn": False,
                }
            ]
        }
    }


# ──────────────────────────────────────────────────────────────────────────────
# Response Models
# ──────────────────────────────────────────────────────────────────────────────

class AccessEventResponse(BaseModel):
    """Result of ML-based anomaly detection for a single event."""

    event_id: str = Field(..., description="Unique identifier assigned to the event.")
    timestamp: str = Field(..., description="ISO-8601 timestamp of the analysis.")
    threat_score: float = Field(
        ..., ge=0, le=100, description="Composite threat score (0–100)."
    )
    threat_level: str = Field(
        ..., description="Categorical level — low, medium, high, critical."
    )
    is_anomalous: bool = Field(
        ..., description="Whether the event crossed the anomaly threshold."
    )
    contributing_factors: List[str] = Field(
        default_factory=list,
        description="List of factors that contributed to the threat score.",
    )
    honey_token_tripped: bool = Field(
        default=False,
        description="Whether a planted decoy honey token or watermarked record was accessed.",
    )
    proof_of_theft: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Cryptographic proof-of-theft certificate tying stolen data to user.",
    )


class ThreatReportResponse(BaseModel):
    """Full GenAI-generated threat analysis report."""

    event_id: str = Field(..., description="Identifier of the analysed event.")
    full_report: str = Field(
        ..., description="Complete narrative threat report (Markdown)."
    )
    executive_summary: str = Field(
        ..., description="One-paragraph summary for executives."
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Ordered list of recommended remediation steps.",
    )
    compliance_notes: List[str] = Field(
        default_factory=list,
        description="Applicable compliance/regulatory notes (GDPR, HIPAA, etc.).",
    )
    risk_level: str = Field(..., description="Overall risk level assessment.")
    confidence: float = Field(
        ..., ge=0, le=1, description="Model confidence in the assessment (0–1)."
    )
    threat_score: float = Field(
        ..., ge=0, le=100, description="Numeric threat score (0–100)."
    )
    threat_level: str = Field(
        ..., description="Categorical threat level — low, medium, high, critical."
    )


class BlockchainLogResponse(BaseModel):
    """Receipt returned after successfully logging an event on-chain."""

    tx_hash: str = Field(..., description="Transaction hash on the blockchain.")
    event_hash: str = Field(..., description="Keccak-256 hash of the event data.")
    block_number: int = Field(
        ..., ge=0, description="Block number that included the transaction."
    )
    timestamp: str = Field(..., description="ISO-8601 timestamp of the block.")
    status: str = Field(
        ..., description="Transaction status — confirmed, pending, failed, blockchain_unavailable."
    )


class BlockchainEventResponse(BaseModel):
    """An access event as recorded on the blockchain."""

    event_hash: str = Field(..., description="Keccak-256 hash of the event.")
    timestamp: int = Field(..., description="Unix timestamp stored on-chain.")
    user_id: str = Field(..., description="User who triggered the event.")
    action: str = Field(..., description="Database action (SELECT, EXPORT, …).")
    table_name: str = Field(..., description="Table that was accessed.")
    threat_score: int = Field(..., description="Threat score at time of logging.")
    ipfs_report_hash: str = Field(
        default="",
        description="IPFS CID of the associated threat report (if pinned).",
    )


class ThreatAlertResponse(BaseModel):
    """An on-chain threat alert."""

    alert_id: int = Field(..., description="Sequential on-chain alert identifier.")
    event_hash: str = Field(..., description="Hash of the triggering event.")
    threat_level: str = Field(..., description="Threat level that triggered the alert.")
    timestamp: int = Field(..., description="Unix timestamp of alert creation.")
    resolved: bool = Field(..., description="Whether the alert has been resolved.")
    responder_address: str = Field(
        default="",
        description="Ethereum address of the responder who resolved the alert.",
    )


class DashboardStats(BaseModel):
    """Aggregated statistics for the front-end dashboard."""

    total_events: int = Field(default=0, description="Total events analysed.")
    total_alerts: int = Field(default=0, description="Total alerts generated.")
    unresolved_alerts: int = Field(default=0, description="Currently open alerts.")
    critical_events_24h: int = Field(
        default=0, description="Critical events in the last 24 hours."
    )
    avg_threat_score: float = Field(
        default=0.0, description="Average threat score across all events."
    )
    events_by_level: Dict[str, int] = Field(
        default_factory=lambda: {
            "low": 0,
            "medium": 0,
            "high": 0,
            "critical": 0,
        },
        description="Event counts grouped by threat level.",
    )
    recent_events: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Most recent events for the activity feed.",
    )


class HealthResponse(BaseModel):
    """System health check response."""

    status: str = Field(..., description="Overall system health — healthy, degraded, unhealthy.")
    ml_engine: str = Field(
        ..., description="ML engine status — ready, degraded, unavailable."
    )
    genai_engine: str = Field(
        ..., description="GenAI engine status — ready, degraded, unavailable."
    )
    blockchain: str = Field(
        ..., description="Blockchain status — connected, disconnected."
    )
    timestamp: str = Field(..., description="ISO-8601 timestamp of the check.")


class AnalyzeResponse(BaseModel):
    """Composite response returned by the full analysis pipeline.

    Bundles the ML detection result, the GenAI report, and the blockchain
    log receipt into a single envelope.
    """

    event: AccessEventResponse = Field(
        ..., description="ML detection result for the event."
    )
    report: ThreatReportResponse = Field(
        ..., description="GenAI-generated threat report."
    )
    blockchain_log: Optional[BlockchainLogResponse] = Field(
        default=None,
        description="Blockchain log receipt (None if chain is unavailable).",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Report generation request body (used by /api/reports/generate)
# ──────────────────────────────────────────────────────────────────────────────

class ReportGenerateRequest(BaseModel):
    """Request body for the stand-alone report generation endpoint."""

    event_data: Dict[str, Any] = Field(
        ..., description="Dictionary of the original access event."
    )
    threat_score: float = Field(
        ..., ge=0, le=100, description="Pre-computed threat score."
    )
    threat_level: str = Field(
        ..., description="Categorical threat level — low, medium, high, critical."
    )
