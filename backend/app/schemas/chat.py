from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: str
    content: str = Field(min_length=1)
    timestamp: str | None = None

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        # Gemini calls the assistant role "model"; normalize it to the API contract.
        if value == "model":
            return "assistant"
        if value not in ("user", "assistant"):
            raise ValueError("role must be 'user' or 'assistant'")
        return value


class ChatRequest(BaseModel):
    messages: list[ChatMessage]
