"""
DataShield AI — Feature Engineering Pipeline
==============================================
Transforms raw access-log events into a numerical feature matrix suitable
for anomaly detection and behaviour analysis models.

The ``FeatureEngineer`` class exposes the standard scikit-learn-style
``fit_transform`` / ``transform`` API so that the same encoding &
scaling parameters learned on the training set are applied consistently
at inference time.

Features Extracted
------------------
1.  ``hour_of_day``         — 0-23
2.  ``is_weekend``          — 0 / 1
3.  ``is_after_hours``      — 1 if hour < 7 or hour > 20
4.  ``hour_sin``            — sin(2π · hour / 24)  (cyclical)
5.  ``hour_cos``            — cos(2π · hour / 24)  (cyclical)
6.  ``action_encoded``      — label-encoded action
7.  ``role_encoded``        — label-encoded role
8.  ``num_rows_log``        — log1p(num_rows_affected)
9.  ``num_sensitive_columns``— count of PII columns in columns_accessed
10. ``has_pii``             — 0 / 1
11. ``is_sensitive_table``  — 0 / 1
12. ``session_duration_log``— log1p(session_duration_seconds)
13. ``is_vpn``              — 0 / 1
14. ``access_velocity``     — events per hour per user (approximate)
15. ``volume_deviation``    — z-score of num_rows vs user historical mean
16. ``time_deviation``      — z-score of hour vs user mean access hour

Usage
-----
>>> from ml_engine.feature_engineering import FeatureEngineer
>>> fe = FeatureEngineer()
>>> X, y = fe.fit_transform(df)
>>> fe.save("saved_models/feature_engineer.joblib")
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from sklearn.preprocessing import LabelEncoder, StandardScaler
    import joblib
except ImportError:
    raise ImportError(
        "scikit-learn and joblib are required.  "
        "pip install scikit-learn joblib"
    )

from config import PII_COLUMNS, SENSITIVE_TABLES

# Suppress benign warnings during transform
warnings.filterwarnings("ignore", category=UserWarning)


class FeatureEngineer:
    """End-to-end feature extraction and scaling pipeline.

    Attributes
    ----------
    action_encoder : LabelEncoder
        Encoder for the ``action`` column.
    role_encoder : LabelEncoder
        Encoder for the ``user_role`` column.
    scaler : StandardScaler
        Fitted scaler for the final feature matrix.
    user_stats : dict
        Per-user historical statistics (mean rows, mean hour, event count)
        computed during ``fit_transform``.
    is_fitted : bool
        ``True`` after ``fit_transform`` has been called.
    feature_names : list[str]
        Ordered list of output feature column names.
    """

    # Canonical feature order
    FEATURE_NAMES: List[str] = [
        "hour_of_day",
        "is_weekend",
        "is_after_hours",
        "hour_sin",
        "hour_cos",
        "action_encoded",
        "role_encoded",
        "num_rows_log",
        "num_sensitive_columns",
        "has_pii",
        "is_sensitive_table",
        "session_duration_log",
        "is_vpn_flag",
        "access_velocity",
        "volume_deviation",
        "time_deviation",
    ]

    def __init__(self) -> None:
        self.action_encoder = LabelEncoder()
        self.role_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.user_stats: Dict[str, Dict[str, float]] = {}
        self.global_stats: Dict[str, float] = {
            "mean_rows": 250.0,
            "std_rows": 1500.0,
            "mean_hour": 13.0,
            "std_hour": 3.5,
            "event_count": 50.0,
            "span_hours": 24.0,
        }
        self.is_fitted: bool = False
        self.feature_names: List[str] = list(self.FEATURE_NAMES)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_timestamp(df: pd.DataFrame) -> pd.DataFrame:
        """Ensure ``timestamp`` is a proper datetime column."""
        df = df.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        return df

    @staticmethod
    def _count_pii(columns_accessed: str) -> int:
        """Count how many PII columns appear in the comma-separated list."""
        if not isinstance(columns_accessed, str) or columns_accessed.strip() == "":
            return 0
        cols = [c.strip().lower() for c in columns_accessed.split(",")]
        return sum(1 for c in cols if c in [p.lower() for p in PII_COLUMNS])

    @staticmethod
    def _is_sensitive_table(table_name: str) -> int:
        """Return 1 if ``table_name`` is in the sensitive list."""
        if not isinstance(table_name, str):
            return 0
        return int(table_name.strip().lower() in [t.lower() for t in SENSITIVE_TABLES])

    def _compute_user_stats(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Compute per-user historical aggregates used for deviation features.

        Returns a dict keyed by ``user_id`` with:
        * ``mean_rows``  — average num_rows_affected
        * ``std_rows``   — std dev of num_rows_affected
        * ``mean_hour``  — average access hour
        * ``std_hour``   — std dev of access hour
        * ``event_count``— total events for this user
        * ``span_hours`` — time span of all events in hours (min 1)
        """
        stats: Dict[str, Dict[str, float]] = {}
        for uid, grp in df.groupby("user_id"):
            hours = grp["timestamp"].dt.hour
            span = (grp["timestamp"].max() - grp["timestamp"].min()).total_seconds() / 3600.0
            span = max(span, 1.0)  # avoid division by zero
            stats[str(uid)] = {
                "mean_rows": float(grp["num_rows_affected"].mean()),
                "std_rows": float(grp["num_rows_affected"].std(ddof=0)) or 1.0,
                "mean_hour": float(hours.mean()),
                "std_hour": float(hours.std(ddof=0)) or 1.0,
                "event_count": float(len(grp)),
                "span_hours": span,
            }
        # Compute global baseline fallback stats
        hours = df["timestamp"].dt.hour
        span = (df["timestamp"].max() - df["timestamp"].min()).total_seconds() / 3600.0
        self.global_stats = {
            "mean_rows": float(df["num_rows_affected"].mean()),
            "std_rows": float(df["num_rows_affected"].std(ddof=0)) or 500.0,
            "mean_hour": float(hours.mean()),
            "std_hour": float(hours.std(ddof=0)) or 3.5,
            "event_count": float(len(df) / max(1, df["user_id"].nunique())),
            "span_hours": max(span, 24.0),
        }
        return stats

    def _extract_raw_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Build the raw (unscaled) feature dataframe."""
        df = self._parse_timestamp(df)

        feats = pd.DataFrame(index=df.index)

        # 1. Hour of day
        feats["hour_of_day"] = df["timestamp"].dt.hour

        # 2. Weekend flag
        feats["is_weekend"] = (df["timestamp"].dt.weekday >= 5).astype(int)

        # 3. After-hours flag (before 7 AM or after 8 PM)
        feats["is_after_hours"] = (
            (feats["hour_of_day"] < 7) | (feats["hour_of_day"] > 20)
        ).astype(int)

        # 4-5. Cyclical hour encoding
        feats["hour_sin"] = np.sin(2 * np.pi * feats["hour_of_day"] / 24.0)
        feats["hour_cos"] = np.cos(2 * np.pi * feats["hour_of_day"] / 24.0)

        # 6. Action encoded
        try:
            feats["action_encoded"] = self.action_encoder.transform(df["action"])
        except ValueError:
            # Unseen labels at inference → map to -1
            feats["action_encoded"] = df["action"].apply(
                lambda x: self.action_encoder.transform([x])[0]
                if x in self.action_encoder.classes_
                else -1
            )

        # 7. Role encoded
        try:
            feats["role_encoded"] = self.role_encoder.transform(df["user_role"])
        except ValueError:
            feats["role_encoded"] = df["user_role"].apply(
                lambda x: self.role_encoder.transform([x])[0]
                if x in self.role_encoder.classes_
                else -1
            )

        # 8. Log-transformed row count
        feats["num_rows_log"] = np.log1p(df["num_rows_affected"].astype(float))

        # 9-10. PII column features
        feats["num_sensitive_columns"] = df["columns_accessed"].apply(self._count_pii)
        feats["has_pii"] = (feats["num_sensitive_columns"] > 0).astype(int)

        # 11. Sensitive table flag
        feats["is_sensitive_table"] = df["table_name"].apply(self._is_sensitive_table)

        # 12. Log-transformed session duration
        feats["session_duration_log"] = np.log1p(
            df["session_duration_seconds"].astype(float)
        )

        # 13. VPN flag
        feats["is_vpn_flag"] = df["is_vpn"].astype(int)

        # Safe helper for user stats lookup with global fallback
        def _get_stat(uid: str, key: str, fallback: float) -> float:
            if uid in self.user_stats and key in self.user_stats[uid]:
                return self.user_stats[uid][key]
            if hasattr(self, "global_stats") and key in self.global_stats:
                return self.global_stats[key]
            return fallback

        # 14. Access velocity (events / hour for this user)
        feats["access_velocity"] = df["user_id"].apply(
            lambda uid: _get_stat(str(uid), "event_count", 5.0)
            / max(1.0, _get_stat(str(uid), "span_hours", 24.0))
        )

        # 15. Volume deviation (z-score of num_rows vs user mean)
        feats["volume_deviation"] = df.apply(
            lambda row: np.clip(
                (float(row["num_rows_affected"]) - _get_stat(str(row["user_id"]), "mean_rows", 250.0))
                / max(10.0, _get_stat(str(row["user_id"]), "std_rows", 500.0)),
                -3.0,
                15.0,
            ),
            axis=1,
        )

        # 16. Time deviation (z-score of hour vs user mean hour)
        hours_series = df["timestamp"].dt.hour.astype(float)
        feats["time_deviation"] = [
            np.clip(
                (float(h) - _get_stat(str(uid), "mean_hour", 13.0))
                / max(1.0, _get_stat(str(uid), "std_hour", 3.5)),
                -4.0,
                4.0,
            )
            for h, uid in zip(hours_series, df["user_id"])
        ]

        # Replace infinities and NaNs
        feats.replace([np.inf, -np.inf], 0.0, inplace=True)
        feats.fillna(0.0, inplace=True)

        return feats

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fit_transform(
        self, df: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Fit encoders/scaler on ``df`` and return (X, y).

        Parameters
        ----------
        df : pd.DataFrame
            Raw access-log DataFrame (as produced by ``data_generator``).

        Returns
        -------
        X : np.ndarray, shape (n_samples, n_features)
            Scaled feature matrix.
        y : np.ndarray, shape (n_samples,)
            Binary labels (1 = anomalous, 0 = normal).
        """
        df = self._parse_timestamp(df)

        # Fit label encoders
        self.action_encoder.fit(df["action"])
        self.role_encoder.fit(df["user_role"])

        # Compute per-user statistics
        self.user_stats = self._compute_user_stats(df)

        # Extract raw features
        feats = self._extract_raw_features(df)

        # Fit scaler
        X = self.scaler.fit_transform(feats.values.astype(np.float64))
        y = df["is_anomalous"].astype(int).values

        self.is_fitted = True
        print(f"[FeatureEngineer] fit_transform complete — "
              f"{X.shape[0]} samples × {X.shape[1]} features")
        return X, y

    def transform(self, df: pd.DataFrame) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Transform new data using previously fitted encoders/scaler.

        Parameters
        ----------
        df : pd.DataFrame
            Raw access-log DataFrame.

        Returns
        -------
        X : np.ndarray
            Scaled feature matrix.
        y : np.ndarray | None
            Labels if ``is_anomalous`` column is present, else ``None``.
        """
        if not self.is_fitted:
            raise RuntimeError(
                "FeatureEngineer has not been fitted yet. Call fit_transform first."
            )

        df = self._parse_timestamp(df)
        feats = self._extract_raw_features(df)
        X = self.scaler.transform(feats.values.astype(np.float64))

        y = None
        if "is_anomalous" in df.columns:
            y = df["is_anomalous"].astype(int).values

        print(f"[FeatureEngineer] transform complete — "
              f"{X.shape[0]} samples × {X.shape[1]} features")
        return X, y

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> Path:
        """Persist the fitted FeatureEngineer to disk.

        Parameters
        ----------
        path : str | Path
            Destination file (e.g. ``saved_models/feature_engineer.joblib``).

        Returns
        -------
        Path
            Resolved path to the saved file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(
            {
                "action_encoder": self.action_encoder,
                "role_encoder": self.role_encoder,
                "scaler": self.scaler,
                "user_stats": self.user_stats,
                "global_stats": getattr(self, "global_stats", {}),
                "feature_names": self.feature_names,
            },
            path,
        )
        print(f"[FeatureEngineer] Saved → {path}")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "FeatureEngineer":
        """Load a previously saved FeatureEngineer.

        Parameters
        ----------
        path : str | Path
            Path to the ``.joblib`` file.

        Returns
        -------
        FeatureEngineer
            Restored instance ready for ``.transform()`` calls.
        """
        data = joblib.load(path)
        fe = cls()
        fe.action_encoder = data["action_encoder"]
        fe.role_encoder = data["role_encoder"]
        fe.scaler = data["scaler"]
        fe.user_stats = data["user_stats"]
        fe.global_stats = data.get("global_stats", {
            "mean_rows": 250.0,
            "std_rows": 1500.0,
            "mean_hour": 13.0,
            "std_hour": 3.5,
            "event_count": 50.0,
            "span_hours": 24.0,
        })
        fe.feature_names = data["feature_names"]
        fe.is_fitted = True
        print(f"[FeatureEngineer] Loaded <- {path}")
        return fe


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from ml_engine.data_generator import generate_dataset

    df = generate_dataset(n_normal=500, n_anomalous=50)
    fe = FeatureEngineer()
    X, y = fe.fit_transform(df)
    print(f"X shape: {X.shape}  y shape: {y.shape}")
    print(f"Feature names: {fe.feature_names}")
    print(f"Anomaly rate: {y.mean():.2%}")
