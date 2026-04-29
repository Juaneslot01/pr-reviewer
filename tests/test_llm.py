from unittest.mock import patch

import pytest

from app.services.llm import review_diff


@pytest.mark.asyncio
async def test_llm_valid_diff() -> None:
    response_data = {
        "choices": [
            {
                "message": {
                    "content": '{"severity":"low","risks":[],"suggestions":[],"summary":"Ok"}'
                }
            }
        ]
    }

    with patch("app.services.llm.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 200
        mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = (
            response_data
        )
        result = await review_diff("diff")

    assert result["severity"] == "low"
    assert result["summary"] == "Ok"


@pytest.mark.asyncio
async def test_llm_malformed_json() -> None:
    response_data = {
        "choices": [{"message": {"content": "{not json"}}]
    }

    with patch("app.services.llm.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 200
        mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = (
            response_data
        )
        result = await review_diff("diff")

    assert result["severity"] == "low"
    assert result["suggestions"] == ["Could not parse LLM response."]


@pytest.mark.asyncio
async def test_llm_truncates_large_diff() -> None:
    response_data = {
        "choices": [
            {
                "message": {
                    "content": '{"severity":"low","risks":[],"suggestions":[],"summary":"Ok"}'
                }
            }
        ]
    }

    large_diff = "a" * 13000

    with patch("app.services.llm.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 200
        mock_client.return_value.__aenter__.return_value.post.return_value.json.return_value = (
            response_data
        )
        result = await review_diff(large_diff)

    assert result["summary"] == "Ok"


@pytest.mark.asyncio
async def test_llm_empty_diff_skips_call() -> None:
    with patch("app.services.llm.httpx.AsyncClient") as mock_client:
        result = await review_diff("   ")

    assert result["summary"] == "No changes to review."
    mock_client.assert_not_called()
