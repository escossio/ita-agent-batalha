"""Ports substituíveis; mock explícito não é um modelo real nem fallback."""
import os
from typing import Protocol
import unicodedata
from .models import ModelPlan, NarrativePlan


class ModelProvider(Protocol):
    name: str
    async def interpret(self, utterance: str) -> dict: ...
    async def compose(self, outcome: str, uncertain: bool) -> dict: ...


class MockProvider:
    name = "mock"

    async def interpret(self, utterance):
        text = ''.join(c for c in unicodedata.normalize('NFKD', utterance.lower()) if not unicodedata.combining(c))
        if any(term in text for term in ("ignore", "prompt", "configuracao", "sql", "invente", "senha", "token")):
            intent = "unknown"
        elif any(term in text for term in ("agora nao", "nao quero", "pare")):
            intent = "end_conversation"
        elif any(term in text for term in ("humano", "desesper", "me machucar", "suicid")):
            intent = "handoff"
        elif any(term in text for term in ("salario", "ate receber", "proxima renda")):
            intent = "project_cashflow"
        else:
            intent = "unknown"
        return ModelPlan(intent=intent, tool="finance.project" if intent == "project_cashflow" else "none").model_dump()

    async def compose(self, outcome, uncertain):
        return NarrativePlan(introduction="supportive" if outcome == "negative" else "direct",
                             closing="customer_choice").model_dump()


def configured_provider() -> ModelProvider:
    name = os.getenv("ITA_MODEL_PROVIDER", "mock")
    if name == "mock":
        return MockProvider()
    if name == "vertex":
        from .vertex import VertexGeminiProvider
        return VertexGeminiProvider(os.getenv("GOOGLE_CLOUD_PROJECT", ""),
                              os.getenv("GOOGLE_CLOUD_LOCATION", ""), os.getenv("ITA_VERTEX_MODEL", ""))
    raise ValueError("unsupported model provider")
