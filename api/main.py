"""
DataShield AI — Unified FastAPI Server
========================================
Integrates ML Anomaly Detection (Layer 1), GenAI Explainability (Layer 2),
and Blockchain Audit Verification (Layer 3) into an enterprise REST API.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config import API_HOST, API_PORT, CORS_ORIGINS
from api.services.detection_service import DetectionService
from api.services.report_service import ReportService
from api.services.blockchain_service import BlockchainService
from api.routes import threats, reports, blockchain

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("datashield.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler initializing backend security services."""
    logger.info("Initializing DataShield AI enterprise services...")
    
    # 1. Initialize ML Detection Engine
    app.state.detection_service = DetectionService()
    
    # 2. Initialize GenAI Explainer & RAG Pipeline
    app.state.report_service = ReportService()
    
    # 3. Initialize Blockchain Audit Client
    app.state.blockchain_service = BlockchainService()

    # In-memory recent events list for live dashboards
    app.state.recent_events = []

    logger.info("✓ DataShield AI services successfully loaded.")
    yield
    logger.info("Shutting down DataShield AI services.")


app = FastAPI(
    title="DataShield AI — Enterprise Data Breach Defense Platform",
    description="Explainable, Threat-Proof, and Traceable Data Security leveraging ML, GenAI, and Blockchain.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(threats.router)
app.include_router(reports.router)
app.include_router(blockchain.router)


@app.get("/", tags=["General"])
async def root():
    return {
        "platform": "DataShield AI",
        "version": "1.0.0",
        "status": "operational",
        "description": "Blockchain + ML + GenAI Powered Data Breach Prevention & Forensics Platform",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "threat_analysis": "/api/threats/analyze",
            "blockchain_events": "/api/blockchain/events",
        },
    }


@app.get("/health", tags=["General"])
async def health_check():
    det_status = app.state.detection_service.get_model_status() if hasattr(app.state, "detection_service") else {}
    rep_status = app.state.report_service.get_service_status() if hasattr(app.state, "report_service") else {}
    bc_status = app.state.blockchain_service.get_service_status() if hasattr(app.state, "blockchain_service") else {}

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ml_engine": det_status,
        "genai_engine": rep_status,
        "blockchain": bc_status,
    }


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=API_HOST,
        port=API_PORT,
        reload=True,
    )
