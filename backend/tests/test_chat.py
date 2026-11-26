import json
from types import SimpleNamespace

import pytest
from app.main import app
from app.schemas.chat import ChatMessage
from app.services.gemini import GENERIC_ERROR, gemini_service
from fastapi.testclient import TestClient
from google.genai import errors

client = TestClient(app)
URL = "/api/chat/stream"
PAYLOAD = {"messages": [{"role": "user", "content": "Hi"}]}


def parse_events(body: str) -> list[str]:
    return [
        line.removeprefix("data: ")
        for line in body.split("\n\n")
        if line.startswith("data: ")
    ]


@pytest.fixture
def captured(monkeypatch):
    calls: list[list[ChatMessage]] = []

    async def fake_stream(messages):
        calls.append(messages)
        yield 'data: {"text": "Hel"}\n\n'
        yield 'data: {"text": "lo"}\n\n'
        yield "data: [DONE]\n\n"

    monkeypatch.setattr(gemini_service, "stream_chat", fake_stream)
    return calls


def test_stream_content_type_and_headers(captured):
    response = client.post(URL, json=PAYLOAD)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["cache-control"] == "no-cache"
    assert response.headers["x-accel-buffering"] == "no"


def test_stream_chunks_are_json_and_end_with_done(captured):
    response = client.post(URL, json=PAYLOAD)
    events = parse_events(response.text)
    assert events[-1] == "[DONE]"
    assert response.text.endswith("data: [DONE]\n\n")
    texts = [json.loads(e)["text"] for e in events[:-1]]
    assert texts == ["Hel", "lo"]


def test_multi_turn_with_timestamps_reaches_service(captured):
    payload = {
        "messages": [
            {"role": "user", "content": "Hi", "timestamp": "2024-01-01T10:00:00Z"},
            {"role": "assistant", "content": "Hello", "timestamp": "2024-01-01T10:00:02Z"},
            {"role": "user", "content": "Bye"},
        ]
    }
    response = client.post(URL, json=payload)
    assert response.status_code == 200
    assert len(captured) == 1
    messages = captured[0]
    assert [m.role for m in messages] == ["user", "assistant", "user"]
    assert [m.content for m in messages] == ["Hi", "Hello", "Bye"]
    assert [m.timestamp for m in messages] == [
        "2024-01-01T10:00:00Z",
        "2024-01-01T10:00:02Z",
        None,
    ]


def test_error_event_is_streamed_without_done(monkeypatch):
    class FailingModels:
        async def generate_content_stream(self, **kwargs):
            raise errors.APIError(500, {"error": {"message": "secret detail"}})

    fake_client = SimpleNamespace(aio=SimpleNamespace(models=FailingModels()))
    monkeypatch.setattr(gemini_service, "_client", fake_client)

    response = client.post(URL, json=PAYLOAD)
    assert response.status_code == 200
    events = parse_events(response.text)
    assert [json.loads(e) for e in events] == [{"error": GENERIC_ERROR}]
    assert "secret detail" not in response.text
    assert "[DONE]" not in response.text


def test_real_service_streams_text_with_mocked_client(monkeypatch):
    async def gen():
        yield SimpleNamespace(text="Hi ")
        yield SimpleNamespace(text="")
        yield SimpleNamespace(text="there")

    class FakeModels:
        async def generate_content_stream(self, **kwargs):
            return gen()

    fake_client = SimpleNamespace(aio=SimpleNamespace(models=FakeModels()))
    monkeypatch.setattr(gemini_service, "_client", fake_client)

    response = client.post(URL, json=PAYLOAD)
    events = parse_events(response.text)
    assert [json.loads(e) for e in events[:-1]] == [{"text": "Hi "}, {"text": "there"}]
    assert events[-1] == "[DONE]"


@pytest.mark.parametrize(
    "payload",
    [
        {"messages": [{"role": "system", "content": "Hi"}]},
        {"messages": [{"role": "user", "content": ""}]},
        {"messages": [{"role": "user"}]},
        {},
    ],
    ids=["bad-role", "empty-content", "missing-content", "missing-messages"],
)
def test_invalid_payload_returns_422(captured, payload):
    response = client.post(URL, json=payload)
    assert response.status_code == 422
    assert captured == []
