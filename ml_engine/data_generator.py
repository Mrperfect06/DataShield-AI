"""
DataShield AI — Synthetic Data Generator
=========================================
Generates realistic data-access logs for training the anomaly-detection
pipeline.  Two flavours of events are produced:

* **Normal** — business-hours queries, moderate row counts, non-sensitive
  tables/columns, consistent geo-locations.
* **Anomalous** — after-hours bulk downloads, PII column access, unusual
  geolocations, impossible-travel scenarios, and role-deviation patterns.

Each event is a flat dictionary ready for ``pandas.DataFrame`` conversion.

Usage
-----
>>> from ml_engine.data_generator import generate_dataset, save_dataset
>>> df = generate_dataset(n_normal=10000, n_anomalous=500)
>>> save_dataset(df, "data/training_data.csv")
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    from faker import Faker
    fake = Faker()
    Faker.seed(42)
except ImportError:
    class MockFaker:
        def email(self):
            return f"user_{random.randint(100, 999)}@corp.internal"
    fake = MockFaker()
from config import (
    NUM_USERS,
    NUM_NORMAL_EVENTS,
    NUM_ANOMALOUS_EVENTS,
    SENSITIVE_TABLES,
    NORMAL_TABLES,
    PII_COLUMNS,
    NORMAL_COLUMNS,
)

random.seed(42)
np.random.seed(42)

# Roles and departments used when creating the user pool
ROLES: List[str] = ["engineer", "analyst", "admin", "intern", "contractor"]
DEPARTMENTS: List[str] = [
    "Engineering",
    "Data Science",
    "Finance",
    "HR",
    "Marketing",
    "Security",
    "Legal",
]

# Actions that can appear in access logs
NORMAL_ACTIONS: List[str] = ["SELECT", "SELECT", "SELECT", "UPDATE"]  # weighted
ANOMALOUS_ACTIONS: List[str] = ["EXPORT", "DOWNLOAD", "DELETE", "SELECT"]

# Geo-location pools
NORMAL_GEOS: List[str] = [
    "New York, US",
    "San Francisco, US",
    "Austin, US",
    "Chicago, US",
    "Seattle, US",
    "Boston, US",
    "Denver, US",
]
UNUSUAL_GEOS: List[str] = [
    "Moscow, RU",
    "Beijing, CN",
    "Lagos, NG",
    "Pyongyang, KP",
    "Tehran, IR",
    "Minsk, BY",
    "Caracas, VE",
]

# Anomaly type catalogue
ANOMALY_TYPES: List[str] = [
    "after_hours",
    "bulk_download",
    "pii_access",
    "geo_anomaly",
    "impossible_travel",
    "role_deviation",
]


# ---------------------------------------------------------------------------
# User Pool
# ---------------------------------------------------------------------------

def _build_user_pool(n_users: int = NUM_USERS) -> List[Dict]:
    """Create a stable pool of synthetic users.

    Each user gets a consistent home geo-location, role, and department so
    that deviation from the norm can be detected later.

    Returns
    -------
    list[dict]
        Each dict contains ``user_id``, ``user_email``, ``user_role``,
        ``department``, and ``home_geo``.
    """
    users: List[Dict] = []
    for i in range(n_users):
        user = {
            "user_id": f"user_{i + 1:03d}",
            "user_email": fake.email(),
            "user_role": random.choice(ROLES),
            "department": random.choice(DEPARTMENTS),
            "home_geo": random.choice(NORMAL_GEOS),
        }
        users.append(user)
    return users


# Global user pool (built once, reused across calls)
_USER_POOL: List[Dict] = _build_user_pool()


# ---------------------------------------------------------------------------
# IP helpers
# ---------------------------------------------------------------------------

def _random_ip(is_vpn: bool = False) -> str:
    """Generate a random RFC-1918-like or public IP string.

    Parameters
    ----------
    is_vpn : bool
        If ``True``, generate from the ``10.x.x.x`` private range to
        simulate VPN traffic.
    """
    if is_vpn:
        return f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"
    return f"{random.randint(1, 223)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}"


# ---------------------------------------------------------------------------
# Event generators
# ---------------------------------------------------------------------------

def _generate_normal_event() -> Dict:
    """Produce a single *normal* access-log event.

    Characteristics:
    * Business hours (07:00 – 20:00), weekdays preferred.
    * Moderate row counts (1 – 500).
    * Non-sensitive tables & columns.
    * Consistent geo-location matching the user's home.
    """
    user = random.choice(_USER_POOL)

    # Timestamp: within last 30 days, business hours
    base_date = datetime.now() - timedelta(days=random.randint(0, 30))
    hour = random.randint(7, 19)  # 07:00 – 19:59
    minute = random.randint(0, 59)
    # Prefer weekdays (Mon–Fri)
    while base_date.weekday() >= 5:
        base_date -= timedelta(days=1)
    timestamp = base_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))

    # Columns accessed — 1-4 normal columns
    cols = random.sample(NORMAL_COLUMNS, k=random.randint(1, min(4, len(NORMAL_COLUMNS))))

    is_vpn = random.random() < 0.3  # 30 % use VPN

    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "user_id": user["user_id"],
        "user_email": user["user_email"],
        "user_role": user["user_role"],
        "department": user["department"],
        "action": random.choice(NORMAL_ACTIONS),
        "table_name": random.choice(NORMAL_TABLES),
        "columns_accessed": cols,
        "num_rows_affected": random.randint(1, 500),
        "source_ip": _random_ip(is_vpn),
        "geo_location": user["home_geo"],
        "session_duration_seconds": random.randint(60, 3600),
        "is_vpn": is_vpn,
        "is_anomalous": False,
        "anomaly_type": None,
    }


def _generate_anomalous_event() -> Dict:
    """Produce a single *anomalous* access-log event.

    One anomaly type is chosen at random, and the event is crafted to
    exhibit the characteristics of that anomaly while keeping the other
    fields plausible.
    """
    user = random.choice(_USER_POOL)
    anomaly_type = random.choice(ANOMALY_TYPES)

    # Defaults (will be overridden per anomaly type)
    base_date = datetime.now() - timedelta(days=random.randint(0, 30))
    hour = random.randint(7, 19)
    minute = random.randint(0, 59)
    timestamp = base_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
    action = random.choice(NORMAL_ACTIONS)
    table = random.choice(NORMAL_TABLES)
    cols: List[str] = random.sample(NORMAL_COLUMNS, k=random.randint(1, 3))
    num_rows = random.randint(1, 500)
    geo = user["home_geo"]
    session_dur = random.randint(60, 3600)
    is_vpn = random.random() < 0.3

    # ----- Apply anomaly-specific mutations -----
    if anomaly_type == "after_hours":
        # Access between 22:00 and 05:00
        hour = random.choice([*range(0, 6), *range(22, 24)])
        timestamp = base_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
        action = random.choice(ANOMALOUS_ACTIONS)
        session_dur = random.randint(5, 300)  # short, suspicious session

    elif anomaly_type == "bulk_download":
        action = random.choice(["EXPORT", "DOWNLOAD"])
        num_rows = random.randint(50_000, 5_000_000)
        session_dur = random.randint(1800, 7200)
        table = random.choice(SENSITIVE_TABLES + NORMAL_TABLES)

    elif anomaly_type == "pii_access":
        # Access sensitive columns on sensitive tables
        table = random.choice(SENSITIVE_TABLES)
        cols = random.sample(PII_COLUMNS, k=random.randint(2, min(5, len(PII_COLUMNS))))
        num_rows = random.randint(100, 100_000)
        action = random.choice(["SELECT", "EXPORT", "DOWNLOAD"])

    elif anomaly_type == "geo_anomaly":
        geo = random.choice(UNUSUAL_GEOS)
        is_vpn = False  # no VPN → raw unusual IP
        action = random.choice(ANOMALOUS_ACTIONS)

    elif anomaly_type == "impossible_travel":
        # Two geos far apart in a short time — we simulate the *second*
        # access that looks suspicious.
        geo = random.choice(UNUSUAL_GEOS)
        session_dur = random.randint(5, 120)
        is_vpn = False

    elif anomaly_type == "role_deviation":
        # e.g.  intern or contractor accessing sensitive tables
        user = dict(user)  # shallow copy so pool is not mutated
        user["user_role"] = random.choice(["intern", "contractor"])
        table = random.choice(SENSITIVE_TABLES)
        cols = random.sample(
            PII_COLUMNS + NORMAL_COLUMNS,
            k=random.randint(2, 4),
        )
        action = random.choice(["DELETE", "EXPORT", "DOWNLOAD", "UPDATE"])
        num_rows = random.randint(500, 500_000)

    return {
        "event_id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "user_id": user["user_id"],
        "user_email": user["user_email"],
        "user_role": user["user_role"],
        "department": user["department"],
        "action": action,
        "table_name": table,
        "columns_accessed": cols,
        "num_rows_affected": num_rows,
        "source_ip": _random_ip(is_vpn),
        "geo_location": geo,
        "session_duration_seconds": session_dur,
        "is_vpn": is_vpn,
        "is_anomalous": True,
        "anomaly_type": anomaly_type,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_dataset(
    n_normal: int = NUM_NORMAL_EVENTS,
    n_anomalous: int = NUM_ANOMALOUS_EVENTS,
) -> pd.DataFrame:
    """Generate a synthetic access-log dataset.

    Parameters
    ----------
    n_normal : int
        Number of normal events to generate.
    n_anomalous : int
        Number of anomalous events to generate.

    Returns
    -------
    pd.DataFrame
        Shuffled DataFrame containing both normal and anomalous events.
    """
    events: List[Dict] = []

    print(f"[DataGenerator] Generating {n_normal} normal events …")
    for _ in range(n_normal):
        events.append(_generate_normal_event())

    print(f"[DataGenerator] Generating {n_anomalous} anomalous events …")
    for _ in range(n_anomalous):
        events.append(_generate_anomalous_event())

    df = pd.DataFrame(events)

    # Convert columns_accessed list → comma-separated string for CSV compat
    df["columns_accessed"] = df["columns_accessed"].apply(
        lambda cols: ",".join(cols) if isinstance(cols, list) else cols
    )

    # Shuffle and reset index
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"[DataGenerator] Dataset ready — {len(df)} total events "
          f"({n_normal} normal, {n_anomalous} anomalous).")
    return df


def save_dataset(df: pd.DataFrame, path: str | Path) -> Path:
    """Persist a DataFrame to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        The dataset to save.
    path : str | Path
        Destination file path (directories are created automatically).

    Returns
    -------
    Path
        Resolved path where the CSV was written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"[DataGenerator] Saved dataset → {path}  ({len(df)} rows)")
    return path


# ---------------------------------------------------------------------------
# Quick self-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    df = generate_dataset(n_normal=200, n_anomalous=20)
    print(df.head(10).to_string())
    print(f"\nAnomalous breakdown:\n{df[df['is_anomalous']]['anomaly_type'].value_counts()}")
    save_dataset(df, "data/sample_access_logs.csv")
