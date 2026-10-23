import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_DIR = BASE_DIR / "Dataset"
PROMPTS_DIR = BASE_DIR / "prompts"

# Environment variable name constants ending in _ENV
TOKEN_ENV = "AGENT_API_TOKEN"
MODEL_KEY_ENV = "GROQ_API_KEY"
TARGET_ENV_VAR = "TARGET_ENV"

# Read secrets strictly from environment variables without hardcoded fallback secrets
AGENT_API_TOKEN = os.environ.get(TOKEN_ENV, "")
GROQ_API_KEY = os.environ.get(MODEL_KEY_ENV, "")
TARGET_ENV = os.environ.get(TARGET_ENV_VAR, "sandbox")

# Capabilities and SLO parameters
MAX_STEPS = 6
CONTEXT_BUDGET_TOKENS = 8000
TIMEOUT_SECONDS = 30
P95_LATENCY_MS = 8000
MAX_COST_PER_TASK_USD = 0.05

# Pricing rates as numbers
PRICE_PER_INPUT_TOKEN_USD = 0.0000005
PRICE_PER_OUTPUT_TOKEN_USD = 0.0000015

# Agent constants
AGENT_NAME = "support_agent"
AGENT_TITLE = "Support Agent"
AGENT_VERSION = "1.0.0"
