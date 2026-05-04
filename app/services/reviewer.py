from app.config import settings
from app.services import database, github, llm


async def process_pr(
    owner: str,
    repo: str,
    pr_number: int,
    pr_sha: str,
    event_action: str,
    pr_title: str,
    author_login: str,
) -> None:
    context = f"{owner}/{repo}#{pr_number} {event_action} {pr_sha}"
    try:
        if database.review_exists(owner, repo, pr_number, pr_sha, event_action):
            print(f"[reviewer] skip duplicate: {context}")
            return
        diff = await github.get_pr_diff(owner, repo, pr_number)
        review = await llm.review_diff(diff)
        review_body = _format_review(review)
        await github.post_pr_comment(owner, repo, pr_number, review_body)
        data = {
            "risks": review.get("risks"),
            "suggestions": review.get("suggestions"),
            "summary": review.get("summary"),
            "severity": review.get("severity"),
            "repo_full_name": f"{owner}/{repo}",
            "pr_number": pr_number,
            "pr_url": f"https://github.com/{owner}/{repo}/pull/{pr_number}",
            "pr_sha": pr_sha,
            "event_action": event_action,
            "llm_model": settings.openrouter_model,
            "diff_truncated": review.get("diff_truncated"),
            "pr_title": pr_title,
            "author_login": author_login,
        }
        database.save_review(data)
    except RuntimeError as e:
        print(f"[reviewer] error: {context}: {e}")


def _format_review(review: dict[str, object]) -> str:
    risks = _format_list(review.get("risks"))
    suggestions = _format_numbered_list(review.get("suggestions"))
    summary = review.get("summary", "")
    severity = review.get("severity", "low")
    severity_emoji = _severity_emoji(severity)
    model_name = settings.openrouter_model
    return (
        "## Review\n\n"
        f"**Severity:** {severity_emoji} {severity}\n\n"
        f"**Summary:** {summary}\n\n"
        "**Risks:**\n"
        f"{risks}\n\n"
        "**Suggestions:**\n"
        f"{suggestions}\n\n"
        f"_Model: {model_name}_"
    )


def _format_list(items: object) -> str:
    if not isinstance(items, list):
        return "- None"
    strings = [item for item in items if isinstance(item, str)]
    if len(strings) == 0:
        return "- None"
    return "\n".join([f"- {item}" for item in strings])


def _format_numbered_list(items: object) -> str:
    if not isinstance(items, list):
        return "1. None"
    strings = [item for item in items if isinstance(item, str)]
    if len(strings) == 0:
        return "1. None"
    return "\n".join([f"{index + 1}. {item}" for index, item in enumerate(strings)])


def _severity_emoji(severity: object) -> str:
    if severity == "high":
        return "\U0001f534"
    if severity == "medium":
        return "\U0001f7e1"
    return "\U0001f7e2"
