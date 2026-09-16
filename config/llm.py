"""Ollama LLM connection utilities."""

from langchain_ollama import ChatOllama

from config.settings import (
    AGENT_MODELS,
    LLM_TEMPERATURE,
    LLM_TIMEOUT,
    OLLAMA_BASE_URL,
)


def get_llm(agent_name: str) -> ChatOllama:
    """Return a ChatOllama instance for the given agent."""
    model = AGENT_MODELS.get(agent_name, AGENT_MODELS["business_advisor"])
    return ChatOllama(
        model=model,
        base_url=OLLAMA_BASE_URL,
        temperature=LLM_TEMPERATURE,
        # ── Fix #2: langchain-ollama uses request_timeout, not timeout ────────
        request_timeout=LLM_TIMEOUT,
    )


def check_ollama_connection() -> bool:
    """Verify Ollama is reachable."""
    try:
        llm = get_llm("business_advisor")
        llm.invoke("ping")
        return True
    except Exception:
        return False
