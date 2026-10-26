"""
DataShield AI — ML Detection Service
======================================
Orchestrates anomaly detection by loading trained models from disk
(IsolationForest, Autoencoder, LSTM) and the fitted FeatureEngineer.

If no trained models are available on disk the service falls back to a
deterministic, rule-based mock scorer so the API always returns a
useful response even before any model training has taken place.

Usage (inside FastAPI)
----------------------
>>> svc = DetectionService()
>>> result = svc.analyze_event(event_dict)
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from config import (
    MODELS_DIR,
    PII_COLUMNS,
    SENSITIVE_TABLES,
    THREAT_SCORE_THRESHOLD,
)
from honeytokens.honeytoken_manager import HoneyTokenManager

logger = logging.getLogger("datashield.detection")

# ---------------------------------------------------------------------------
# Try to import ML components — all are optional at runtime
# ---------------------------------------------------------------------------

_joblib_available = False
try:
    import joblib
    _joblib_available = True
except ImportError:
    logger.warning("joblib not installed — model loading disabled.")

_fe_class = None
try:
    from ml_engine.feature_engineering import FeatureEngineer
    _fe_class = FeatureEngineer
except ImportError:
    logger.warning("ml_engine.feature_engineering unavailable.")

_iso_class = None
try:
    from ml_engine.anomaly_detector import IsolationForestDetector
    _iso_class = IsolationForestDetector
except ImportError:
    logger.info("IsolationForestDetector not importable — will use mock scores.")

_ae_class = None
try:
    from ml_engine.anomaly_detector import AutoencoderDetector
    _ae_class = AutoencoderDetector
except ImportError:
    logger.info("AutoencoderDetector not importable — will use mock scores.")

_lstm_class = None
try:
    from ml_engine.behavior_analyzer import BehaviorAnalyzer
    _lstm_class = BehaviorAnalyzer
except ImportError:
    logger.info("BehaviorAnalyzer not importable — will use mock scores.")

_threat_scorer_class = None
try:
    from ml_engine.threat_scorer import ThreatScorer
    _threat_scorer_class = ThreatScorer
except ImportError:
    logger.info("ThreatScorer not importable — will use mock scorer.")


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class DetectionService:
    """Loads trained ML artefacts and exposes a single ``analyze_event`` API.

    Attributes
    ----------
    feature_engineer : FeatureEngineer | None
        Fitted feature transformer (loaded from ``saved_models/``).
    iso_detector : IsolationForestDetector | None
        Trained Isolation Forest model.
    ae_detector : AutoencoderDetector | None
        Trained Autoencoder model.
    lstm_detector : BehaviorAnalyzer | None
        Trained LSTM behavioural model.
    threat_scorer : ThreatScorer | None
        Composite threat scoring component.
    models_loaded : dict[str, bool]
        Quick lookup of which models were successfully loaded.
    """

    def __init__(self) -> None:
        """Initialise the service, attempting to load every model from disk."""
        self.feature_engineer: Optional[Any] = None
        self.iso_detector: Optional[Any] = None
        self.ae_detector: Optional[Any] = None
        self.lstm_detector: Optional[Any] = None
        self.threat_scorer: Optional[Any] = None

        self.models_loaded: Dict[str, bool] = {
            "feature_engineer": False,
            "isolation_forest": False,
            "autoencoder": False,
            "lstm_behaviour": False,
            "threat_scorer": False,
        }

        self.honeytoken_mgr = HoneyTokenManager()
        self._load_models()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_models(self) -> None:
        """Best-effort loading of all ML artefacts.

        Each model is loaded independently so that a failure in one
        does not prevent the others from being used.
        """
        models_dir = Path(MODELS_DIR)

        # 1. Feature Engineer
        fe_path = models_dir / "feature_engineer.joblib"
        if fe_path.exists() and _fe_class is not None:
            try:
                self.feature_engineer = _fe_class.load(fe_path)
                self.models_loaded["feature_engineer"] = True
                logger.info("FeatureEngineer loaded from %s", fe_path)
            except Exception as exc:
                logger.error("Failed to load FeatureEngineer: %s", exc)
        else:
            logger.warning(
                "FeatureEngineer artefact not found at %s — using mock scoring.",
                fe_path,
            )

        # 2. Isolation Forest
        iso_path = models_dir / "isolation_forest.joblib"
        if iso_path.exists() and _joblib_available:
            try:
                self.iso_detector = joblib.load(iso_path)
                self.models_loaded["isolation_forest"] = True
                logger.info("IsolationForest loaded from %s", iso_path)
            except Exception as exc:
                logger.error("Failed to load IsolationForest: %s", exc)

        # 3. Autoencoder
        ae_path = models_dir / "autoencoder.pt"
        if ae_path.exists() and _ae_class is not None:
            try:
                self.ae_detector = _ae_class.load(str(ae_path))
                self.models_loaded["autoencoder"] = True
                logger.info("Autoencoder loaded from %s", ae_path)
            except Exception as exc:
                logger.error("Failed to load Autoencoder: %s", exc)

        # 4. LSTM Behaviour Analyzer
        lstm_path = models_dir / "behavior_analyzer.pt"
        if not lstm_path.exists():
            lstm_path = models_dir / "behavior_lstm.pt"
        if lstm_path.exists() and _lstm_class is not None:
            try:
                self.lstm_detector = _lstm_class.load(str(lstm_path))
                self.models_loaded["lstm_behaviour"] = True
                logger.info("LSTM BehaviorAnalyzer loaded from %s", lstm_path)
            except Exception as exc:
                logger.error("Failed to load BehaviorAnalyzer: %s", exc)

        # 5. Threat Scorer (stateless — just needs the class)
        if _threat_scorer_class is not None:
            try:
                self.threat_scorer = _threat_scorer_class()
                self.models_loaded["threat_scorer"] = True
                logger.info("ThreatScorer initialised.")
            except Exception as exc:
                logger.error("Failed to init ThreatScorer: %s", exc)

        loaded = sum(self.models_loaded.values())
        total = len(self.models_loaded)
        logger.info(
            "DetectionService ready — %d/%d models loaded. "
            "Mock scoring %s.",
            loaded,
            total,
            "disabled" if loaded == total else "enabled for missing models",
        )

    # ------------------------------------------------------------------
    # Feature preparation
    # ------------------------------------------------------------------

    def _prepare_features(self, event: Dict[str, Any]) -> Optional[np.ndarray]:
        """Convert a single event dict into a scaled feature vector.

        Parameters
        ----------
        event : dict
            Raw access-event dictionary (same keys as ``AccessEventInput``).

        Returns
        -------
        np.ndarray | None
            1-D scaled feature vector, or ``None`` if the feature engineer
            is not available.
        """
        if self.feature_engineer is None or not self.feature_engineer.is_fitted:
            return None

        try:
            # Build a single-row DataFrame matching the training schema
            row = {
                "timestamp": datetime.now(timezone.utc),
                "user_id": event.get("user_id", "unknown"),
                "user_email": event.get("user_email", ""),
                "user_role": event.get("user_role", "analyst"),
                "department": event.get("department", "Unknown"),
                "action": event.get("action", "SELECT"),
                "table_name": event.get("table_name", "public.unknown"),
                "columns_accessed": ",".join(event.get("columns_accessed", [])),
                "num_rows_affected": int(event.get("num_rows_affected", 0)),
                "source_ip": event.get("source_ip", "0.0.0.0"),
                "geo_location": event.get("geo_location", "Unknown"),
                "session_duration_seconds": int(
                    event.get("session_duration_seconds", 0)
                ),
                "is_vpn": bool(event.get("is_vpn", False)),
            }

            df = pd.DataFrame([row])
            X, _ = self.feature_engineer.transform(df)
            return X[0]  # single sample
        except Exception as exc:
            logger.error("Feature preparation failed: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Mock (rule-based) scorer
    # ------------------------------------------------------------------

    @staticmethod
    def _get_mock_score(event: Dict[str, Any]) -> Dict[str, Any]:
        """Deterministic, rule-based fallback scorer.

        Returns a dict with the same structure as the real pipeline output
        so that calling code does not need to distinguish between the two.

        Heuristic rules
        ---------------
        +20  after-hours access (hour < 7 or hour > 20)
        +25  PII column access
        +20  bulk download / export (>10 000 rows)
        +10  VPN usage
        +15  role deviation (intern/contractor on sensitive table)

        The score is capped at 100.

        Parameters
        ----------
        event : dict
            Raw access-event dictionary.

        Returns
        -------
        dict
            Keys: threat_score, threat_level, is_anomalous,
            contributing_factors, raw_scores.
        """
        score = 0
        factors: List[str] = []

        # ── After-hours ─────────────────────────────────────────────────
        # Check event payload first, fallback to timestamp if provided
        if event.get("is_after_hours", False):
            score += 20
            factors.append("after_hours_access")

        # ── PII column access ───────────────────────────────────────────
        cols = event.get("columns_accessed", [])
        if isinstance(cols, str):
            cols = [c.strip() for c in cols.split(",") if c.strip()]
        pii_found = [c for c in cols if c.lower() in [p.lower() for p in PII_COLUMNS]]
        if pii_found:
            score += 25
            factors.append(f"pii_columns_accessed ({', '.join(pii_found)})")

        # ── Bulk download / export ──────────────────────────────────────
        num_rows = int(event.get("num_rows_affected", 0))
        action = str(event.get("action", "")).upper()
        if num_rows > 10_000 or action in ("EXPORT", "DOWNLOAD"):
            score += 20
            factors.append("bulk_data_access")

        # ── VPN usage ───────────────────────────────────────────────────
        if event.get("is_vpn", False):
            score += 10
            factors.append("vpn_connection")

        # ── Role deviation ──────────────────────────────────────────────
        role = str(event.get("user_role", "")).lower()
        table = str(event.get("table_name", "")).lower()
        if role in ("intern", "contractor") and table in [
            t.lower() for t in SENSITIVE_TABLES
        ]:
            score += 15
            factors.append("role_deviation")

        # ── Sensitive table access ──────────────────────────────────────
        if table in [t.lower() for t in SENSITIVE_TABLES]:
            score += 10
            factors.append("sensitive_table_access")

        # Cap at 100
        score = min(score, 100)

        # Derive level
        if score >= 80:
            level = "critical"
        elif score >= 60:
            level = "high"
        elif score >= 40:
            level = "medium"
        else:
            level = "low"

        return {
            "threat_score": float(score),
            "threat_level": level,
            "is_anomalous": score >= THREAT_SCORE_THRESHOLD,
            "contributing_factors": factors,
            "raw_scores": {
                "isolation_forest": None,
                "autoencoder": None,
                "lstm": None,
                "mock": score,
            },
        }

    # ------------------------------------------------------------------
    # Main analysis entry-point
    # ------------------------------------------------------------------

    def analyze_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Run full ML pipeline on a single event.

        Falls back to mock scoring when any model is unavailable.

        Parameters
        ----------
        event : dict
            Raw access-event dictionary with the fields defined in
            ``AccessEventInput``.

        Returns
        -------
        dict
            Keys:
            - ``event_id``            — str
            - ``timestamp``           — ISO-8601 str
            - ``threat_score``        — float 0-100
            - ``threat_level``        — str
            - ``is_anomalous``        — bool
            - ``contributing_factors``— list[str]
            - ``raw_scores``          — dict
            - ``features``            — np.ndarray | None
        """
        event_id = event.get("event_id") or str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        # Attempt real ML pipeline
        features = self._prepare_features(event)
        use_ml = (
            features is not None
            and self.iso_detector is not None
            and self.threat_scorer is not None
        )

        if use_ml:
            try:
                # Individual model scores with calibrated mapping (0 = normal, 1 = anomaly)
                if hasattr(self.iso_detector, "decision_function"):
                    raw_dec = float(self.iso_detector.decision_function(features.reshape(1, -1))[0])
                    # In sklearn: raw_dec > 0 is inlier (normal), raw_dec < 0 is outlier (anomaly)
                    # Maps ~ +0.15 -> 0.05, ~ -0.15 -> 0.95
                    iso_score = float(np.clip(0.5 - raw_dec * 2.5, 0.0, 1.0))
                else:
                    pred = float(self.iso_detector.predict(features.reshape(1, -1))[0])
                    iso_score = 0.05 if pred == 1.0 else 0.95

                ae_score = 0.0
                if self.ae_detector is not None:
                    ae_score = float(
                        self.ae_detector.predict(features.reshape(1, -1))[0]
                    )
                lstm_score = 0.0
                if self.lstm_detector is not None:
                    # Construct pseudo-sequence of length 10 by repeating the single event
                    seq = np.repeat(features.reshape(1, 1, -1), 10, axis=1)
                    lstm_score = float(self.lstm_detector.predict(seq)[0])

                # Composite scoring
                result = self.threat_scorer.score_event(
                    isolation_score=iso_score,
                    autoencoder_score=ae_score,
                    lstm_score=lstm_score,
                    feature_dict=event,
                )
                threat_score = result.get("threat_score", result.get("score", 50.0))
                threat_level = result.get("threat_level", result.get("level", "MEDIUM"))
                factors = result.get("contributing_factors", result.get("factors", []))

                # Check Honey Token Traps (Physical Proof of Theft)
                honey_tripped, honey_detail = self.honeytoken_mgr.inspect_event_for_honeytoken(event)
                proof_cert = None
                if honey_tripped and honey_detail:
                    threat_score = 100.0
                    threat_level = "CRITICAL"
                    token_id = honey_detail.get("token_id", "CANARY-TRAP")
                    proof_cert = self.honeytoken_mgr.generate_proof_of_theft(
                        token_id=token_id,
                        suspect_user_id=event.get("user_id", "unknown"),
                    )
                    factors = [
                        f"🪤 HONEY TOKEN TRIPPED: Accessed planted decoy asset [{token_id}] in `{honey_detail.get('target_table')}`.",
                        "CONFIRMED THEFT: Zero operational value decoy record was touched with malicious intent.",
                        f"PROOF OF THEFT: Cryptographic watermark binding {proof_cert['watermark_hash'][:16]}... generated.",
                    ] + factors

                return {
                    "event_id": event_id,
                    "timestamp": timestamp,
                    "threat_score": threat_score,
                    "threat_level": threat_level,
                    "is_anomalous": bool(threat_score >= THREAT_SCORE_THRESHOLD),
                    "contributing_factors": factors,
                    "honey_token_tripped": honey_tripped,
                    "proof_of_theft": proof_cert,
                    "raw_scores": {
                        "isolation_forest": iso_score,
                        "autoencoder": ae_score,
                        "lstm": lstm_score,
                    },
                    "features": features,
                }
            except Exception as exc:
                logger.error(
                    "ML pipeline failed for event %s, falling back to mock: %s",
                    event_id,
                    exc,
                )

        # Fallback — rule-based mock scorer
        mock = self._get_mock_score(event)
        mock["event_id"] = event_id
        mock["timestamp"] = timestamp
        mock["features"] = features  # may be None

        # Check Honey Token Traps (Physical Proof of Theft)
        honey_tripped, honey_detail = self.honeytoken_mgr.inspect_event_for_honeytoken(event)
        if honey_tripped and honey_detail:
            mock["threat_score"] = 100.0
            mock["threat_level"] = "CRITICAL"
            mock["is_anomalous"] = True
            token_id = honey_detail.get("token_id", "CANARY-TRAP")
            proof_cert = self.honeytoken_mgr.generate_proof_of_theft(
                token_id=token_id,
                suspect_user_id=event.get("user_id", "unknown"),
            )
            mock["honey_token_tripped"] = True
            mock["proof_of_theft"] = proof_cert
            mock["contributing_factors"] = [
                f"🪤 HONEY TOKEN TRIPPED: Accessed planted decoy asset [{token_id}] in `{honey_detail.get('target_table')}`.",
                "CONFIRMED THEFT: Zero operational value decoy record was touched with malicious intent.",
            ] + mock.get("contributing_factors", [])
        else:
            mock["honey_token_tripped"] = False
            mock["proof_of_theft"] = None

        return mock

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def get_model_status(self) -> Dict[str, Any]:
        """Return a summary of which models are loaded and operational.

        Returns
        -------
        dict
            Keys: ``models_loaded`` (dict[str, bool]),
            ``overall_status`` (str — ready | degraded | mock_only),
            ``models_dir`` (str).
        """
        loaded_count = sum(self.models_loaded.values())
        total = len(self.models_loaded)

        if loaded_count == total:
            status = "ready"
        elif loaded_count > 0:
            status = "degraded"
        else:
            status = "mock_only"

        return {
            "models_loaded": dict(self.models_loaded),
            "overall_status": status,
            "models_dir": str(MODELS_DIR),
            "loaded_count": loaded_count,
            "total_models": total,
        }
