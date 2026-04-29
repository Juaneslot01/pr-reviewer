import hashlib
import hmac

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, patch

from app.config import settings
from app.main import app


def _sign(body: bytes) -> str:
    secret = settings.github_webhook_secret.encode("utf-8")
    digest = hmac.new(secret, body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_webhook_pr_opened_valid_signature() -> None:
    payload = {
        "action": "opened",
        "repository": {"name": "repo", "owner": {"login": "owner"}},
        "pull_request": {"number": 123},
    }
    body = _json_bytes(payload)
    headers = {"X-Hub-Signature-256": _sign(body)}

    with patch("app.routers.webhook.process_pr", new=AsyncMock()) as mock_task:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/webhook", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    mock_task.assert_awaited_once_with("owner", "repo", 123)


@pytest.mark.asyncio
async def test_webhook_pr_synchronize_valid_signature() -> None:
    payload = {
        "action": "synchronize",
        "repository": {"name": "repo", "owner": {"login": "owner"}},
        "pull_request": {"number": 456},
    }
    body = _json_bytes(payload)
    headers = {"X-Hub-Signature-256": _sign(body)}

    with patch("app.routers.webhook.process_pr", new=AsyncMock()) as mock_task:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/webhook", content=body, headers=headers)

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    mock_task.assert_awaited_once_with("owner", "repo", 456)


@pytest.mark.asyncio
async def test_webhook_invalid_signature() -> None:
    payload = {
        "action": "opened",
        "repository": {"name": "repo", "owner": {"login": "owner"}},
        "pull_request": {"number": 1},
    }
    body = _json_bytes(payload)
    headers = {"X-Hub-Signature-256": "sha256=bad"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/webhook", content=body, headers=headers)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_missing_signature() -> None:
    payload = {
        "action": "opened",
        "repository": {"name": "repo", "owner": {"login": "owner"}},
        "pull_request": {"number": 1},
    }
    body = _json_bytes(payload)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/webhook", content=body)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_webhook_non_pr_event() -> None:
    payload = {"action": "opened"}
    body = _json_bytes(payload)
    headers = {"X-Hub-Signature-256": _sign(body)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/webhook", content=body, headers=headers)

    assert response.status_code == 200
    assert response.json() == {"status": "ignored"}


@pytest.mark.asyncio
async def test_webhook_malformed_json() -> None:
    body = b"{not json}"
    headers = {"X-Hub-Signature-256": _sign(body)}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/webhook", content=body, headers=headers)

    assert response.status_code == 400


def _json_bytes(payload: dict) -> bytes:
    import json

    return json.dumps(payload).encode("utf-8")
