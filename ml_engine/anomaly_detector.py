"""
DataShield AI — Anomaly Detection Models
==========================================
Two complementary anomaly detectors:

1. **IsolationForestDetector** — scikit-learn Isolation Forest for fast,
   unsupervised anomaly scoring.
2. **AutoencoderDetector** — PyTorch-based deep autoencoder that scores
   events by reconstruction error.

Both expose a unified ``fit`` / ``predict`` / ``save`` / ``load`` API.

Usage
-----
>>> from ml_engine.anomaly_detector import IsolationForestDetector, AutoencoderDetector
>>> ifd = IsolationForestDetector()
>>> ifd.fit(X_train)
>>> scores = ifd.predict(X_test)
"""

from __future__ import annotations

import warnings
from pathlib import Path
from typing import Optional

import numpy as np

# scikit-learn ---------------------------------------------------------------
try:
    from sklearn.ensemble import IsolationForest
    import joblib

    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    warnings.warn("scikit-learn not found — IsolationForestDetector unavailable.")

# PyTorch --------------------------------------------------------------------
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False
    warnings.warn("PyTorch not found — AutoencoderDetector unavailable.")

from config import (
    ANOMALY_CONTAMINATION,
    AUTOENCODER_LATENT_DIM,
    TRAINING_EPOCHS,
    BATCH_SIZE,
    LEARNING_RATE,
)


# ============================================================================
# 1. Isolation Forest Detector
# ============================================================================

class IsolationForestDetector:
    """Wrapper around ``sklearn.ensemble.IsolationForest``.

    Anomaly scores are re-mapped to a **[0, 1]** scale where
    **higher = more anomalous** (the opposite of sklearn's native
    convention where negatives indicate outliers).

    Parameters
    ----------
    contamination : float
        Expected proportion of outliers in the training data.
    random_state : int
        Random seed for reproducibility.
    n_estimators : int
        Number of trees in the forest.
    """

    def __init__(
        self,
        contamination: float = ANOMALY_CONTAMINATION,
        random_state: int = 42,
        n_estimators: int = 200,
    ) -> None:
        if not _SKLEARN_AVAILABLE:
            raise RuntimeError("scikit-learn is required for IsolationForestDetector.")
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=n_estimators,
            n_jobs=-1,
        )
        self.is_fitted: bool = False

    def fit(self, X: np.ndarray) -> "IsolationForestDetector":
        """Fit the Isolation Forest on the feature matrix.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
            Training feature matrix (typically all data, including anomalies
            up to the ``contamination`` ratio).

        Returns
        -------
        self
        """
        print(f"[IsolationForest] Training on {X.shape[0]} samples, "
              f"{X.shape[1]} features …")
        self.model.fit(X)
        self.is_fitted = True
        print("[IsolationForest] Training complete.")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores in **[0, 1]** (higher = more anomalous).

        The raw ``decision_function`` output (large negative = outlier) is
        rescaled via min-max normalisation so that 0 ≈ most normal and
        1 ≈ most anomalous.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        np.ndarray, shape (n_samples,)
            Anomaly scores between 0 and 1.
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        # sklearn: higher decision_function → more normal
        raw_scores = self.model.decision_function(X)

        # Invert so higher = more anomalous, then min-max scale to [0, 1]
        inverted = -raw_scores
        score_min = inverted.min()
        score_max = inverted.max()
        denom = score_max - score_min
        if denom == 0:
            return np.zeros(len(X))
        scores = (inverted - score_min) / denom
        return scores.astype(np.float64)

    def predict_labels(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Binary labels: 1 = anomalous, 0 = normal.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix.
        threshold : float
            Score threshold above which an event is labelled anomalous.
        """
        return (self.predict(X) >= threshold).astype(int)

    # -- Persistence --

    def save(self, path: str | Path) -> Path:
        """Persist the trained model with joblib.

        Parameters
        ----------
        path : str | Path
            Destination file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        print(f"[IsolationForest] Saved → {path}")
        return path

    def load(self, path: str | Path) -> "IsolationForestDetector":
        """Load a previously trained model.

        Parameters
        ----------
        path : str | Path
            Path to the joblib file.
        """
        self.model = joblib.load(path)
        self.is_fitted = True
        print(f"[IsolationForest] Loaded ← {path}")
        return self


# ============================================================================
# 2. Autoencoder Detector (PyTorch)
# ============================================================================

if _TORCH_AVAILABLE:

    class _Autoencoder(nn.Module):
        """Symmetric fully-connected autoencoder.

        Architecture
        ------------
        input_dim → 64 → 32 → latent_dim → 32 → 64 → input_dim

        The bottleneck forces the network to learn a compressed
        representation of *normal* patterns; anomalies produce larger
        reconstruction errors.
        """

        def __init__(self, input_dim: int, latent_dim: int = AUTOENCODER_LATENT_DIM) -> None:
            super().__init__()
            self.encoder = nn.Sequential(
                nn.Linear(input_dim, 64),
                nn.ReLU(),
                nn.BatchNorm1d(64),
                nn.Dropout(0.2),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.BatchNorm1d(32),
                nn.Linear(32, latent_dim),
                nn.ReLU(),
            )
            self.decoder = nn.Sequential(
                nn.Linear(latent_dim, 32),
                nn.ReLU(),
                nn.BatchNorm1d(32),
                nn.Dropout(0.2),
                nn.Linear(32, 64),
                nn.ReLU(),
                nn.BatchNorm1d(64),
                nn.Linear(64, input_dim),
            )

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            """Reconstruct input through the bottleneck."""
            z = self.encoder(x)
            x_hat = self.decoder(z)
            return x_hat


class AutoencoderDetector:
    """Train a deep autoencoder and score events by reconstruction error.

    The detector normalises reconstruction errors to **[0, 1]** by tracking
    the distribution of errors on the training set (mean + 3σ capping).

    Parameters
    ----------
    input_dim : int
        Number of features (columns in X).
    latent_dim : int
        Size of the bottleneck layer.
    learning_rate : float
        Adam optimiser learning rate.
    device : str | None
        ``"cuda"`` or ``"cpu"``.  Auto-detected when ``None``.
    """

    def __init__(
        self,
        input_dim: int = 16,
        latent_dim: int = AUTOENCODER_LATENT_DIM,
        learning_rate: float = LEARNING_RATE,
        device: Optional[str] = None,
    ) -> None:
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required for AutoencoderDetector.")
        self.input_dim = input_dim
        self.latent_dim = latent_dim
        self.learning_rate = learning_rate
        self.device = torch.device(
            device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        )

        self.model: _Autoencoder = _Autoencoder(input_dim, latent_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()

        # Error normalisation params (set during fit)
        self._error_mean: float = 0.0
        self._error_std: float = 1.0
        self.is_fitted: bool = False

    def fit(
        self,
        X: np.ndarray,
        epochs: int = TRAINING_EPOCHS,
        batch_size: int = BATCH_SIZE,
        verbose: bool = True,
    ) -> "AutoencoderDetector":
        """Train the autoencoder on the (mostly normal) feature matrix.

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)
        epochs : int
            Number of training epochs.
        batch_size : int
            Mini-batch size.
        verbose : bool
            Print epoch loss summaries.

        Returns
        -------
        self
        """
        self.input_dim = X.shape[1]
        # Rebuild model if input_dim changed
        self.model = _Autoencoder(self.input_dim, self.latent_dim).to(self.device)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=self.learning_rate)

        tensor_X = torch.FloatTensor(X).to(self.device)
        dataset = TensorDataset(tensor_X, tensor_X)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model.train()
        print(f"[Autoencoder] Training on {X.shape[0]} samples, "
              f"{X.shape[1]} features for {epochs} epochs …")

        for epoch in range(1, epochs + 1):
            epoch_loss = 0.0
            for batch_x, _ in loader:
                self.optimizer.zero_grad()
                reconstructed = self.model(batch_x)
                loss = self.criterion(reconstructed, batch_x)
                loss.backward()
                self.optimizer.step()
                epoch_loss += loss.item() * batch_x.size(0)
            epoch_loss /= len(dataset)

            if verbose and (epoch % max(1, epochs // 10) == 0 or epoch == 1):
                print(f"  Epoch {epoch:4d}/{epochs}  Loss={epoch_loss:.6f}")

        # Compute error distribution on training data for normalisation
        self.model.eval()
        with torch.no_grad():
            recon = self.model(tensor_X)
            errors = torch.mean((tensor_X - recon) ** 2, dim=1).cpu().numpy()
        self._error_mean = float(errors.mean())
        self._error_std = float(errors.std()) or 1.0
        self.is_fitted = True
        print("[Autoencoder] Training complete.")
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return anomaly scores in **[0, 1]** (higher = more anomalous).

        Scores are the per-sample MSE reconstruction error, normalised
        using the training set error distribution and clipped to [0, 1].

        Parameters
        ----------
        X : np.ndarray, shape (n_samples, n_features)

        Returns
        -------
        np.ndarray, shape (n_samples,)
        """
        if not self.is_fitted:
            raise RuntimeError("Model not fitted. Call fit() first.")

        self.model.eval()
        tensor_X = torch.FloatTensor(X).to(self.device)
        with torch.no_grad():
            recon = self.model(tensor_X)
            errors = torch.mean((tensor_X - recon) ** 2, dim=1).cpu().numpy()

        # Normalise: z-score then scale to [0, 1] via sigmoid-like capping
        z = (errors - self._error_mean) / self._error_std
        # Cap at ±3σ then rescale
        scores = np.clip(z / 3.0, 0.0, 1.0)
        return scores.astype(np.float64)

    def predict_labels(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """Binary labels: 1 = anomalous, 0 = normal."""
        return (self.predict(X) >= threshold).astype(int)

    # -- Persistence --

    def save(self, path: str | Path) -> Path:
        """Save autoencoder model and normalisation parameters.

        Parameters
        ----------
        path : str | Path
            Destination file (e.g. ``saved_models/autoencoder.pt``).
        """
        if not _TORCH_AVAILABLE:
            raise RuntimeError("PyTorch is required to save the model.")
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "input_dim": self.input_dim,
                "latent_dim": self.latent_dim,
                "error_mean": self._error_mean,
                "error_std": self._error_std,
            },
            path,
        )
        print(f"[Autoencoder] Saved → {path}")
        return path

    @classmethod
    def load(cls, path: str | Path) -> "AutoencoderDetector":
        """Load a previously trained autoencoder.

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
        instance.latent_dim = checkpoint["latent_dim"]
        instance._error_mean = checkpoint["error_mean"]
        instance._error_std = checkpoint["error_std"]
        instance.model = _Autoencoder(instance.input_dim, instance.latent_dim).to(instance.device)
        instance.model.load_state_dict(checkpoint["model_state_dict"])
        instance.model.eval()
        instance.is_fitted = True
        print(f"[Autoencoder] Loaded <- {path}")
        return instance


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Generate random data for a smoke test
    np.random.seed(42)
    X_demo = np.random.randn(500, 16).astype(np.float32)

    print("=== Isolation Forest ===")
    ifd = IsolationForestDetector()
    ifd.fit(X_demo)
    iso_scores = ifd.predict(X_demo)
    print(f"Score range: [{iso_scores.min():.4f}, {iso_scores.max():.4f}]")

    if _TORCH_AVAILABLE:
        print("\n=== Autoencoder ===")
        aed = AutoencoderDetector(input_dim=16)
        aed.fit(X_demo, epochs=10, verbose=True)
        ae_scores = aed.predict(X_demo)
        print(f"Score range: [{ae_scores.min():.4f}, {ae_scores.max():.4f}]")
