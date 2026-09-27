import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
MODEL = "gpt-4.1-mini-2025-04-14"
SEARCH_CAP, MODEL_CAP, SOURCE_CAP = 3, 2, 9
REQUEST_BYTE_CAP, OUTPUT_TOKEN_CAP, RUN_SECONDS = 100_000, 6000, 180
# Admission estimates, not a provider billing guarantee. No model switching.
SEARCH_USD = 0.01
INPUT_USD_PER_M, OUTPUT_USD_PER_M = 0.40, 1.60
MAX_ESTIMATE_USD = 0.20


def settings():
    """Read only named keys. No shell evaluation; environment takes precedence."""
    values = {}
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text().splitlines():
            key, sep, value = line.strip().partition("=")
            if sep and key in {"VC_ENABLE_LIVE", "OPENAI_API_KEY", "TAVILY_API_KEY"}:
                values[key] = value.strip().strip("\"'")
    return {key: os.environ.get(key, values.get(key, "")) for key in
            ("VC_ENABLE_LIVE", "OPENAI_API_KEY", "TAVILY_API_KEY")}


def readiness():
    env = settings()
    return {"enabled": env["VC_ENABLE_LIVE"].lower() == "true",
            "openai_configured": bool(env["OPENAI_API_KEY"]),
            "tavily_configured": bool(env["TAVILY_API_KEY"]),
            "model": MODEL, "max_searches": SEARCH_CAP, "max_model_calls": MODEL_CAP,
            "max_output_tokens_per_call": OUTPUT_TOKEN_CAP, "max_seconds": RUN_SECONDS,
            "max_estimated_usd": MAX_ESTIMATE_USD}
