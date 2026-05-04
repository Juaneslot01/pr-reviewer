import asyncio

from httpx import AsyncClient

from app.config import settings


async def get_pr_diff(owner: str, repo: str, pull_number: int) -> str:
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"
    headers = {
        "Accept": "application/vnd.github.v3.diff",
        "Authorization": f"token {settings.github_token}",
        "User-Agent": "pr_reviewer",
    }
    for attempt in range(1, 4):
        async with AsyncClient() as client:
            response = await client.get(
                base_url,
                headers=headers,
                timeout=30,
            )
        if 200 <= response.status_code < 300:
            return response.text
        if response.status_code in {403, 429}:
            await asyncio.sleep(0.5 * attempt)
            continue
        raise RuntimeError(f"{response.status_code}...{response.text}...")
    raise RuntimeError(f"{response.status_code}...{response.text}...")


async def post_pr_comment(owner: str, repo: str, issue_number: int, body: str) -> None:
    base_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"token {settings.github_token}",
        "User-Agent": "pr_reviewer",
    }
    for attempt in range(1, 4):
        async with AsyncClient() as client:
            response = await client.post(
                base_url,
                headers=headers,
                json={"body": body},
                timeout=30,
            )
        if 200 <= response.status_code < 300:
            return
        if response.status_code in {403, 429}:
            await asyncio.sleep(0.5 * attempt)
            continue
        raise RuntimeError(f"{response.status_code}...{response.text}...")
    raise RuntimeError(f"{response.status_code}...{response.text}...")
