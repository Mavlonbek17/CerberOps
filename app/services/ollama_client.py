"""Shared low-level client for talking to the local Ollama daemon.

All AI-powered services (remediation reports, false-positive triage, smart
recon planning, PoC generation, chat) go through this module so that
connectivity checks, timeouts, and JSON parsing behave consistently.
"""

import json
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def check_ollama_available() -> bool:
    """Return True if Ollama is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            return r.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False


async def list_models() -> list[str]:
    """List available models in the local Ollama instance."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{settings.ollama_base_url}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                return [m["name"] for m in models]
    except Exception:
        pass
    return []


async def generate(
    *,
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.1,
    num_predict: int = 1024,
    json_mode: bool = True,
    timeout: float = 120.0,
) -> str | None:
    """Call Ollama's /api/generate and return the raw response text.

    Returns None if Ollama is unreachable or returns an error — callers
    are expected to fall back to a deterministic/template behavior.
    """
    model = model or settings.ollama_model

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(timeout=timeout)) as client:
            r = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": model,
                    "system": system,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json" if json_mode else "",
                    "options": {
                        "temperature": temperature,
                        "top_p": 0.9,
                        "num_predict": num_predict,
                        "repeat_penalty": 1.1,
                    },
                },
            )
            if r.status_code != 200:
                logger.error("Ollama returned %d: %s", r.status_code, r.text[:300])
                return None
            return r.json().get("response", "")
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        logger.error("Ollama request failed: %s", exc)
        return None


async def generate_json(
    *,
    prompt: str,
    system: str = "",
    model: str | None = None,
    temperature: float = 0.1,
    num_predict: int = 1024,
    timeout: float = 120.0,
) -> dict | None:
    """Call Ollama expecting a JSON object back. Returns None on failure."""
    text = await generate(
        prompt=prompt,
        system=system,
        model=model,
        temperature=temperature,
        num_predict=num_predict,
        json_mode=True,
        timeout=timeout,
    )
    if text is None:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("Ollama returned non-JSON despite format=json: %s", text[:200])
        return None


def to_str(val: object) -> str:
    """Coerce any JSON value (str/list/dict) to a plain readable string."""
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        parts: list[str] = []
        for i, item in enumerate(val, 1):
            if isinstance(item, dict):
                step = item.get("step", item.get("title", item.get("name", "")))
                desc = item.get("description", item.get("detail", ""))
                cmds = item.get("commands", item.get("command", []))
                if isinstance(cmds, str):
                    cmds = [cmds]
                line = f"{i}. {step}: {desc}" if step else f"{i}. {desc}"
                if cmds:
                    line += "\n   " + "\n   ".join(str(c) for c in cmds)
                parts.append(line)
            else:
                parts.append(f"{i}. {item}")
        return "\n".join(parts)
    if isinstance(val, dict):
        return "\n".join(f"{k}: {v}" for k, v in val.items())
    return str(val)
