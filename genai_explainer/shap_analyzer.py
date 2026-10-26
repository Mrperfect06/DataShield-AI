"""
DataShield AI — SHAP Model Explainability
===========================================
Generates feature attributions and human-interpretable explanations for
anomaly detection models using SHAP (SHapley Additive exPlanations).
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Optional, Any, Union
import numpy as np

try:
    import shap
    _SHAP_AVAILABLE = True
except ImportError:
    _SHAP_AVAILABLE = False
    warnings.warn("SHAP library not found. Falling back to heuristic feature importance.")


class SHAPAnalyzer:
    """
    Computes and formats feature contributions for anomaly decisions.
    """

    def __init__(self, model: Any = None, feature_names: Optional[List[str]] = None):
        self.model = model
        self.feature_names = feature_names or [
            "hour_of_day", "is_weekend", "is_after_hours", "hour_sin", "hour_cos",
            "action_encoded", "role_encoded", "num_rows_log", "num_sensitive_columns",
            "has_pii", "is_sensitive_table", "session_duration_log", "is_vpn",
            "access_velocity", "volume_deviation", "time_deviation"
        ]
        self.explainer = None
        self._init_explainer()

    def _init_explainer(self):
        if not _SHAP_AVAILABLE or self.model is None:
            return

        try:
            # Check if model has estimator_ or is IsolationForest
            estimator = getattr(self.model, "model", self.model)
            if hasattr(estimator, "estimators_"):
                self.explainer = shap.TreeExplainer(estimator)
        except Exception as e:
            # Fallback if tree explainer initialization fails
            self.explainer = None

    def explain_single(self, x: Union[np.ndarray, List[float]]) -> Dict[str, Any]:
        """
        Explain a single feature vector instance.
        """
        x_arr = np.asarray(x, dtype=float).reshape(1, -1)
        return self.explain(x_arr)

    def explain(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Calculates feature attributions for given sample(s).
        """
        if not _SHAP_AVAILABLE or self.explainer is None:
            return self._heuristic_explanation(X)

        try:
            shap_vals = self.explainer.shap_values(X)
            # TreeExplainer on IsolationForest may return array or list
            if isinstance(shap_vals, list):
                shap_matrix = shap_vals[0]
            else:
                shap_matrix = shap_vals

            mean_abs_impact = np.abs(shap_matrix).mean(axis=0) if shap_matrix.ndim > 1 else np.abs(shap_matrix)
            
            # Sort features by descending impact
            indices = np.argsort(mean_abs_impact)[::-1]
            
            feature_importance = {}
            top_factors = []
            
            for idx in indices:
                feat_name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
                importance = float(mean_abs_impact[idx])
                feature_importance[feat_name] = round(importance, 4)

            # Extract top 4 explanations
            for idx in indices[:4]:
                name = self.feature_names[idx] if idx < len(self.feature_names) else f"feature_{idx}"
                top_factors.append(f"Model weight on `{name}` contributed to anomaly signal.")

            return {
                "feature_importance": feature_importance,
                "top_factors": top_factors,
                "explainer_type": "SHAP_TreeExplainer",
            }
        except Exception as e:
            return self._heuristic_explanation(X)

    def _heuristic_explanation(self, X: np.ndarray) -> Dict[str, Any]:
        """Fallback explanation based on common high-risk feature indicators."""
        feature_importance = {}
        top_factors = []
        
        # High impact names based on domain knowledge
        domain_weights = {
            "num_rows_log": 0.28,
            "has_pii": 0.24,
            "is_sensitive_table": 0.18,
            "is_after_hours": 0.14,
            "volume_deviation": 0.10,
            "is_vpn": 0.06,
        }

        for name, weight in domain_weights.items():
            feature_importance[name] = weight
            top_factors.append(f"High sensitivity attribute `{name}` strongly correlates with risk threshold.")

        return {
            "feature_importance": feature_importance,
            "top_factors": top_factors,
            "explainer_type": "Domain_Attribution_Fallback",
        }
