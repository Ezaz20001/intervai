import os
import sys
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

if not GROQ_API_KEY or GROQ_API_KEY == "REPLACE_ME":
    print("WARNING: GROQ_API_KEY is not set or is at default value. Set a real key in .env or via environment variable.", file=sys.stderr)

POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "")
if not POSTGRES_PASSWORD or POSTGRES_PASSWORD == "REPLACE_ME":
    print("WARNING: POSTGRES_PASSWORD is not set or is at default value. Set a real password in .env or via environment variable.", file=sys.stderr)

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
if not REDIS_PASSWORD or REDIS_PASSWORD == "REPLACE_ME":
    print("WARNING: REDIS_PASSWORD is not set or is at default value. Set a real password in .env or via environment variable.", file=sys.stderr)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8501,http://localhost:8000").split(",")
CORS_ORIGINS = [o.strip() for o in CORS_ORIGINS if o.strip()]
for origin in CORS_ORIGINS:
    if origin != "*" and not (origin.startswith("http://") or origin.startswith("https://")):
        print(f"WARNING: CORS_ORIGINS contains invalid origin '{origin}'. Expected a full URL.", file=sys.stderr)
if "*" in CORS_ORIGINS:
    print("WARNING: CORS_ORIGINS contains '*' which allows all origins. This is insecure when credentials are enabled.", file=sys.stderr)
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", str(10 * 1024 * 1024)))
SESSION_TTL = int(os.getenv("SESSION_TTL", "3600"))
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "30"))
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/progress.db")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "data/chroma_db")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")

LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

SESSION_QUESTION_LIMIT = int(os.getenv("SESSION_QUESTION_LIMIT", "5"))

USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
LOCAL_LLM_BITS = int(os.getenv("LOCAL_LLM_BITS", "4"))

CROSS_ENCODER_MODEL = os.getenv("CROSS_ENCODER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://intervai:intervai@localhost:5432/intervai")
USE_POSTGRES = os.getenv("USE_POSTGRES", "false").lower() == "true"

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

DRIFT_WINDOW_SIZE = int(os.getenv("DRIFT_WINDOW_SIZE", "20"))
DRIFT_Z_THRESHOLD = float(os.getenv("DRIFT_Z_THRESHOLD", "2.0"))

GUARDRAIL_INJECTION_THRESHOLD = float(os.getenv("GUARDRAIL_INJECTION_THRESHOLD", "0.85"))
GUARDRAIL_OFFTOPIC_THRESHOLD = float(os.getenv("GUARDRAIL_OFFTOPIC_THRESHOLD", "0.6"))

COUNTDOWN_SECONDS = int(os.getenv("COUNTDOWN_SECONDS", "120"))

os.makedirs(DATABASE_PATH.rsplit("/", 1)[0] if "/" in DATABASE_PATH else "data", exist_ok=True)
os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)
