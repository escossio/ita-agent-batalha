"""Explicit Data runtime selection. No credential required by the CI transport."""
import json
import os
from pathlib import Path
from datetime import datetime
from .bigquery import BigQueryConfig, BigQueryLedgerReader, SOURCE_FIELDS
from .normalization import timestamp_source


class MockBigQueryTransport:
    def __init__(self, config):
        self.config = config

    def request(self, method, url, payload, correlation_id):
        schema = {"fields": [{"name": name, "type": kind, "mode": "NULLABLE"} for name, kind in SOURCE_FIELDS]}
        config = self.config
        if method == "GET":
            return dict(schema=schema, type="TABLE", location=config.location,
                        tableReference=dict(projectId=config.project, datasetId=config.dataset, tableId=config.table))
        rows = json.loads(Path(os.environ["ITA_BIGQUERY_MOCK_ROWS_FILE"]).read_text())
        params = {p["name"]: p["parameterValue"]["value"] for p in payload["queryParameters"]}
        start, end = (datetime.fromisoformat(params[k].replace("Z", "+00:00")) for k in ("from_time", "to_time"))
        selected = [r for r in rows if r["id_usuario"] == params["source_user_id"] and r["anomesdia"] is not None
                    and start <= datetime.fromisoformat(timestamp_source(r["anomesdia"]).replace("Z", "+00:00")) < end][:1001]
        return dict(schema=schema, jobComplete=True, totalRows=str(len(selected)),
                    rows=[{"f": [{"v": row[name]} for name, _ in SOURCE_FIELDS]} for row in selected])


def configured_reader():
    mode = os.getenv("ITA_DATA_PROVIDER", "postgres")
    if mode not in {"bigquery", "bigquery_mock"}:
        raise ValueError("ledger provider not enabled")
    config = BigQueryConfig.from_env()
    return BigQueryLedgerReader(config, MockBigQueryTransport(config) if mode == "bigquery_mock" else None)
