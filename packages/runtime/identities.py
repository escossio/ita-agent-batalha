"""External, revocable identity bindings. Never accept a client-selected customer."""
from datetime import datetime, timezone
import hashlib
from http.cookies import SimpleCookie
import json
import os
from pathlib import Path
from typing import Annotated
from pydantic import Field, model_validator
from packages.contracts.base import Record, Timestamp, Digest
from packages.contracts.models import CustomerContext


class IdentityBinding(Record):
    context: CustomerContext
    source_user_id: Annotated[str, Field(min_length=1, max_length=256)]
    session_hash: Digest
    expires_at: Timestamp
    max_window_days: Annotated[int, Field(ge=1, le=366)]


class IdentityRegistry(Record):
    bindings: Annotated[list[IdentityBinding], Field(max_length=10000)]

    @model_validator(mode="after")
    def unique_bindings(self):
        if len({b.context.customer_id for b in self.bindings}) != len(self.bindings) or len({b.session_hash for b in self.bindings}) != len(self.bindings):
            raise ValueError("ambiguous identity mapping")
        if any(b.context.mode != "COMPETITION" for b in self.bindings):
            raise ValueError("external identities require competition context")
        return self


def bindings():
    return IdentityRegistry.model_validate(json.loads(Path(os.environ["ITA_IDENTITY_REGISTRY_FILE"]).read_text())).bindings


def active(binding):
    return datetime.fromisoformat(binding.expires_at.replace("Z", "+00:00")) > datetime.now(timezone.utc)


def for_customer(customer):
    match = next((b for b in bindings() if b.context.customer_id == customer and active(b)), None)
    if match is None:
        raise PermissionError("UNKNOWN_CUSTOMER")
    return match


def authenticate(headers):
    try:
        value = headers.get("Authorization", "")
        if value.startswith("Bearer "):
            token = value[7:]
        else:
            cookie = SimpleCookie(headers.get("Cookie", ""))
            token = cookie["ita_session"].value
        if not 32 <= len(token) <= 512:
            raise ValueError()
        digest = hashlib.sha256(token.encode()).hexdigest()
        match = next((b for b in bindings() if b.session_hash == digest and active(b)), None)
        if match is None:
            raise ValueError()
        return match
    except Exception:
        raise PermissionError("AUTHENTICATED_SESSION_REQUIRED") from None
