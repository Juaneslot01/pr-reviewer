import hashlib
import hmac
from http import HTTPStatus

from fastapi import APIRouter, HTTPException

from app.config import settings

router = APIRouter()


@router.post("/webhook")
async def webhook_handler():
    pass


def verify_webhook(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        raise HTTPException(
            status_code=401, detail="X-Hub-Signature-256 header is missing!"
        )
    secret = settings.github_webhook_secret.encode("utf-8")
    digest = hmac.new(secret, payload_body, hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature!")
    return True


def pull_request_verification(data: dict) -> tuple[HTTPStatus, str]:
    if "pull_request" not in data:
        return (HTTPStatus.OK, "ignored")

    action = data.get("action")
    if action in {"opened", "synchronize"}:
        return (HTTPStatus.OK, "accepted")
    else:
        return (HTTPStatus.OK, "ignored")
