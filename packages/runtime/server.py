"""HTTP de fundação: saúde, identificação da requisição e shutdown limpo."""

import json
import signal
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from time import monotonic
from uuid import UUID, uuid4


def event(service: str, name: str, **fields) -> None:
    print(json.dumps({"service": service, "event": name, **fields}), flush=True)


def serve(service: str) -> None:
    class Handler(BaseHTTPRequestHandler):
        server_version = "ITA"
        sys_version = ""

        def log_message(self, *_args):
            pass

        def do_GET(self):
            started = monotonic()
            raw = self.headers.get("X-Correlation-ID")
            try:
                correlation_id = str(UUID(raw)) if raw else str(uuid4())
            except ValueError:
                self.send_error(400, "invalid correlation ID")
                return
            if self.path == "/healthz":
                status = 200
                content_type = "application/json"
                body = json.dumps({"service": service, "status": "ok", "mode": "FOUNDATION"}).encode()
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
            self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)
            event(service, "request.completed", correlation_id=correlation_id, status=status,
                  duration_ms=round((monotonic() - started) * 1000, 3))

    server = ThreadingHTTPServer(("0.0.0.0", 8080), Handler)
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
