import asyncio
import json
import os
from pathlib import Path
from packages.contracts.models import AgentResponse
from packages.runtime.http_client import HttpTransport, RemoteFailure
from packages.runtime.server import serve, request_headers


class WebTransport(HttpTransport):
    ROUTES = {"chat": "http://api:8080/v1/chat"}
    TIMEOUT = 30

    def headers(self, destination, payload, correlation_id):
        result = super().headers(destination, payload, correlation_id)
        for name in ("Authorization", "Cookie"):
            if request_headers.get().get(name):
                result[name] = request_headers.get()[name]
        return result


def chat(payload, correlation_id):
    try:
        response = asyncio.run(WebTransport().post("chat", payload, correlation_id))
    except RemoteFailure as error:
        if error.code == "POLICY_DENIED":
            raise PermissionError("AUTHORIZATION_REQUIRED") from None
        raise
    value = AgentResponse.model_validate(response)
    if value.correlation_id != correlation_id:
        raise ValueError("correlation mismatch")
    return 200, value.model_dump()


if __name__ == "__main__":
    root = Path(__file__).parent / "static"
    pages = {"/runtime.json": ("application/json", json.dumps({"mode": os.getenv("ITA_RUNTIME_MODE", "demo")}).encode()), "/": ("text/html; charset=utf-8", (root / "index.html").read_bytes()),
             "/app.js": ("text/javascript; charset=utf-8", (root / "app.js").read_bytes()),
             "/style.css": ("text/css; charset=utf-8", (root / "style.css").read_bytes())}
    serve("web", {"/api/chat": chat}, pages=pages)
