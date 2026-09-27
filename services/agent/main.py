import asyncio
from packages.runtime.http_client import HttpTransport
from packages.runtime.server import serve
from .orchestrator import Orchestrator
from .providers import configured_provider


class AgentTransport(HttpTransport):
    TIMEOUT = 12
    ROUTES = {"authorize": "http://policy:8080/v1/authorize", "execute": "http://tool-broker:8080/v1/execute"}


def respond(payload, correlation_id):
    if payload.get("correlation_id") != correlation_id:
        raise ValueError("correlation mismatch")
    agent = Orchestrator(configured_provider(), AgentTransport())
    return 200, asyncio.run(agent.run(payload)).model_dump()


if __name__ == "__main__":
    serve("agent", {"/v1/respond": respond})
