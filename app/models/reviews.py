from datetime import datetime

from pydantic import BaseModel


class ReviewOut(BaseModel):
    id: str
    repo_full_name: str
    created_at: datetime
    pr_number: int
    pr_title: str | None
    pr_url: str
    pr_sha: str
    author_login: str | None
    event_action: str
    diff_truncated: bool | None
    llm_model: str | None
    severity: str
    summary: str
    suggestions: list[str] | None
    risks: list[str] | None
