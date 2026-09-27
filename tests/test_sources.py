import hashlib
import json
from pathlib import Path
import unittest
import zipfile

from scripts.architecture_check import violations


class SourceGateTests(unittest.TestCase):
    def test_frozen_sources_and_nonblocking_pending_document(self):
        manifest = json.loads(Path("docs/source/manifest.json").read_text())
        self.assertEqual(len(manifest["sources"]), 4)
        self.assertEqual(len({s["id"] for s in manifest["sources"]}), 4)
        for source in manifest["sources"]:
            if source["status"] == "SOURCE_PENDING_LOCAL_COPY":
                self.assertEqual(source["id"], "voice_and_tone")
                self.assertIsNone(source["sha256"])
                self.assertIsNone(source["path"])
                self.assertFalse(source["blocking_structural_steps"])
                continue
            data = Path(source["path"]).read_bytes()
            self.assertEqual(len(data), source["size_bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), source["sha256"])
            if source["path"].endswith(".xlsx"):
                with zipfile.ZipFile(source["path"]) as archive:
                    self.assertIsNone(archive.testzip())

    def test_agent_import_bypass_is_rejected(self):
        for source in ("import psycopg", "from packages.finance import calculate", "import subprocess", "exec('x')",
                       "from google.cloud import bigquery", "import google.cloud.bigquery",
                       "url = 'https://bigquery.googleapis.com/bigquery/v2/projects'"):
            with self.subTest(source=source):
                self.assertTrue(violations(Path("services/agent/main.py"), source))

    def test_bigquery_is_exclusive_to_data_access(self):
        for component in ("agent", "finance", "policy", "api", "tool-broker"):
            self.assertTrue(violations(Path(f"services/{component}/main.py"), "from google.cloud import bigquery"))
        self.assertFalse(violations(Path("services/data/bigquery.py"), "from google.cloud import bigquery"))

    def test_publication_fixture_exception_is_narrow(self):
        from scripts.publication_check import inspect
        fixture = ("broker" + "@" + "example.iam.gserviceaccount.com").encode()
        self.assertFalse(inspect("tests/test_cloudrun.py", fixture))
        self.assertTrue(inspect("README.md", fixture))
        real_shape = ("person" + "@" + "unapproved.invalid").encode()
        self.assertTrue(inspect("tests/test_cloudrun.py", real_shape))

    def test_agent_contract_import_is_allowed(self):
        self.assertFalse(violations(Path("services/agent/main.py"), "from packages.contracts import Request"))


if __name__ == "__main__":
    unittest.main()
