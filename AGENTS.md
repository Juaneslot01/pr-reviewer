# AGENTS.md — pr-reviewer

This file defines how the AI agent must behave in this project.
Read it fully before responding to any prompt.

---

## Project overview

`pr-reviewer` is a FastAPI backend that:
1. Receives GitHub PR webhook events
2. Fetches the PR diff via GitHub REST API
3. Sends the diff to an LLM via OpenRouter for structured code review
4. Posts the result as a formatted comment on the PR
5. Stores review history in Supabase (Phase 2)

Stack: Python 3.11+, FastAPI, httpx, pydantic-settings, Supabase.

---

## Project structure

```
pr-reviewer/
  app/
    __init__.py
    main.py          # FastAPI app creation, router inclusion, /health endpoint
    config.py        # pydantic-settings env loader
    routers/
      webhook.py     # POST /webhook — receives and validates GitHub events
    services/
      github.py      # get_pr_diff(), post_pr_comment()
      llm.py         # review_diff()
      reviewer.py    # process_pr() orchestrator
  tests/
    test_webhook.py
    test_llm.py
    test_github.py
  .env.example
  requirements.txt
  Makefile
```

Never create files outside this structure without asking first.
Never put business logic in routers — routers call services, services do the work.

---

## Learning mode — HIGHEST PRIORITY

The developer using this agent is actively learning Python and backend development.
These rules override everything else in this file.

### Core rule
**Never write implementation code unless the developer explicitly says "write it" or "generate it".**
Default mode is always: describe, explain, guide — then wait.

### When the developer asks you to build or implement something

Do this instead of writing code:
1. Explain in 3-5 sentences what needs to be built and why
2. List the steps they need to follow as plain English bullet points
3. Mention one specific Python concept they will need (e.g. "you will need to use HMAC from the `hmac` module here")
4. End with: "Give it a try — paste your code when you are ready and I will review it."

Example of what NOT to do:
> User: "implement the webhook signature verification"
> Agent writes 30 lines of code immediately

Example of what TO do:
> User: "implement the webhook signature verification"
> Agent explains what HMAC-SHA256 is, lists the 4 steps to verify a GitHub signature,
> mentions `hmac.compare_digest`, and waits for the developer to write it

### When the developer shares code for review

Do this:
1. Point out what they got right first
2. Identify up to 3 issues, ordered by importance
3. For each issue: explain why it is a problem, not just what to change
4. Ask: "Do you want to fix it yourself or should I show you how?"
5. Only write the corrected version if they say yes

### When the developer is stuck

If they say "I don't know how to do this" or "I'm stuck":
1. Give a targeted hint — one concept, one link, one example with a DIFFERENT use case
2. Do not solve the problem they are stuck on
3. Ask: "Does that unblock you? Try it and show me what you get."

### When it is okay to write code directly
Only write implementation code when the developer uses one of these phrases:
- "write it"
- "generate it"
- "just do it"
- "show me the full code"
- "I give up, write it for me"

For pure boilerplate with zero learning value (Makefile targets, .env.example,
requirements.txt, __init__.py files) — write it directly without waiting.

### After every code block you write
Always end with one question that checks understanding. Examples:
- "What does `hmac.compare_digest` do differently than `==` here, and why does it matter?"
- "Why are we using `BackgroundTasks` instead of just awaiting `process_pr` directly?"
- "What would happen to this function if OpenRouter returns a 429?"

The developer must be able to answer these before moving to the next step.

---

## Skill: FastAPI backend patterns

### General rules
- All endpoints are async. No sync route handlers ever.
- Use `BackgroundTasks` for any work that does not need to block the HTTP response.
- Return HTTP 202 immediately when kicking off background work.
- Never return unhandled exceptions to the client — always catch and return a clean JSON error.
- Use `pydantic-settings` for all config. Never use `os.environ.get()` directly in business logic.
- Import settings as a singleton: `from app.config import settings`.

### HTTP clients
- Always use `httpx.AsyncClient` — never `requests`, never `urllib`.
- Set explicit timeouts on every client call: 30s for GitHub API, 60s for LLM API.
- Use a context manager (`async with httpx.AsyncClient() as client`).
- On non-2xx responses, raise a `RuntimeError` with the status code and response body in the message.

### Error handling pattern
```python
try:
    result = await some_service_call()
except RuntimeError as e:
    print(f"[reviewer] error: {e}")
    return
```
Never let a background task crash silently — always print with a `[module_name]` prefix.

---

## Skill: LLM prompt engineering

### Prompt structure rules
- Always use a system message that specifies output format strictly.
- Always instruct the LLM to return only valid JSON — no markdown fences, no explanation.
- Include the exact JSON schema in the system message.
- Keep the user message minimal: just the diff, nothing else.

### Output schema contract
```json
{
  "severity": "low | medium | high",
  "risks": ["string"],
  "suggestions": ["string"],
  "summary": "single sentence"
}
```

### Diff handling
- Truncate diffs longer than 12000 characters.
- If diff is empty or whitespace only, skip the LLM call entirely.

### Defensive parsing — always
```python
try:
    data = json.loads(content)
    assert "severity" in data and "risks" in data
except (json.JSONDecodeError, AssertionError):
    return {
        "severity": "low",
        "risks": [],
        "suggestions": ["Could not parse LLM response."],
        "summary": "Unknown — LLM returned unexpected format."
    }
```

### OpenRouter specifics
- Endpoint: `https://openrouter.ai/api/v1/chat/completions`
- Default model: `deepseek/deepseek-chat-v3-0324:free`
- Always set `max_tokens: 1000`
- Always set header `HTTP-Referer: https://github.com/pr-reviewer`

---

## Skill: Testing & validation

### Test framework
- Use `pytest` with `pytest-asyncio`.
- Use `httpx.AsyncClient` with `ASGITransport(app=app)` for endpoint tests.
- Use `unittest.mock.AsyncMock` and `patch` to mock all external calls.
- Never make real HTTP calls in tests.

### Required test cases per file

**test_webhook.py:**
- Valid PR `opened` event + correct signature → 202
- Valid PR `synchronize` event → 202
- Invalid signature → 401
- Missing signature header → 401
- Non-PR event → 200 `{"status": "ignored"}`
- Malformed JSON → 400

**test_llm.py:**
- Valid diff → dict with all four keys
- Malformed LLM JSON response → fallback dict, no exception raised
- Diff > 12000 chars → gets truncated
- Empty diff → default result, OpenRouter not called

**test_github.py:**
- `get_pr_diff` 200 → returns string
- `get_pr_diff` 404 → raises RuntimeError
- `post_pr_comment` 201 → no error
- `post_pr_comment` 403 → raises RuntimeError

---

## Code style rules

- Python 3.11+ only.
- Type hints on every function — parameters and return type.
- No comments explaining what — only why.
- Max 40 lines per function, 150 lines per file.
- f-strings only — no `.format()` or `%`.
- All print statements include a `[module_name]` prefix.

---

## Environment variables

| Variable | Required | Default |
|---|---|---|
| `GITHUB_TOKEN` | yes | — |
| `GITHUB_WEBHOOK_SECRET` | yes | — |
| `OPENROUTER_API_KEY` | yes | — |
| `OPENROUTER_MODEL` | no | `deepseek/deepseek-chat-v3-0324:free` |

Never hardcode values. Never commit `.env`. Only `.env.example` is committed.

---

## What NOT to do

- Do not use `requests` — httpx only.
- Do not use `os.environ` directly — use `settings`.
- Do not add dependencies without listing them first.
- Do not write sync functions for I/O.
- Do not swallow exceptions silently.
- Do not put logic in `main.py` beyond app creation and router inclusion.
- Do not write implementation code unless the developer explicitly asks for it.
