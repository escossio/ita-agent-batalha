import copy
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from scripts.inventory_bigquery import InventoryError, collect, metadata_get, write_private


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.ref = dict(projectId="demo-project", datasetId="demo_dataset")
        self.schema = {"fields": [{"name": "entries", "type": "RECORD", "mode": "REPEATED", "fields": [
            {"name": "amount", "type": "NUMERIC", "mode": "NULLABLE", "precision": "18", "scale": "2"}]}]}
        self.calls = []

    def get(self, url, params):
        self.calls.append((url, params))
        if url.endswith("/demo_dataset"):
            return dict(datasetReference=self.ref, location="US", access=[{"private": "excluded"}])
        if url.endswith("/tables"):
            second = "pageToken" in params
            return dict(totalItems=2, tables=[{"tableReference": self.ref | {"tableId": "b" if second else "a"}}],
                        **({} if second else {"nextPageToken": "next"}))
        return dict(tableReference=self.ref | {"tableId": url.rsplit("/", 1)[1]},
                    type="VIEW", schema=copy.deepcopy(self.schema), view={"query": "private definition"})

    def test_pagination_preserves_full_nested_schema_without_rows_or_view_sql(self):
        result = collect("demo-project", "demo_dataset", self.get, "us")
        self.assertEqual(result["table_count"], 2)
        self.assertEqual([t["table_id"] for t in result["tables"]], ["a", "b"])
        self.assertTrue(all(t["schema"] == self.schema for t in result["tables"]))
        self.assertNotIn("private", json.dumps(result))
        self.assertFalse(any("/data" in url.rsplit("/datasets/", 1)[-1] for url, _ in self.calls))
        self.assertEqual(result["schema_sha256"], collect("demo-project", "demo_dataset", self.get)["schema_sha256"])

    def test_missing_table_schema_count_or_foreign_identity_never_certifies(self):
        for mutation in ("schema", "count", "foreign", "duplicate", "loop"):
            def broken(url, params):
                result = self.get(url, params)
                if mutation == "schema" and "schema" in result:
                    del result["schema"]
                if mutation == "count" and "totalItems" in result:
                    result["totalItems"] = 3
                if mutation == "foreign" and "schema" in result:
                    result["tableReference"]["projectId"] = "foreign-project"
                if mutation == "duplicate" and "tables" in result:
                    result["tables"][0]["tableReference"]["tableId"] = "a"
                if mutation == "loop" and "pageToken" in params:
                    result["nextPageToken"] = "next"
                return result
            with self.subTest(mutation=mutation), self.assertRaises(InventoryError):
                collect("demo-project", "demo_dataset", broken)

    def test_region_mismatch_or_invalid_configuration_prevents_capture(self):
        with self.assertRaisesRegex(InventoryError, "LOCATION_MISMATCH"):
            collect("demo-project", "demo_dataset", self.get, "EU")
        for project, dataset in [("../invalid", "demo"), ("demo-project", "../invalid")]:
            self.calls.clear()
            with self.assertRaises(InventoryError):
                collect(project, dataset, self.get)
            self.assertEqual(self.calls, [])

    def test_capture_is_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "inventory.json"
            write_private(path, {"original": True})
            self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)
            with self.assertRaises(FileExistsError):
                write_private(path, {"original": False})
            self.assertEqual(json.loads(path.read_text()), {"original": True})

    def test_http_failure_does_not_expose_body_and_redirects_are_disabled(self):
        class Response:
            status_code = 403
            raw = io.BytesIO(b"private error detail")
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        class Session:
            def get(self, url, **kwargs):
                self.kwargs = kwargs
                return Response()
        session = Session()
        with self.assertRaisesRegex(InventoryError, "^BIGQUERY_METADATA_HTTP_403$"):
            metadata_get(session, "https://bigquery.googleapis.com/", {})
        self.assertFalse(session.kwargs["allow_redirects"])
        self.assertEqual(session.kwargs["timeout"], (3, 15))
