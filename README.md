# DataShield AI 🛡️
# Blockchain + ML + GenAI Powered Data Breach Prevention & Forensics

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### 1. Install Python Dependencies
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Install Blockchain Dependencies
```bash
cd blockchain
npm install
```

### 3. Install Frontend Dependencies
```bash
cd frontend
npm install
```

### 4. Set Up Environment
```bash
copy .env.example .env
# Edit .env with your API keys
```

### 5. Generate Synthetic Data & Train Models
```bash
python -m ml_engine.train
```

### 6. Start Local Blockchain
```bash
cd blockchain
npx hardhat node
# In another terminal:
npx hardhat run scripts/deploy.js --network localhost
```

### 7. Initialize RAG Knowledge Base
```bash
python -m genai_explainer.rag_pipeline
```

### 8. Start the API Server
```bash
python -m api.main
```

### 9. Start the Frontend
```bash
cd frontend
npm run dev
```

### 10. Open Dashboard
Navigate to `http://localhost:5173`

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DataShield AI Platform                       │
├──────────────────┬──────────────────┬───────────────────────────┤
│  🔍 ML Engine    │  🧠 GenAI Engine │  ⛓️ Blockchain Audit      │
│                  │                  │                           │
│  • Anomaly Det.  │  • SHAP Analysis │  • Immutable Logs         │
│  • User Behavior │  • LLM Reports   │  • Smart Contracts        │
│  • Threat Score  │  • RAG Pipeline  │  • Evidence Chain          │
├──────────────────┴──────────────────┴───────────────────────────┤
│                      FastAPI Backend                             │
├─────────────────────────────────────────────────────────────────┤
│                     React Dashboard                              │
└─────────────────────────────────────────────────────────────────┘
```

## License
MIT
