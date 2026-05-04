import hashlib
import hmac
from http import HTTPStatus
from json import JSONDecodeError

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.reviewer import process_pr

router = APIRouter()


@router.post("/webhook")
async def webhook_handler(
    request: Request, background_tasks: BackgroundTasks
) -> JSONResponse:

    body = await request.body()
    verify_webhook(body, request.headers.get("X-Hub-Signature-256"))

    try:
        data = await request.json()
    except JSONDecodeError:
        raise HTTPException(status_code=400, detail="Malformed JSON")

    status, message = pull_request_verification(data)

    try:
        if status == HTTPStatus.ACCEPTED:
            owner, repo, pr_number, pr_sha, event_action, pr_title, author_login = (
                extract_pr_details(data)
            )
            background_tasks.add_task(
                process_pr,
                owner,
                repo,
                pr_number,
                pr_sha,
                event_action,
                pr_title,
                author_login,
            )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return JSONResponse(status_code=status.value, content={"status": message})


def verify_webhook(payload_body: bytes, signature_header: str | None) -> None:
    if not signature_header:
        raise HTTPException(
            status_code=401, detail="X-Hub-Signature-256 header is missing!"
        )
    secret = settings.github_webhook_secret.encode("utf-8")
    digest = hmac.new(secret, msg=payload_body, digestmod=hashlib.sha256).hexdigest()
    expected = f"sha256={digest}"

    if not hmac.compare_digest(expected, signature_header):
        raise HTTPException(status_code=401, detail="Invalid signature!")


def pull_request_verification(data: dict) -> tuple[HTTPStatus, str]:
    if "pull_request" not in data:
        return (HTTPStatus.OK, "ignored")

    action = data.get("action")
    if action in {"opened", "synchronize"}:
        return (HTTPStatus.ACCEPTED, "accepted")
    else:
        return (HTTPStatus.OK, "ignored")


def extract_pr_details(data: dict) -> tuple[str, str, int, str, str, str, str]:
    try:
        owner = data["repository"]["owner"]["login"]
        repo = data["repository"]["name"]
        pr_number = data["pull_request"]["number"]
        pr_sha = data["pull_request"]["head"]["sha"]
        event_action = data["action"]
        pr_title = data["pull_request"]["title"]
        author_login = data["pull_request"]["user"]["login"]
    except (KeyError, TypeError):
        raise RuntimeError("Malformed PR payload")

    if (
        not isinstance(owner, str)
        or not isinstance(repo, str)
        or not isinstance(pr_number, int)
        or not isinstance(pr_sha, str)
        or not isinstance(event_action, str)
        or not isinstance(pr_title, str)
        or not isinstance(author_login, str)
    ):
        raise RuntimeError("Malformed PR payload")

    return owner, repo, pr_number, pr_sha, event_action, pr_title, author_login
