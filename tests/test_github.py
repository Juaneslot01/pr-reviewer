from unittest.mock import patch

import pytest

from app.services.github import get_pr_diff, post_pr_comment


@pytest.mark.asyncio
async def test_get_pr_diff_200() -> None:
    with patch("app.services.github.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value.text = "diff"
        result = await get_pr_diff("o", "r", 1)

    assert result == "diff"


@pytest.mark.asyncio
async def test_get_pr_diff_404() -> None:
    with patch("app.services.github.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 404
        mock_client.return_value.__aenter__.return_value.get.return_value.text = "not found"
        with pytest.raises(RuntimeError):
            await get_pr_diff("o", "r", 1)


@pytest.mark.asyncio
async def test_post_pr_comment_201() -> None:
    with patch("app.services.github.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 201
        await post_pr_comment("o", "r", 1, "body")


@pytest.mark.asyncio
async def test_post_pr_comment_403() -> None:
    with patch("app.services.github.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.post.return_value.status_code = 403
        mock_client.return_value.__aenter__.return_value.post.return_value.text = "forbidden"
        with pytest.raises(RuntimeError):
            await post_pr_comment("o", "r", 1, "body")


@pytest.mark.asyncio
async def test_get_pr_diff_retries_on_429() -> None:
    with patch("app.services.github.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get.return_value.status_code = 429
        mock_client.return_value.__aenter__.return_value.get.return_value.text = "rate limited"
        with pytest.raises(RuntimeError):
            await get_pr_diff("o", "r", 1)
