"""Identidade canônica de requisição; não concede autorização."""
import hashlib
import json
from .models import ToolRequest


def request_digest(request: ToolRequest) -> str:
    data = request.model_dump(exclude={"policy_decision_id"})
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
