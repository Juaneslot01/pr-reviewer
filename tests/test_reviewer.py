from unittest.mock import AsyncMock, patch

import pytest

from app.services.reviewer import _format_review, process_pr


def test_format_review_includes_sections_and_model() -> None:
    review = {
        "severity": "medium",
        "summary": "Looks fine overall.",
        "risks": ["Possible null access"],
        "suggestions": ["Add a guard"],
    }

    body = _format_review(review)

    assert "## Review" in body
    assert "**Severity:**" in body
    assert "**Summary:** Looks fine overall." in body
    assert "**Risks:**" in body
    assert "- Possible null access" in body
    assert "**Suggestions:**" in body
    assert "1. Add a guard" in body
    assert "_Model:" in body


def test_format_review_empty_lists() -> None:
    review = {
        "severity": "low",
        "summary": "No issues.",
        "risks": [],
        "suggestions": [],
    }

    body = _format_review(review)

    assert "- None" in body
    assert "1. None" in body


@pytest.mark.asyncio
async def test_process_pr_skips_duplicate() -> None:
    with patch("app.services.reviewer.database.review_exists", return_value=True):
        with patch("app.services.reviewer.github.get_pr_diff", new=AsyncMock()) as mock_diff:
            await process_pr("o", "r", 1, "sha", "opened", "title", "author")

    mock_diff.assert_not_awaited()
