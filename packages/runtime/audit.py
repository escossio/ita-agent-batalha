import json
from datetime import datetime, timezone
from uuid import uuid4
from packages.contracts.models import AuditEvent


def audit(correlation_id, component, name, status, sink=None, **fields):
    record = AuditEvent(schema_version="1.0", event_id=str(uuid4()), correlation_id=correlation_id,
                        occurred_at=datetime.now(timezone.utc).isoformat(), component=component,
                        event=name, status=status, **fields)
    if sink is not None:
        sink(record)
    else:
        print(json.dumps(record.model_dump(exclude_none=True)), flush=True)
