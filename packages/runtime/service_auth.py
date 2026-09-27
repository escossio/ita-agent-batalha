"""Workspace/runtime supplied pairwise keys; no secret or identity in logs."""
import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
import threading
import time
from uuid import uuid4
from . import cloudrun


def key(name):
    value = Path(os.environ[name]).read_bytes().strip()
    if len(value) < 32:
        raise PermissionError("INVALID_SERVICE_IDENTITY")
    return value


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sign_identity(claims):
    if cloudrun.enabled():
        return cloudrun.sign_customer_identity(claims)
    body = base64.urlsafe_b64encode(canonical(claims)).decode()
    signature = hmac.new(key("ITA_IDENTITY_KEY_FILE"), body.encode(), hashlib.sha256).hexdigest()
    return body + "." + signature


def verify_identity(token):
    try:
        if cloudrun.enabled():
            claims = cloudrun.verify_customer_identity(token)
        else:
            claims = verify_local_identity(token)
        if set(claims) != {"customer_id", "correlation_id", "window", "proposed_spend_cents", "expires", "session_hash"}:
            raise ValueError()
        if type(claims["expires"]) is not int or not time.time() < claims["expires"] <= time.time() + 31:
            raise ValueError()
        return claims
    except Exception:
        raise PermissionError("INVALID_IDENTITY_PROOF") from None


def verify_local_identity(token):
    try:
        body, signature = token.split(".")
        expected = hmac.new(key("ITA_IDENTITY_KEY_FILE"), body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError()
        claims = json.loads(base64.b64decode(body, altchars=b"-_", validate=True))
        if set(claims) != {"customer_id", "correlation_id", "window", "proposed_spend_cents", "expires", "session_hash"}:
            raise ValueError()
        if type(claims["expires"]) is not int or not time.time() < claims["expires"] <= time.time() + 31:
            raise ValueError()
        return claims
    except Exception:
        raise PermissionError("INVALID_IDENTITY_PROOF") from None


def broker_headers(path, payload, cid):
    timestamp, nonce = str(int(time.time())), str(uuid4())
    message = canonical(["POST", path, cid, timestamp, nonce, payload])
    signature = hmac.new(key("ITA_BROKER_DATA_KEY_FILE"), message, hashlib.sha256).hexdigest()
    return {"X-ITA-Time": timestamp, "X-ITA-Nonce": nonce, "X-ITA-Signature": signature}


class BrokerAuthenticator:
    def __init__(self):
        self.seen, self.lock = {}, threading.Lock()

    def __call__(self, payload, cid, headers, path):
        if cloudrun.enabled():
            # Full token signature + audience + caller allow-list, in addition to Run IAM.
            cloudrun.inbound("data", headers)
            return
        try:
            stamp, nonce, signature = (headers.get(name, "") for name in ("X-ITA-Time", "X-ITA-Nonce", "X-ITA-Signature"))
            now = time.time()
            if len(stamp) > 12 or len(nonce) != 36 or len(signature) != 64 or abs(now - int(stamp)) > 30:
                raise ValueError()
            message = canonical(["POST", path, cid, stamp, nonce, payload])
            expected = hmac.new(key("ITA_BROKER_DATA_KEY_FILE"), message, hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError()
            with self.lock:
                self.seen = {k: expiry for k, expiry in self.seen.items() if expiry >= now}
                if nonce in self.seen or len(self.seen) >= 10000:
                    raise ValueError()
                self.seen[nonce] = int(stamp) + 30
        except Exception:
            raise PermissionError("BROKER_IDENTITY_REQUIRED") from None
