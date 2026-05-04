from typing import List

from fastapi import APIRouter

from app.models.reviews import ReviewOut
from app.services.database import get_reviews

router = APIRouter()


@router.get("/reviews/{owner}/{repo}", response_model=List[ReviewOut])
async def get_reviews_api(owner: str, repo: str) -> List[ReviewOut]:
    return get_reviews(owner, repo)
