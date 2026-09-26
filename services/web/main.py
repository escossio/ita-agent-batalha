import asyncio
from pathlib import Path
from packages.contracts.models import AgentResponse
from packages.runtime.http_client import HttpTransport
from packages.runtime.server import serve


class WebTransport(HttpTransport):
    ROUTES = {"chat": "http://api:8080/v1/chat"}
    TIMEOUT = 30


def chat(payload, correlation_id):
    response = asyncio.run(WebTransport().post("chat", payload, correlation_id))
    value = AgentResponse.model_validate(response)
    if value.correlation_id != correlation_id:
        raise ValueError("correlation mismatch")
    return 200, value.model_dump()


if __name__ == "__main__":
    root = Path(__file__).parent / "static"
    pages = {"/": ("text/html; charset=utf-8", (root / "index.html").read_bytes()),
             "/app.js": ("text/javascript; charset=utf-8", (root / "app.js").read_bytes()),
             "/style.css": ("text/css; charset=utf-8", (root / "style.css").read_bytes())}
    serve("web", {"/api/chat": chat}, pages=pages)
