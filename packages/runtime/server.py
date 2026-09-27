"""HTTP de fundação: saúde, identificação da requisição e shutdown limpo."""

import json
import os
from . import cloudrun
from contextvars import ContextVar

import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import monotonic
from uuid import UUID, uuid4

request_headers = ContextVar("request_headers", default={})


def event(service: str, name: str, **fields) -> None:
    print(json.dumps({"service": service, "event": name, **fields}), flush=True)


def listen_port():
    port = int(os.getenv("PORT", "8080"))
    if not 1 <= port <= 65535:
        raise ValueError("INVALID_PORT")
    return port


def serve(service: str, routes=None, pages=None, health=None, before_route=None) -> None:
    is_cloud = cloudrun.enabled()
    if is_cloud and service != "observability" and os.getenv("ITA_RUNTIME_MODE") != "competition":
        raise ValueError("CLOUD_COMPETITION_REQUIRED")
    class Handler(BaseHTTPRequestHandler):
        server_version = "ITA"
        sys_version = ""

        def log_message(self, *_args):
            pass

        def do_POST(self):
            from pydantic import ValidationError
            started = monotonic()
            correlation_id = str(uuid4())
            status = 500
            result = {"error": "DEPENDENCY_UNAVAILABLE", "retryable": False}
            self.connection.settimeout(5)
            try:
                raw = self.headers.get("X-Correlation-ID")
                correlation_id = str(UUID(raw)) if raw else correlation_id
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 262144 or self.headers.get("Content-Type") != "application/json":
                    raise ValueError("invalid body framing")
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("unsupported transfer encoding")
                route = (routes or {}).get(self.path)
                if route is None:
                    status, result = 404, {"error": "NOT_IMPLEMENTED", "retryable": False}
                else:
                    payload = json.loads(self.rfile.read(length))
                    if not isinstance(payload, dict):
                        raise ValueError("object required")
                    if is_cloud:
                        if os.getenv("ITA_CLOUD_BOOTSTRAP") == "1":
                            raise RuntimeError("BOOTSTRAP_NOT_SERVING")
                        if service != "web":
                            cloudrun.inbound(service, self.headers)
                    if before_route:
                        before_route(payload, correlation_id, self.headers, self.path)
                    token = request_headers.set(self.headers)
                    try:
                        status, result = route(payload, correlation_id)
                    finally:
                        request_headers.reset(token)
            except (ValueError, ValidationError):
                status, result = 400, {"error": "INVALID_INPUT", "retryable": False}
            except PermissionError:
                status, result = 403, {"error": "POLICY_DENIED", "retryable": False}
            except TimeoutError:
                status, result = 504, {"error": "TIMEOUT", "retryable": True}
            except Exception:
                # Do not leak exception strings, payloads, credentials or infrastructure.
                status, result = 503, {"error": "DEPENDENCY_UNAVAILABLE", "retryable": True}
            body = json.dumps(result).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Correlation-ID", correlation_id)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
            event(service, "request.completed", correlation_id=correlation_id, status=status,
                  duration_ms=round((monotonic() - started) * 1000, 3))

        def do_GET(self):
            started = monotonic()
            raw = self.headers.get("X-Correlation-ID")
            try:
                correlation_id = str(UUID(raw)) if raw else str(uuid4())
            except ValueError:
                self.send_error(400, "invalid correlation ID")
                return
            if self.path == "/healthz":
                healthy = health() if health else True
                status = 200 if healthy else 503
                content_type = "application/json"
                body = json.dumps({"service": service, "status": "ok" if healthy else "unavailable", "mode": os.getenv("ITA_RUNTIME_MODE", "demo")}).encode()
            elif self.path in (pages or {}):
                status = 200
                content_type, body = pages[self.path]
            elif service == "web" and self.path == "/":
                status = 200
                content_type = "text/html; charset=utf-8"
                body = b'<!doctype html><html lang="pt-BR"><meta charset="utf-8"><title>ITA</title><h1>ITA</h1><p>DEMO: infraestrutura preparada. Jornadas ainda n\xc3\xa3o implementadas.</p></html>'
            else:
                status = 404
                content_type = "application/json"
                body = b'{"error":"NOT_IMPLEMENTED","retryable":false}'
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Correlation-ID", correlation_id)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)
            event(service, "request.completed", correlation_id=correlation_id, status=status,
                  duration_ms=round((monotonic() - started) * 1000, 3))

    server = ThreadingHTTPServer(("0.0.0.0", listen_port()), Handler)
    server.daemon_threads = True

    def stop(_number, _frame):
        event(service, "shutdown.requested")
        threading.Thread(target=server.shutdown, daemon=True).start()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    event(service, "startup.ready")
    try:
        server.serve_forever(poll_interval=0.1)
    finally:
        server.server_close()
        event(service, "shutdown.completed")
