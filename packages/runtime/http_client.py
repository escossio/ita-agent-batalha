"""Transporte interno limitado: destinos fixos, sem redirects, proxy ou payload nos logs."""
import asyncio
import json
import urllib.error
import urllib.request


class RemoteFailure(Exception):
    def __init__(self, code="DEPENDENCY_UNAVAILABLE"):
        self.code = code
        super().__init__(code)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class HttpTransport:
    ROUTES = {
        "authorize": "http://policy:8080/v1/authorize",
        "snapshot": "http://data:8080/v1/snapshot",
        "project": "http://finance:8080/v1/project",
    }

    def _post(self, destination, payload, correlation_id):
        request = urllib.request.Request(self.ROUTES[destination], data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "X-Correlation-ID": correlation_id})
        opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=2) as response:
                if response.headers.get("X-Correlation-ID") != correlation_id:
                    raise RemoteFailure("INVALID_OUTPUT")
                body = response.read(262145)
                if len(body) > 262144:
                    raise RemoteFailure("INVALID_OUTPUT")
                value = json.loads(body)
                if not isinstance(value, dict):
                    raise RemoteFailure("INVALID_OUTPUT")
                return value
        except urllib.error.HTTPError as error:
            if error.code == 422:
                raise RemoteFailure("MISSING_DATA") from None
            raise RemoteFailure() from None
        except urllib.error.URLError as error:
            if isinstance(error.reason, TimeoutError):
                raise TimeoutError() from None
            raise RemoteFailure() from None
        except (ValueError, UnicodeDecodeError):
            raise RemoteFailure("INVALID_OUTPUT") from None

    async def post(self, destination, payload, correlation_id):
        return await asyncio.to_thread(self._post, destination, payload, correlation_id)
