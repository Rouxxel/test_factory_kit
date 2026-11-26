# API Specification

Base URL (direct): `http://localhost:8000`. Through the frontend dev server: `http://localhost:8080` (proxies `/api/*` to port 8000). There is no authentication. CORS allows the origin `http://localhost:8080` with any method and header.

## GET /api/health

Reports that the service is up and which model is configured.

**Request:** no parameters or body.

**Response `200 OK`** (`application/json`):

```json
{ "status": "ok", "model": "gemini-2.5-flash" }
```

| Field | Type | Description |
| --- | --- | --- |
| `status` | string | Always `"ok"` |
| `model` | string | Value of `MODEL_NAME` (default `gemini-2.5-flash`) |

The endpoint does not call Gemini, so it succeeds even when `GEMINI_API_KEY` is missing or invalid.

## POST /api/chat/stream

Sends the conversation history and streams the model's reply as Server-Sent Events.

### Request

`Content-Type: application/json`

```json
{
  "messages": [
    { "role": "user", "content": "Hello", "timestamp": "2026-11-26T12:00:00Z" },
    { "role": "assistant", "content": "Hi there! How can I help?", "timestamp": "2026-11-26T12:00:02Z" },
    { "role": "user", "content": "Tell me a joke", "timestamp": "2026-11-26T12:00:10Z" }
  ]
}
```

**ChatRequest**

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `messages` | array of ChatMessage | yes | Full conversation, oldest first. The list itself may be empty; the schema does not enforce a minimum. The backend keeps no state between calls. |

**ChatMessage**

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `role` | string | yes | `"user"` or `"assistant"`. The value `"model"` is accepted and normalized to `"assistant"`. Any other value fails validation. |
| `content` | string | yes | Minimum length 1. |
| `timestamp` | string or null | no | Defaults to `null`. Not parsed or validated as a date. The frontend sends an ISO 8601 UTC string. The backend does not forward it to Gemini. |

Unknown extra fields (such as the frontend's `id`) are ignored by default.

Roles are sent to Gemini as `user` for `user`, and `model` for `assistant`.

### Successful response `200 OK`

Headers:

| Header | Value |
| --- | --- |
| `Content-Type` | `text/event-stream; charset=utf-8` |
| `Cache-Control` | `no-cache` |
| `X-Accel-Buffering` | `no` (stops nginx-style proxies from buffering the stream) |

The status is `200` even if Gemini later fails. Failures that happen after the stream has started are reported as an `error` event in the body.

### SSE framing

Each event is one line `data: <payload>` followed by a blank line (`\n\n`). There are no `event:` or `id:` fields.

| Event | Wire format | Meaning |
| --- | --- | --- |
| Text delta | `data: {"text": "chunk"}\n\n` | A piece of the reply. Concatenate in order. Empty chunks are skipped. |
| Done | `data: [DONE]\n\n` | The reply completed. Last event of a successful stream. |
| Error | `data: {"error": "Failed to get a response from the model."}\n\n` | The model call failed. The stream ends right after this event, and **`[DONE]` is not sent**. |

The error message is a fixed generic string. Details are logged on the server (exception class name only) and not returned. Errors raised by `google-genai` (`APIError`), `httpx` (`HTTPError`) and `ValueError` (for example a missing API key) all produce this event. Text events may precede the error event if the failure occurs mid-stream.

Example success stream:

```text
data: {"text": "Why did the "}

data: {"text": "chicken cross the road?"}

data: [DONE]

```

Example failure stream:

```text
data: {"error": "Failed to get a response from the model."}

```

Clients should treat a stream that ends with neither `[DONE]` nor an `error` event as a failure (the frontend reports "Stream ended unexpectedly").

### Validation errors `422 Unprocessable Entity`

FastAPI rejects invalid bodies before streaming starts, with a JSON body and no SSE framing. These cases return 422:

- body missing, or `messages` missing
- a message with a `role` other than `user`, `assistant` or `model`
- a message with empty `content` or missing `content`
- wrong types (for example `messages` is not an array)

Example for `{"messages": [{"role": "bad", "content": ""}]}`:

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "messages", 0, "role"],
      "msg": "Value error, role must be 'user' or 'assistant'",
      "input": "bad",
      "ctx": { "error": {} }
    },
    {
      "type": "string_too_short",
      "loc": ["body", "messages", 0, "content"],
      "msg": "String should have at least 1 character",
      "input": "",
      "ctx": { "min_length": 1 }
    }
  ]
}
```

The exact `detail` entries come from FastAPI and Pydantic and can differ slightly between versions. The `loc` path shows which field failed.

### Other statuses

| Status | When |
| --- | --- |
| `404` | Unknown path |
| `405` | Wrong method (for example `GET /api/chat/stream`) |
| `500` | Unexpected server error before streaming starts |

## Configuration (environment)

Read from `backend/.env` (when the server runs from `backend/`) or from process environment variables.

| Variable | Default | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | empty | Gemini API key. Required for chat requests. |
| `MODEL_NAME` | `gemini-2.5-flash` | Model id used for chat and shown by `/api/health`. |
| `PORT` | `8000` | Declared in settings and `.env.example`. The listening port is set by the `--port` flag on `uvicorn`, not by this variable. |
