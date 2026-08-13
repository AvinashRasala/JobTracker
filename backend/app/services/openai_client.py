"""
Thin wrapper around OpenAI's Chat Completions API using plain httpx --
consistent with the Gmail client, no heavy SDK dependency needed for a
handful of calls.
"""
import httpx

from app.config import settings

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"


class OpenAINotConfiguredError(Exception):
    pass


class OpenAIRequestError(Exception):
    pass


async def chat_completion(system_prompt: str, user_prompt: str, max_tokens: int = 700) -> str:
    if not settings.OPENAI_API_KEY:
        raise OpenAINotConfiguredError(
            "AI features aren't configured on this server yet (missing OPENAI_API_KEY)."
        )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            OPENAI_API_URL,
            headers={
                "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEFAULT_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
        )

    if resp.status_code != 200:
        raise OpenAIRequestError(f"OpenAI request failed: {resp.status_code} {resp.text}")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        raise OpenAIRequestError(f"Unexpected OpenAI response shape: {data}") from e
