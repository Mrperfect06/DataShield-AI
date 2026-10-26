"""
DataShield AI — Shared Configuration
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ─── Project Paths ────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
ML_ENGINE_DIR = PROJECT_ROOT / "ml_engine"
GENAI_DIR = PROJECT_ROOT / "genai_explainer"
BLOCKCHAIN_DIR = PROJECT_ROOT / "blockchain"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "saved_models"

# ─── ML Engine Config ────────────────────────────────────────────────────────
ANOMALY_CONTAMINATION = 0.05          # Expected fraction of anomalies
THREAT_SCORE_THRESHOLD = 70           # Score above which to trigger alerts
LSTM_SEQUENCE_LENGTH = 10             # Sequence length for behavior model
LSTM_HIDDEN_SIZE = 64
LSTM_NUM_LAYERS = 2
AUTOENCODER_LATENT_DIM = 16
TRAINING_EPOCHS = 50
BATCH_SIZE = 64
LEARNING_RATE = 1e-3

# ─── Synthetic Data Config ───────────────────────────────────────────────────
NUM_USERS = 50
NUM_NORMAL_EVENTS = 10000
NUM_ANOMALOUS_EVENTS = 500
SENSITIVE_TABLES = [
    "prod.users", "prod.payments", "prod.medical_records",
    "prod.ssn_data", "prod.credit_cards", "prod.employee_salaries",
]
NORMAL_TABLES = [
    "analytics.page_views", "analytics.sessions", "logs.app_events",
    "staging.temp_data", "public.products", "public.categories",
]
PII_COLUMNS = ["email", "phone", "ssn", "credit_card", "address", "dob"]
NORMAL_COLUMNS = ["id", "name", "created_at", "status", "type", "count"]

# ─── GenAI Config ─────────────────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL_NAME = "gemini-2.0-flash"
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
CHROMA_COLLECTION_NAME = "security_policies"
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma_db")
MAX_RAG_RESULTS = 5

# ─── Blockchain Config ───────────────────────────────────────────────────────
POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "http://127.0.0.1:8545")
DEPLOYER_PRIVATE_KEY = os.getenv("DEPLOYER_PRIVATE_KEY", "")  # Loaded from .env
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS", "")

# ─── API Config ───────────────────────────────────────────────────────────────
API_HOST = "0.0.0.0"
API_PORT = 8000
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
