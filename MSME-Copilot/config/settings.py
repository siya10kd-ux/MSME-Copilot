"""Application settings for MSME Copilot."""

from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SAMPLE_DATA_DIR = DATA_DIR / "sample_datasets"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
DB_DIR = BASE_DIR / "db"
CHROMA_DIR = DB_DIR / "chroma"
SQLITE_PATH = DB_DIR / "msme_metrics.db"

# Ollama configuration
OLLAMA_BASE_URL = "http://localhost:11434"

# Configurable model names per agent
AGENT_MODELS = {
    "document_agent": "qwen2.5-coder:7b-instruct",
    "finance_agent": "qwen2.5-coder:7b-instruct",
    "inventory_agent": "qwen2.5-coder:7b-instruct",
    "supplier_agent": "qwen2.5-coder:7b-instruct",
    "business_advisor": "qwen2.5-coder:7b-instruct",
}

# LLM parameters
LLM_TEMPERATURE = 0.1
LLM_TIMEOUT = 120

# Random seed for reproducible demo
RANDOM_SEED = 42
