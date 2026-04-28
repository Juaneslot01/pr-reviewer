from httpx import AsyncClient

from app.config import settings


async def get_pr_diff(owner: str, repo: str, pull_number: int) -> str:
    base_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pull_number}"

    async with AsyncClient() as client:
        response = await client.get(
            base_url,
            headers={
                "Accept": "application/vnd.github.v3.diff",
                "Authorization": f"token {settings.github_token}",
                "User-Agent": "pr_reviewer",
            },
            timeout=30,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"{response.status_code}...{response.text}...")
        return response.text


async def post_pr_comment(owner: str, repo: str, issue_number: int, body: str) -> None:
    base_url = (
        f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
    )
    async with AsyncClient() as client:
        response = await client.post(
            base_url,
            headers={
                "Accept": "application/vnd.github.v3+json",
                "Authorization": f"token {settings.github_token}",
                "User-Agent": "pr_reviewer",
            },
            json={
                "body": body,
            },
            timeout=30,
        )
        if response.status_code < 200 or response.status_code >= 300:
            raise RuntimeError(f"{response.status_code}...{response.text}...")
