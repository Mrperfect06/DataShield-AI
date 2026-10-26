"""
DataShield AI — ML Training Pipeline
======================================
Generates synthetic data, extracts features, trains models:
  1. Feature Engineering pipeline (saved as joblib)
  2. Isolation Forest (saved as joblib)
  3. PyTorch Deep Autoencoder (saved as .pt)
  4. LSTM User Behavior Analyzer (saved as .pt)
Evaluates performance and saves all artifacts to `saved_models/`.
"""

import os
import sys
from pathlib import Path

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import (
    MODELS_DIR,
    DATA_DIR,
    NUM_NORMAL_EVENTS,
    NUM_ANOMALOUS_EVENTS,
    TRAINING_EPOCHS,
    BATCH_SIZE,
    LSTM_SEQUENCE_LENGTH,
)
from ml_engine.data_generator import generate_dataset, save_dataset
from ml_engine.feature_engineering import FeatureEngineer
from ml_engine.anomaly_detector import IsolationForestDetector, AutoencoderDetector
from ml_engine.behavior_analyzer import BehaviorAnalyzer
from ml_engine.threat_scorer import ThreatScorer


def run_training_pipeline():
    print("=" * 65)
    print("🛡️  DataShield AI — Machine Learning Pipeline Training")
    print("=" * 65)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Generate Synthetic Access Log Dataset
    print(f"\n[1/5] Generating dataset ({NUM_NORMAL_EVENTS} normal, {NUM_ANOMALOUS_EVENTS} anomalous events)...")
    df = generate_dataset(n_normal=NUM_NORMAL_EVENTS, n_anomalous=NUM_ANOMALOUS_EVENTS)
    raw_data_path = DATA_DIR / "access_logs_sample.csv"
    save_dataset(df, raw_data_path)
    print(f"      ✓ Dataset saved to: {raw_data_path} (Shape: {df.shape})")

    # 2. Feature Engineering
    print("\n[2/5] Running Feature Engineering...")
    fe = FeatureEngineer()
    X, y = fe.fit_transform(df)
    fe_path = MODELS_DIR / "feature_engineer.joblib"
    fe.save(fe_path)
    print(f"      ✓ Transformed {X.shape[0]} samples into {X.shape[1]} features.")
    print(f"      ✓ Feature pipeline saved to: {fe_path}")

    # 3. Train Isolation Forest
    print("\n[3/5] Training Isolation Forest...")
    # Train primarily on normal data if available, or entire mix
    normal_mask = (y == 0)
    X_train_norm = X[normal_mask] if np.sum(normal_mask) > 100 else X
    
    iso_detector = IsolationForestDetector()
    iso_detector.fit(X_train_norm)
    iso_path = MODELS_DIR / "isolation_forest.joblib"
    iso_detector.save(iso_path)
    iso_scores = iso_detector.predict(X)
    print(f"      ✓ Isolation Forest saved to: {iso_path}")
    print(f"      ✓ Mean score on normal: {np.mean(iso_scores[normal_mask]):.3f} | on anomalies: {np.mean(iso_scores[~normal_mask]):.3f}")

    # 4. Train PyTorch Autoencoder
    print("\n[4/5] Training PyTorch Autoencoder...")
    ae_detector = AutoencoderDetector(input_dim=X.shape[1])
    try:
        ae_detector.fit(X_train_norm, epochs=min(TRAINING_EPOCHS, 15), batch_size=BATCH_SIZE)
        ae_path = MODELS_DIR / "autoencoder.pt"
        ae_detector.save(ae_path)
        ae_scores = ae_detector.predict(X)
        print(f"      ✓ Autoencoder saved to: {ae_path}")
        print(f"      ✓ Mean recon error on normal: {np.mean(ae_scores[normal_mask]):.4f} | on anomalies: {np.mean(ae_scores[~normal_mask]):.4f}")
    except Exception as e:
        print(f"      ⚠️ Autoencoder training skipped or failed: {e}")
        ae_scores = np.zeros(len(X))

    # 5. Train LSTM User Behavior Analyzer
    print("\n[5/5] Training LSTM User Behavior Analyzer...")
    behavior_analyzer = BehaviorAnalyzer(input_dim=X.shape[1])
    try:
        X_seq, y_seq = behavior_analyzer.build_sequences(
            df=df,
            feature_matrix=X,
            labels=y,
            seq_length=LSTM_SEQUENCE_LENGTH,
        )
        if len(X_seq) > 0:
            behavior_analyzer.fit(X_seq, y_seq, epochs=min(TRAINING_EPOCHS, 10), batch_size=BATCH_SIZE)
            lstm_path = MODELS_DIR / "behavior_lstm.pt"
            behavior_analyzer.save(lstm_path)
            print(f"      ✓ LSTM model saved to: {lstm_path} (Sequences: {len(X_seq)})")
        else:
            print("      ⚠️ Not enough sequential samples for LSTM per user.")
    except Exception as e:
        print(f"      ⚠️ LSTM training skipped or failed: {e}")

    # Summary Evaluation
    print("\n" + "=" * 65)
    print("🎯  Model Ensemble Validation Complete")
    scorer = ThreatScorer()
    sample_threat = scorer.score_event(
        isolation_score=0.85,
        autoencoder_score=0.78,
        lstm_score=0.92,
        feature_dict={
            "num_rows_affected": 24000,
            "is_after_hours": True,
            "has_pii": True,
            "columns_accessed": ["ssn", "credit_card"],
            "is_sensitive_table": True,
            "is_vpn": True,
            "user_role": "contractor",
            "action": "EXPORT",
        }
    )
    print(f"Validation Sample Threat Score: {sample_threat['threat_score']} ({sample_threat['threat_level']})")
    print(f"Contributing Factors:")
    for f in sample_threat['contributing_factors']:
        print(f"  - {f}")
    print("=" * 65)


if __name__ == "__main__":
    run_training_pipeline()
