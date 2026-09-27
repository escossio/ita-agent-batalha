"""Cloud Run transport identity; domain never depends on this adapter."""
import os
import re
import time
from urllib.parse import urlsplit

SERVICES = {"web", "api", "agent", "policy", "tool-broker", "data", "finance", "observability"}


def enabled():
    value = os.getenv("ITA_PLATFORM", "local")
    if value not in {"local", "cloudrun"} or (os.getenv("K_SERVICE") and value != "cloudrun"):
        raise ValueError("INVALID_RUNTIME_PLATFORM")
    return value == "cloudrun"


def service_url(service):
    if service not in SERVICES:
        raise ValueError("UNKNOWN_SERVICE")
    value = os.environ["ITA_" + service.upper().replace("-", "_") + "_URL"]
    url = urlsplit(value)
    if (url.scheme != "https" or not url.hostname or not url.hostname.endswith(".run.app")
            or url.username or url.password or url.port or url.path or url.query or url.fragment):
        raise ValueError("CLOUD_RUN_CANONICAL_URL_REQUIRED")
    return value


def auth_request():
    from google.auth.transport.requests import Request
    class BoundedRequest(Request):
        def __call__(self, *args, **kwargs):
            kwargs["timeout"] = 5
            return super().__call__(*args, **kwargs)
    return BoundedRequest()


def outbound(audience):
    from google.oauth2.id_token import fetch_id_token
    try:
        token = fetch_id_token(auth_request(), audience)
        if not isinstance(token, str) or not token or len(token) > 8192:
            raise ValueError()
        # Cloud Run may strip the signature of X-Serverless-Authorization. Keep a
        # separate full token for application verification; never forward incoming tokens.
        return {"X-Serverless-Authorization": "Bearer " + token, "X-ITA-Service-Identity": token}
    except Exception:
        raise PermissionError("SERVICE_IDENTITY_UNAVAILABLE") from None


def inbound(service, headers):
    from google.oauth2.id_token import verify_oauth2_token
    try:
        token = headers.get("X-ITA-Service-Identity", "")
        if not token or len(token) > 8192:
            raise ValueError()
        claims = verify_oauth2_token(token, auth_request(), audience=service_url(service))
        callers = os.environ["ITA_ALLOWED_CALLERS"].split(",")
        if (claims.get("email_verified") is not True or claims.get("email") not in callers
                or not claims.get("sub") or claims.get("exp", 0) <= time.time()):
            raise ValueError()
    except Exception:
        raise PermissionError("SERVICE_IDENTITY_REQUIRED") from None


def signer_email():
    email = os.environ["ITA_IDENTITY_SIGNER"]
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]@[a-z][a-z0-9-]+\.iam\.gserviceaccount\.com", email):
        raise ValueError("INVALID_IDENTITY_SIGNER")
    return email


def sign_customer_identity(claims):
    import json
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    try:
        email = signer_email()
        now = int(time.time())
        payload = dict(iss=email, sub=email, aud=service_url("policy"), iat=now, exp=claims["expires"], ita=claims)
        credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        with AuthorizedSession(credentials, refresh_timeout=5) as session:
            session.trust_env = False
            with session.post(f"https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/{email}:signJwt",
                              json={"payload": json.dumps(payload)}, timeout=(3, 5), stream=True,
                              allow_redirects=False) as response:
                if response.status_code != 200:
                    raise ValueError()
                body = response.raw.read(8193, decode_content=True)
                if len(body) > 8192:
                    raise ValueError()
                token = json.loads(body)["signedJwt"]
                if not isinstance(token, str) or len(token) > 4096:
                    raise ValueError()
                return token
    except Exception:
        raise PermissionError("IDENTITY_SIGNING_UNAVAILABLE") from None


def verify_customer_identity(token):
    from google.oauth2.id_token import verify_token
    try:
        if not isinstance(token, str) or len(token) > 4096:
            raise ValueError()
        email = signer_email()
        claims = verify_token(token, auth_request(), audience=service_url("policy"),
                              certs_url=f"https://www.googleapis.com/service_accounts/v1/metadata/x509/{email}")
        if (claims.get("iss") != email or claims.get("sub") != email
                or not time.time() < claims.get("exp", 0) <= time.time() + 31
                or claims["ita"]["expires"] != claims["exp"]):
            raise ValueError()
        return claims["ita"]
    except Exception:
        raise PermissionError("INVALID_IDENTITY_PROOF") from None
