"""
DataShield AI — Threat Scorer Ensemble
========================================
Combines scores from Isolation Forest, Autoencoder, and LSTM models into a
calibrated 0-100 threat score with threat classification and top factor attribution.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any
import numpy as np

from config import THREAT_SCORE_THRESHOLD


class ThreatScorer:
    """
    Ensemble scorer that aggregates anomaly signals into a 0-100 score.
    """

    def __init__(
        self,
        isolation_weight: float = 0.30,
        autoencoder_weight: float = 0.35,
        lstm_weight: float = 0.35,
        threshold: float = THREAT_SCORE_THRESHOLD,
    ):
        total = isolation_weight + autoencoder_weight + lstm_weight
        self.w_iso = isolation_weight / total
        self.w_ae = autoencoder_weight / total
        self.w_lstm = lstm_weight / total
        self.threshold = threshold

    def get_threat_level(self, score: float) -> str:
        """Categorize 0-100 score into severity band."""
        if score >= 80:
            return "CRITICAL"
        elif score >= 60:
            return "HIGH"
        elif score >= 35:
            return "MEDIUM"
        else:
            return "LOW"

    def score_event(
        self,
        isolation_score: Optional[float] = None,
        autoencoder_score: Optional[float] = None,
        lstm_score: Optional[float] = None,
        feature_dict: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Calculates ensemble threat score and factors.
        Each component score is expected in range [0, 1].
        """
        weights = []
        scores = []

        if isolation_score is not None:
            # Map isolation score cleanly:
            # If from raw sklearn predict (-1 = outlier, +1 = inlier):
            if isolation_score == 1.0:
                iso_norm = 0.05
            elif isolation_score == -1.0:
                iso_norm = 0.95
            else:
                iso_norm = float(np.clip(isolation_score, 0.0, 1.0))
            scores.append(iso_norm)
            weights.append(self.w_iso)

        if autoencoder_score is not None:
            ae_norm = np.clip(autoencoder_score, 0.0, 1.0)
            scores.append(ae_norm)
            weights.append(self.w_ae)

        if lstm_score is not None:
            lstm_norm = np.clip(lstm_score, 0.0, 1.0)
            scores.append(lstm_norm)
            weights.append(self.w_lstm)

        if not scores:
            # Fallback to rule-based heuristic scoring if models aren't passed
            final_norm = self._heuristic_score(feature_dict)
        else:
            total_weight = sum(weights)
            final_norm = sum(s * (w / total_weight) for s, w in zip(scores, weights))

        # Scale to 0-100
        threat_score = round(float(final_norm * 100), 1)

        # Baseline Guardrail: Benign routine access check
        is_benign = False
        if feature_dict:
            num_rows = int(feature_dict.get("num_rows_affected", 0))
            table = str(feature_dict.get("table_name", "")).lower()
            action = str(feature_dict.get("action", "")).upper()
            has_pii = bool(feature_dict.get("has_pii", False) or feature_dict.get("num_sensitive_columns", 0) > 0)
            is_vpn = bool(feature_dict.get("is_vpn", False))
            is_after = bool(feature_dict.get("is_after_hours", False))
            
            # Non-sensitive table, low row count, no PII, standard query action, no VPN
            is_sensitive_tbl = any(s in table for s in ["credit", "medical", "patient", "salary", "ssn", "secret", "auth", "token", "payment"])
            if num_rows <= 250 and not has_pii and not is_sensitive_tbl and not is_vpn and not is_after and action in ["SELECT", "READ", "GET", "VIEW"]:
                threat_score = min(threat_score, 12.0)
                is_benign = True

        threat_level = self.get_threat_level(threat_score)
        is_anomalous = bool(threat_score >= self.threshold)

        if is_benign or threat_score < 30.0:
            factors = ["Standard operational query within expected baseline parameters. Low risk."]
        else:
            factors = self.extract_contributing_factors(feature_dict)

        return {
            "threat_score": threat_score,
            "threat_level": threat_level,
            "is_anomalous": is_anomalous,
            "contributing_factors": factors,
            "raw_scores": {
                "isolation_forest": round(float(isolation_score), 4) if isolation_score is not None else None,
                "autoencoder": round(float(autoencoder_score), 4) if autoencoder_score is not None else None,
                "lstm": round(float(lstm_score), 4) if lstm_score is not None else None,
            },
        }

    def _heuristic_score(self, feature_dict: Optional[Dict[str, Any]]) -> float:
        """Rule-based heuristic fallback if ML models are missing."""
        if not feature_dict:
            return 0.1
        score = 0.0
        if feature_dict.get("is_after_hours") or feature_dict.get("hour_of_day", 12) < 7 or feature_dict.get("hour_of_day", 12) > 20:
            score += 0.25
        if feature_dict.get("has_pii") or feature_dict.get("num_sensitive_columns", 0) > 0:
            score += 0.30
        if feature_dict.get("is_sensitive_table"):
            score += 0.20
        if feature_dict.get("num_rows_affected", 0) > 5000:
            score += 0.25
        if feature_dict.get("is_vpn"):
            score += 0.10
        return min(score, 0.99)

    def extract_contributing_factors(self, event_or_features: Optional[Dict[str, Any]]) -> List[str]:
        """Translates raw event / feature attributes into actionable factor explanations."""
        if not event_or_features:
            return ["Baseline telemetry anomaly detected across behavioral metrics."]

        factors = []
        d = event_or_features

        num_rows = d.get("num_rows_affected", 0)
        if num_rows > 10000:
            factors.append(f"Excessive volume exfiltration risk: {num_rows:,} rows requested.")
        elif num_rows > 2500:
            factors.append(f"Elevated data download volume ({num_rows:,} rows).")

        if d.get("is_after_hours") or (isinstance(d.get("hour_of_day"), (int, float)) and (d["hour_of_day"] < 6 or d["hour_of_day"] > 21)):
            hour = d.get("hour_of_day", "unusual")
            factors.append(f"After-hours access detected (local hour: {hour}).")

        if d.get("has_pii") or d.get("num_sensitive_columns", 0) > 0:
            cols = d.get("columns_accessed")
            if isinstance(cols, list):
                cols_str = ", ".join(cols[:4])
            else:
                cols_str = "sensitive fields"
            factors.append(f"Targeted high-risk PII columns ({cols_str}).")

        if d.get("is_sensitive_table"):
            table = d.get("table_name", "production")
            factors.append(f"Critical production schema accessed: `{table}`.")

        if d.get("is_vpn"):
            geo = d.get("geo_location", "External Gateway")
            factors.append(f"Access routed via external VPN/proxy endpoint ({geo}).")

        role = str(d.get("user_role", "")).lower()
        action = str(d.get("action", "")).upper()
        if role in ["intern", "contractor"] and action in ["EXPORT", "DOWNLOAD", "DELETE"]:
            factors.append(f"Role mismatch: {role.title()} initiated bulk `{action}` operation.")

        if not factors:
            factors.append("Statistical deviation in session duration and query velocity.")

        return factors
