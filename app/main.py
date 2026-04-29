from fastapi import FastAPI

from app.config import settings
from app.routers.webhook import router as webhook_router

app = FastAPI()
app.include_router(webhook_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "model": settings.openrouter_model}
