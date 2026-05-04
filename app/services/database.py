import time
from typing import List

from supabase import create_client

from app.config import settings
from app.models.reviews import ReviewOut

__all__ = ["client", "get_reviews", "review_exists", "save_review"]

client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key,
)


def save_review(review: dict, attempts: int = 3, delay_seconds: float = 0.5) -> None:
    for attempt in range(1, attempts + 1):
        try:
            client.table("pr-review").insert(review).execute()
            return
        except Exception as e:
            print(f"[supabase] insert failed (attempt {attempt}): {e}")
            if attempt < attempts:
                time.sleep(delay_seconds * attempt)


def get_reviews(owner: str, repo: str) -> List[ReviewOut]:
    try:
        reviews = (
            client.table("pr-review")
            .select("*")
            .eq("repo_full_name", f"{owner}/{repo}")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        reviews_data = reviews.data
        reviews_out = [ReviewOut.model_validate(review) for review in reviews_data]

    except Exception as e:
        print(f"[supabase] select failed: {e}")
        return []
    return reviews_out


def review_exists(
    owner: str,
    repo: str,
    pr_number: int,
    pr_sha: str,
    event_action: str,
) -> bool:
    try:
        response = (
            client.table("pr-review")
            .select("id")
            .eq("repo_full_name", f"{owner}/{repo}")
            .eq("pr_number", pr_number)
            .eq("pr_sha", pr_sha)
            .eq("event_action", event_action)
            .limit(1)
            .execute()
        )
        return len(response.data) > 0
    except Exception as e:
        print(f"[supabase] exists check failed: {e}")
        return False


def health_check() -> bool:
    try:
        client.table("pr-review").select("id").limit(1).execute()
        return True
    except Exception as e:
        print(f"[supabase] health check failed: {e}")
        return False
