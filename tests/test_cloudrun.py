import os
import time
import unittest
from unittest.mock import patch, Mock
from packages.runtime import cloudrun
from packages.runtime.http_client import HttpTransport
from packages.runtime.server import listen_port
from packages.runtime.service_auth import BrokerAuthenticator, sign_identity, verify_identity
from services.api.main import ApiTransport
from services.web.main import WebTransport
from services.agent.main import AgentTransport


class CloudRunTests(unittest.TestCase):
    def setUp(self):
        env = {"ITA_PLATFORM": "cloudrun", "ITA_POLICY_URL": "https://policy-example.run.app",
               "ITA_DATA_URL": "https://data-example.run.app", "ITA_API_URL": "https://api-example.run.app",
               "ITA_AGENT_URL": "https://agent-example.run.app", "ITA_TOOL_BROKER_URL": "https://broker-example.run.app",
               "ITA_FINANCE_URL": "https://finance-example.run.app", "ITA_ALLOWED_CALLERS": "broker@example.iam.gserviceaccount.com",
               "ITA_IDENTITY_SIGNER": "ita-api-sa@example-project.iam.gserviceaccount.com"}
        self.env = patch.dict(os.environ, env, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_dynamic_port_and_invalid_port(self):
        for value in ("9091", "8081", "65535"):
            with patch.dict(os.environ, PORT=value):
                self.assertEqual(listen_port(), int(value))
        for value in ("0", "-1", "65536", "foo"):
            with patch.dict(os.environ, PORT=value), self.assertRaises(ValueError):
                listen_port()

    def test_all_routes_resolve_external_config(self):
        for transport in (HttpTransport(), ApiTransport(), WebTransport(), AgentTransport()):
            for destination in transport.ROUTES:
                self.assertTrue(transport.endpoint(destination).startswith("https://"))
                self.assertNotIn(":8080", transport.endpoint(destination))

    def test_no_local_fallback_or_unsafe_endpoint(self):
        for value in ("http://localhost:8080", "https://127.0.0.1", "https://data:8080", "https://x.run.app/path",
                      "https://x.run.app@evil.example", "https://x.run.app?x=1", "https://x.run.app:443", "https://evil.example"):
            with patch.dict(os.environ, ITA_DATA_URL=value), self.assertRaises(ValueError):
                HttpTransport().endpoint("ledger")
        del os.environ["ITA_DATA_URL"]
        with self.assertRaises(KeyError):
            HttpTransport().endpoint("ledger")
        with patch.dict(os.environ, ITA_PLATFORM="local", K_SERVICE="ita-data"), self.assertRaises(ValueError):
            cloudrun.enabled()

    @patch("google.oauth2.id_token.fetch_id_token", return_value="ephemeral-runtime-token")
    def test_token_audience_and_no_hmac_in_cloud(self, fetch):
        headers = HttpTransport().headers("ledger", {}, "cid")
        self.assertEqual(fetch.call_args.args[1], os.environ["ITA_DATA_URL"])
        self.assertEqual(headers["X-Serverless-Authorization"], "Bearer ephemeral-runtime-token")
        self.assertNotIn("X-ITA-Signature", headers)

    @patch("google.oauth2.id_token.fetch_id_token", side_effect=RuntimeError("credential failure"))
    def test_auth_failure_does_not_send_request(self, _fetch):
        with patch("urllib.request.build_opener") as opener, self.assertRaises(PermissionError):
            HttpTransport()._post("ledger", {}, "cid")
        opener.assert_not_called()

    @patch("google.oauth2.id_token.verify_oauth2_token")
    def test_data_requires_valid_signed_token_audience_and_broker(self, verify):
        claims = dict(email="broker@example.iam.gserviceaccount.com", email_verified=True, sub="123", exp=time.time()+60)
        verify.return_value = claims
        auth = BrokerAuthenticator()
        auth({}, "cid", {"X-ITA-Service-Identity": "signed"}, "/v1/ledger")
        self.assertEqual(verify.call_args.kwargs["audience"], os.environ["ITA_DATA_URL"])
        for change in ({"email": "agent@example.iam.gserviceaccount.com"}, {"email_verified": False}, {"exp": 0}):
            verify.return_value = claims | change
            with self.assertRaises(PermissionError):
                auth({}, "cid", {"X-ITA-Service-Identity": "signed"}, "/v1/ledger")
        with self.assertRaises(PermissionError):
            auth({}, "cid", {}, "/v1/ledger")
        verify.side_effect = ValueError("invalid signature/audience")
        with self.assertRaises(PermissionError):
            auth({}, "cid", {"X-ITA-Service-Identity": "forged"}, "/v1/ledger")

    @patch("google.oauth2.id_token.verify_token")
    def test_customer_proof_signer_and_expiry(self, verify):
        inner = dict(customer_id="customer", correlation_id="cid", window={}, proposed_spend_cents=0,
                     expires=int(time.time())+30, session_hash="a"*64)
        email = os.environ["ITA_IDENTITY_SIGNER"]
        claims = dict(iss=email, sub=email, exp=inner["expires"], ita=inner)
        verify.return_value = claims
        self.assertEqual(verify_identity("signed-jwt"), inner)
        self.assertEqual(verify.call_args.kwargs["audience"], os.environ["ITA_POLICY_URL"])
        self.assertTrue(verify.call_args.kwargs["certs_url"].endswith(email))
        for change in ({"iss": "other"}, {"sub": "other"}, {"exp": time.time()+600}):
            verify.return_value = claims | change
            with self.assertRaises(PermissionError):
                verify_identity("signed-jwt")

    @patch("google.auth.default", return_value=(Mock(), None))
    @patch("google.auth.transport.requests.AuthorizedSession")
    def test_remote_signing_without_local_key(self, session_type, _default):
        response = session_type.return_value.__enter__.return_value.post.return_value.__enter__.return_value
        response.status_code = 200
        response.raw.read.return_value = b'{"signedJwt":"signed-jwt"}'
        self.assertEqual(sign_identity({"expires": int(time.time())+30}), "signed-jwt")
        response.status_code = 403
        with self.assertRaises(PermissionError):
            sign_identity({"expires": int(time.time())+30})

    def test_local_mode_unchanged(self):
        with patch.dict(os.environ, ITA_PLATFORM="local"):
            self.assertEqual(ApiTransport().endpoint("respond"), "http://agent:8080/v1/respond")
