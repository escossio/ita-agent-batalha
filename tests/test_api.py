import contextlib
import io
import unittest
from pydantic import ValidationError
from services.api.models import ChatInput
from services.api.main import chat_async
from services.agent.orchestrator import Orchestrator
from services.agent.providers import MockProvider
from test_agent import AgentPorts
from test_contracts import CID


class ApiTests(unittest.IsolatedAsyncioTestCase):
    async def test_valid_input_traverses_orchestrator_and_tools(self):
        class Port:
            async def post(self, destination, payload, cid):
                return (await Orchestrator(MockProvider(), AgentPorts(), lambda e: None).run(payload)).model_dump()
        with contextlib.redirect_stdout(io.StringIO()):
            result = await chat_async(dict(utterance="Até o salário dá?", amount_brl="500,00", consent_to_analysis=True), CID, Port())
        self.assertEqual(result.financial_result.closing_cents, 60000)
        self.assertEqual(result.correlation_id, CID)

    def test_decimal_amount_is_exact_and_critical_fields_cannot_be_injected(self):
        base = dict(utterance="Até o salário?", amount_brl="0,29", consent_to_analysis=True)
        self.assertEqual(ChatInput.model_validate(base).amount_cents(), 29)
        for patch in ({"amount_brl": "NaN"}, {"amount_brl": "1.001"}, {"amount_brl": "-1"},
                      {"customer_id": "other"}, {"balance_cents": 1000}, {"allowed": True},
                      {"context": {}}, {"consent_to_analysis": "true"}):
            with self.subTest(patch=patch), self.assertRaises(ValidationError):
                ChatInput.model_validate(base | patch)
