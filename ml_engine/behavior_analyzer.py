"""
DataShield AI — LSTM User Behaviour Analyzer
==============================================
Analyses temporal access patterns per user using an LSTM network.
A sliding window of feature vectors is classified as normal or anomalous,
capturing sequential dependencies that point models miss.

Architecture
------------
``UserBehaviorLSTM`` (nn.Module):
    input_dim → LSTM(hidden=64, layers=2, dropout=0.3) → FC → sigmoid

``BehaviorAnalyzer`` (high-level wrapper):
    build_sequences → fit → predict → save / load

Usage
-----
>>> from ml_engine.behavior_analyzer import BehaviorAnalyzer
>>> ba = BehaviorAnalyzer(input_dim=16)
>>> X_seq, y_seq = ba.build_sequences(df, feature_matrix, labels, seq_length=10)
>>> ba.fit(X_seq, y_seq, epochs=50)
>>> probs = ba.predict(X_seq)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

# PyTorch --------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    warnings.warn("PyTorch not found — BehaviorAnalyzer will be unavailable.")

from config import (
    LSTM_SEQUENCE_LENGTH,
    LSTM_HIDDEN_SIZE,
    LSTM_NUM_LAYERS,
    TRAINING_EPOCHS,
    BATCH_SIZE,
    LEARNING_RATE,
)


# ============================================================================
# LSTM Model
# ============================================================================

if _TORCH_AVAILABLE:

    class UserBehaviorLSTM(nn.Module):
        """LSTM network for sequential anomaly classification.

        Parameters
        ----------
        input_dim : int
            Number of features per time step.
        hidden_size : int
            LSTM hidden-state dimensionality.
        num_layers : int
            Number of stacked LSTM layers.
        dropout : float
            Dropout between LSTM layers (only applied when num_layers > 1).
        """

        def __init__(
            self,
            input_dim: int,
            hidden_size: int = LSTM_HIDDEN_SIZE,
            num_layers: int = LSTM_NUM_LAYERS,
            dropout: float = 0.3,
        ) -> None:
            super().__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size=input_dim,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0.0,
            )
            self.batch_norm = nn.BatchNorm1d(hidden_size)
            self.dropout = nn.Dropout(0.3)
            self.fc = nn.Linear(hidden_size, 1)
            self.sigmoid = nn.Sigmoid()

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Forward pass.

            Parameters
            ----------
            x : torch.Tensor, shape (batch, seq_len, input_dim)

            Returns
            -------
            torch.Tensor, shape (batch, 1)
                Anomaly probability for each sequence.
            """
            # h_0, c_0 default to zeros
            lstm_out, _ = self.lstm(x)
            # Take the last time-step's output
            last_hidden = lstm_out[:, -1, :]  # (batch, hidden_size)
            normed = self.batch_norm(last_hidden)
            dropped = self.dropout(normed)
            logit = self.fc(dropped)
            prob = self.sigmoid(logit)
            return prob


# ============================================================================
# High-Level Analyzer
# ============================================================================

class BehaviorAnalyzer:
    """LSTM-based sequential behaviour analysis.

    Wraps ``UserBehaviorLSTM`` with data preparation, training,
    prediction, and persistence helpers.

    Parameters
    ----------
    input_dim : int
        Number of features per time step (must match FeatureEngineer output).
    hidden_size : int
        LSTM hidden dimensionality.
    num_layers : int
        Number of stacked LSTM layers.
    learning_rate : float
        Optimiser learning rate.
    device : str | None
        ``"cuda"`` or ``"cpu"``.  Auto-detected when ``None``.
    """

    def __init__(
        self,
        input_dim: int = 16,
        hidden_size: int = LSTM_HIDDEN_SIZE,
        num_layers: int = LSTM_NUM_LAYERS,
        learning_rate: float = LEARNING_RATE,
        device: Optional[str] = None,
    ) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for BehaviorAnalyzer.")

        self.input_dim = input_dim
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.learning_rate = learning_rate
        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        self.model: Optional[UserBehaviorLSTM] = None
        self.is_fitted: bool = False

    def _build_model(self) -> UserBehaviorLSTM:
        """Instantiate the LSTM and move it to the target device."""
        model = UserBehaviorLSTM(
            input_dim=self.input_dim,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
        ).to(self.device)
        return model

    # ------------------------------------------------------------------
    # Sequence building
    # ------------------------------------------------------------------

    @staticmethod
    def build_sequences(
        df: pd.DataFrame,
        feature_matrix: np.ndarray,
        labels: np.ndarray,
        seq_length: int = LSTM_SEQUENCE_LENGTH,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create sliding-window sequences grouped by user.

        For each user, events are sorted by timestamp and a sliding window
        of ``seq_length`` consecutive feature vectors is extracted.  The
        label for each window is 1 if **any** event in the window is
        anomalous (conservative labelling).

        Parameters
        ----------
        df : pd.DataFrame
            Raw event DataFrame (needs ``user_id`` and ``timestamp``).
        feature_matrix : np.ndarray, shape (n_samples, n_features)
            Scaled feature vectors aligned with ``df``.
        labels : np.ndarray, shape (n_samples,)
            Binary labels (1 = anomalous).
        seq_length : int
            Window size.

        Returns
        -------
        X_seq : np.ndarray, shape (n_sequences, seq_length, n_features)
        y_seq : np.ndarray, shape (n_sequences,)
        """
        df = df.copy().reset_index(drop=True)
        # Ensure timestamp is datetime
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

        X_sequences: List[np.ndarray] = []
        y_sequences: List[int] = []

        for _uid, grp in df.groupby("user_id"):
            # Sort by time within user
            sorted_idx = grp.sort_values("timestamp").index.tolist()
            if len(sorted_idx) < seq_length:
                continue  # skip users with too few events

            user_features = feature_matrix[sorted_idx]
            user_labels = labels[sorted_idx]

            for start in range(len(sorted_idx) - seq_length + 1):
                end = start + seq_length
                X_sequences.append(user_features[start:end])
                # Label = 1 if ANY event in window is anomalous
                y_sequences.append(int(user_labels[start:end].max()))

        if len(X_sequences) == 0:
            # Fallback: non-user-grouped sliding window over the whole dataset
            warnings.warn(
                "No user had enough events for sequences — "
                "falling back to global sliding window."
            )
            for start in range(len(feature_matrix) - seq_length + 1):
                end = start + seq_length
                X_sequences.append(feature_matrix[start:end])
                y_sequences.append(int(labels[start:end].max()))

        X_seq = np.array(X_sequences, dtype=np.float32)
        y_seq = np.array(y_sequences, dtype=np.float32)
        print(f"[BehaviorAnalyzer] Built {len(X_seq)} sequences of length {seq_length}")
        return X_seq, y_seq

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(
        self,
        X_sequences: np.ndarray,
        y_labels: np.ndarray,
        epochs: int = TRAINING_EPOCHS,
        batch_size: int = BATCH_SIZE,
        verbose: bool = True,
    ) -> "BehaviorAnalyzer":
        """Train the LSTM on labelled sequences.

        Parameters
        ----------
        X_sequences : np.ndarray, shape (n_seq, seq_len, n_features)
        y_labels : np.ndarray, shape (n_seq,)
        epochs : int
        batch_size : int
        verbose : bool

        Returns
        -------
        self
        """
        self.input_dim = X_sequences.shape[2]
        self.model = self._build_model()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)

        # Use weighted BCE to handle class imbalance
        pos_count = y_labels.sum()
        neg_count = len(y_labels) - pos_count
        pos_weight_val = max(neg_count / max(pos_count, 1), 1.0)
        pos_weight = torch.tensor([pos_weight_val], dtype=torch.float32).to(self.device)
        criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

        tensor_X = torch.FloatTensor(X_sequences).to(self.device)
        tensor_y = torch.FloatTensor(y_labels).unsqueeze(1).to(self.device)
        dataset = TensorDataset(tensor_X, tensor_y)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model.train()
        print(f"[BehaviorAnalyzer] Training LSTM on {len(X_sequences)} sequences "
              f"for {epochs} epochs (pos_weight={pos_weight_val:.2f}) …")

        for epoch in range(1, epochs + 1):
            epoch_loss = 0.0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                # Use raw logits for BCEWithLogitsLoss
                lstm_out, _ = self.model.lstm(batch_x)
                last_hidden = lstm_out[:, -1, :]
                normed = self.model.batch_norm(last_hidden)
                dropped = self.model.dropout(normed)
                logits = self.model.fc(dropped)
                loss = criterion(logits, batch_y)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item() * batch_x.size(0)
            epoch_loss /= len(dataset)

            if verbose and (epoch % max(1, epochs // 10) == 0 or epoch == 1):
                print(f"  Epoch {epoch:4d}/{epochs}  Loss={epoch_loss:.6f}")

        self.is_fitted = True
        print("[BehaviorAnalyzer] Training complete.")
        return self

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def predict(self, X_sequences: np.ndarray) -> np.ndarray:
        """Return anomaly probabilities for each sequence.

        Parameters
        ----------
        X_sequences : np.ndarray, shape (n_seq, seq_len, n_features)

        Returns
        -------
        np.ndarray, shape (n_seq,)
            Probabilities in [0, 1].
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        self.model.eval()
        tensor_X = torch.FloatTensor(X_sequences).to(self.device)

        with torch.no_grad():
            probs = self.model(tensor_X).squeeze(1).cpu().numpy()

        return probs.astype(np.float64)

    def predict_labels(
        self, X_sequences: np.ndarray, threshold: float = 0.5
    ) -> np.ndarray:
        """Binary labels: 1 = anomalous, 0 = normal."""
        return (self.predict(X_sequences) >= threshold).astype(int)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> Path:
        """Save the LSTM model and metadata.

        Parameters
        ----------
        path : str | Path
            Destination file (e.g. ``saved_models/behavior_lstm.pt``).
        """
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to save the model.")
        if self.model is None:
            raise RuntimeError("No model to save. Call fit() first.")

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "input_dim": self.input_dim,
                "hidden_size": self.hidden_size,
                "num_layers": self.num_layers,
            },
            path,
        )
        print(f"[BehaviorAnalyzer] Saved → {path}")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "BehaviorAnalyzer":
        """Load a previously trained LSTM model.

        Parameters
        ----------
        path : str | Path
            Path to the ``.pt`` file.
        """
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to load the model.")

        instance = cls()
        checkpoint = torch.load(path, map_location=instance.device, weights_only=False)
        instance.input_dim = checkpoint["input_dim"]
        instance.hidden_size = checkpoint["hidden_size"]
        instance.num_layers = checkpoint["num_layers"]
        instance.model = instance._build_model()
        instance.model.load_state_dict(checkpoint["model_state_dict"])
        instance.model.eval()
        instance.is_fitted = True
        print(f"[BehaviorAnalyzer] Loaded <- {path}")
        return instance


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not _TORCH_AVAILABLE:
        print("PyTorch not installed — skipping self-test.")
    else:
        np.random.seed(42)
        n_seq, seq_len, n_feat = 200, 10, 16
        X_demo = np.random.randn(n_seq, seq_len, n_feat).astype(np.float32)
        y_demo = (np.random.rand(n_seq) > 0.9).astype(np.float32)

        ba = BehaviorAnalyzer(input_dim=n_feat)
        ba.fit(X_demo, y_demo, epochs=5, verbose=True)
        probs = ba.predict(X_demo)
        print(f"Prob range: [{probs.min():.4f}, {probs.max():.4f}]")
        print(f"Mean anomaly prob: {probs.mean():.4f}")
