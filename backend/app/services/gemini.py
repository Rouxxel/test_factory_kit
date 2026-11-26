import json
import logging
from collections.abc import AsyncIterator

import httpx
from google import genai
from google.genai import errors, types

from app.config import settings
from app.schemas.chat import ChatMessage

logger = logging.getLogger(__name__)

GENERIC_ERROR = "Failed to get a response from the model."


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


class GeminiService:
    def __init__(self) -> None:
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        # Created lazily so importing this module works without an API key.
        if self._client is None:
            self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
        return self._client

    @staticmethod
    def build_contents(messages: list[ChatMessage]) -> list[types.Content]:
        return [
            types.Content(
                role="model" if m.role == "assistant" else "user",
                parts=[types.Part(text=m.content)],
            )
            for m in messages
        ]

    async def stream_chat(self, messages: list[ChatMessage]) -> AsyncIterator[str]:
        try:
            stream = await self.client.aio.models.generate_content_stream(
                model=settings.MODEL_NAME,
                contents=self.build_contents(messages),
            )
            async for chunk in stream:
                if chunk.text:
                    yield _sse({"text": chunk.text})
        except (errors.APIError, httpx.HTTPError, ValueError) as exc:
            # Log only the exception type: messages may echo request details.
            logger.error("Gemini streaming failed: %s", type(exc).__name__)
            yield _sse({"error": GENERIC_ERROR})
            return
        yield "data: [DONE]\n\n"


gemini_service = GeminiService()
