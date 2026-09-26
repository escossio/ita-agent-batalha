import asyncio
from packages.runtime.http_client import HttpTransport
from packages.runtime.server import serve
from .engine import Broker

broker = Broker(HttpTransport())


def execute(payload, correlation_id):
    if payload.get("correlation_id") != correlation_id:
        raise ValueError("correlation mismatch")
    result = asyncio.run(broker.execute(payload))
    return 200, result.model_dump()


if __name__ == "__main__":
    serve("tool-broker", {"/v1/execute": execute})
