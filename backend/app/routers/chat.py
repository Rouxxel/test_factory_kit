from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest
from app.services.gemini import gemini_service

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    return StreamingResponse(
        gemini_service.stream_chat(request.messages),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
