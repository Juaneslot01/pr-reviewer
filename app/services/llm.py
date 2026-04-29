import inspect
import json

import httpx

from app.config import settings


def _build_messages(diff: str) -> list[dict[str, str]]:
    system_message = (
        "You are a senior code reviewer. Return only valid JSON. "
        "Do not wrap in markdown fences. Do not include any other text. "
        "Return JSON with this exact schema: "
        '{"severity":"low|medium|high","risks":["string"],"suggestions":["string"],"summary":"single sentence"}.'
    )
    user_message = diff
    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def _truncate_diff(diff: str, limit: int = 12000) -> str:
    return diff[:limit]


def _default_review() -> dict[str, object]:
    return {
        "severity": "low",
        "risks": [],
        "suggestions": ["Could not parse LLM response."],
        "summary": "Unknown - LLM returned unexpected format.",
    }


async def review_diff(diff: str) -> dict[str, object]:
    if diff.strip() == "":
        return {
            "severity": "low",
            "risks": [],
            "suggestions": [],
            "summary": "No changes to review.",
        }

    diff = _truncate_diff(diff)
    payload = {
        "model": settings.openrouter_model,
        "max_tokens": 1000,
        "messages": _build_messages(diff),
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "HTTP-Referer": "https://github.com/pr-reviewer",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            json=payload,
            headers=headers,
        )

    if response.status_code < 200 or response.status_code >= 300:
        raise RuntimeError(f"OpenRouter error {response.status_code}: {response.text}")

    parsed = response.json()
    if inspect.isawaitable(parsed):
        parsed = await parsed
    content = parsed["choices"][0]["message"]["content"]
    try:
        data = json.loads(content)
        assert isinstance(data, dict)
        assert data.get("severity") in {"low", "medium", "high"}
        assert isinstance(data.get("risks"), list)
        assert isinstance(data.get("suggestions"), list)
        assert isinstance(data.get("summary"), str)
        return data
    except (json.JSONDecodeError, AssertionError):
        return _default_review()
