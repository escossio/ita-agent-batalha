"""Transporte interno limitado: destinos fixos, sem redirects, proxy ou payload nos logs."""
import asyncio
import json
from urllib.parse import urlsplit
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
    TIMEOUT = 2
    ROUTES = {
        "authorize": "http://policy:8080/v1/authorize",
        "snapshot": "http://data:8080/v1/snapshot",
        "project": "http://finance:8080/v1/project",
        "ledger": "http://data:8080/v1/ledger",
        "assess": "http://finance:8080/v1/assess-ledger",
    }

    def headers(self, destination, payload, correlation_id):
        result = {"Content-Type": "application/json", "X-Correlation-ID": correlation_id}
        if destination in {"snapshot", "ledger"}:
            from .service_auth import broker_headers
            result.update(broker_headers(urlsplit(self.ROUTES[destination]).path, payload, correlation_id))
        return result

    def _post(self, destination, payload, correlation_id):
        request = urllib.request.Request(self.ROUTES[destination], data=json.dumps(payload).encode(),
            headers=self.headers(destination, payload, correlation_id))
        opener = urllib.request.build_opener(NoRedirect, urllib.request.ProxyHandler({}))
        try:
            with opener.open(request, timeout=8 if destination == "ledger" else self.TIMEOUT) as response:
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
            if destination == "ledger" and error.code in {503, 504}:
                try:
                    failure = json.loads(error.read(4097)).get("error")
                except Exception:
                    failure = None
                if failure in {"SOURCE_AUTHENTICATION_FAILED", "SOURCE_SCHEMA_MISMATCH", "SOURCE_REGION_MISMATCH", "SOURCE_NOT_FOUND", "SOURCE_INVALID_DATA", "TIMEOUT"}:
                    raise RemoteFailure(failure) from None
            if error.code == 403:
                raise RemoteFailure("POLICY_DENIED") from None
            if error.code == 504:
                raise TimeoutError() from None
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
