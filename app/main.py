from fastapi import FastAPI

from app.config import settings
from app.routers.reviews import router as reviews_router
from app.routers.webhook import router as webhook_router
from app.services.database import health_check

app = FastAPI()
app.include_router(webhook_router)
app.include_router(reviews_router)


@app.get("/health")
async def health() -> dict[str, str]:
    supabase_ok = health_check()
    status = "ok" if supabase_ok else "degraded"
    return {
        "status": status,
        "model": settings.openrouter_model,
        "supabase": "ok" if supabase_ok else "unavailable",
    }
