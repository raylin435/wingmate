"""Environment-driven settings. Every sponsor integration is optional: a missing key falls back
to a local implementation so the demo always runs."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND = Path(__file__).resolve().parents[1]
load_dotenv(BACKEND.parent / ".env")
load_dotenv(BACKEND / ".env")

DATA = BACKEND / "data"
CACHE = DATA / ".cache"
CACHE.mkdir(parents=True, exist_ok=True)


def env(key: str, default: str | None = None) -> str | None:
    value = os.environ.get(key, "").strip()
    return value or default


SIE_API_KEY = env("SIE_API_KEY")
SINGLESTORE_URL = env("SINGLESTORE_URL")
STATSIG_SERVER_KEY = env("STATSIG_SERVER_KEY")
AMPLITUDE_API_KEY = env("AMPLITUDE_API_KEY")
COGNEE_ENABLED = env("COGNEE_ENABLED", "auto")  # auto | 1 | 0
COGNEE_RECALL_TIMEOUT_S = float(env("COGNEE_RECALL_TIMEOUT_S", "8"))

CHAT_MODEL = env("SIE_CHAT_MODEL", "Qwen/Qwen3.8-27B-FP8")
EMBED_MODEL = env("SIE_EMBED_MODEL", "BAAI/bge-m3")
RERANK_MODEL = env("SIE_RERANK_MODEL", "Qwen/Qwen3-Reranker-4B")
CLASSIFY_MODEL = env("SIE_CLASSIFY_MODEL", "fastino/gliner2-large-v1")
PII_MODEL = env("SIE_PII_MODEL", "numind/NuNER_Zero")

# Show people by their first name everywhere (cards, chat, agent prompts). Set REAL_NAMES=0 to go back to
# made-up handles with names revealed only after both people accept.
REAL_NAMES = (env("REAL_NAMES", "1") or "1").lower() not in ("0", "false", "no", "off")

DEMO_PERSONA = "maya"
WARM_MEMORY = (env("WARM_MEMORY", "maya,theo,jordan,ben,kenji,diego") or "").split(",")
TIMEZONE = "America/Los_Angeles"

DEFAULT_POLICY = {
    "rerank_keep": 5,
    "candidate_pool": 20,
    "a2a_turns": 6,
    "min_score": 70,
    "agent_model": CHAT_MODEL,
    "max_words_per_message": 60,
}
DEFAULT_STRATEGY = "agent_predate"
