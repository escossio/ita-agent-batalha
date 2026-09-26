"""Read-only competition adapter. Only trusted Data Access callers may use it.

No HTTP route/tool is exposed until identity mapping and policy wiring are certified.
"""
from dataclasses import dataclass
from datetime import datetime
import json
import os
import re
from packages.contracts.ledger import CompetitionLedger, LedgerReadRequest
from .normalization import SourceDataError, normalize_entry


# Reviewed schema only; no raw inventory/IAM/project identifiers are packaged.
SOURCE_FIELDS = (
    ("id_usuario", "STRING"), ("anomesdia", "TIMESTAMP"), ("anomes", "INTEGER"),
    ("tipo", "STRING"), ("descr", "STRING"), ("vlr", "FLOAT"),
    ("nom_cate_macro", "STRING"), ("nom_cate_micro", "STRING"), ("saldo_apos", "FLOAT"),
    ("parcela_atual", "FLOAT"), ("parcela_total", "FLOAT"),
)


@dataclass(frozen=True)
class BigQueryConfig:
    project: str
    dataset: str
    table: str
    location: str
    currency: str
    money_unit: str
    maximum_bytes_billed: int

    def __post_init__(self):
        patterns = ((self.project, r"[a-z][a-z0-9-]{4,61}[a-z0-9]"),
                    (self.dataset, r"[A-Za-z0-9_]{1,1024}"), (self.table, r"[A-Za-z0-9_]{1,1024}"),
                    (self.location, r"[A-Za-z0-9-]{1,64}"))
        if any(not re.fullmatch(pattern, value or "") for value, pattern in patterns):
            raise SourceDataError("INVALID_BIGQUERY_CONFIGURATION")
        if self.currency != "BRL" or self.money_unit != "major":
            raise SourceDataError("EXPLICIT_BRL_MAJOR_UNIT_REQUIRED")
        if type(self.maximum_bytes_billed) is not int or not 1 <= self.maximum_bytes_billed <= 10**12:
            raise SourceDataError("EXPLICIT_QUERY_BUDGET_REQUIRED")

    @classmethod
    def from_env(cls):
        try:
            return cls(os.environ["ITA_BIGQUERY_PROJECT"], os.environ["ITA_BIGQUERY_DATASET"],
                       os.environ["ITA_BIGQUERY_TABLE"], os.environ["ITA_BIGQUERY_LOCATION"],
                       os.environ["ITA_BIGQUERY_CURRENCY"], os.environ["ITA_BIGQUERY_MONEY_UNIT"],
                       int(os.environ["ITA_BIGQUERY_MAX_BYTES_BILLED"]))
        except (KeyError, ValueError):
            raise SourceDataError("INVALID_BIGQUERY_CONFIGURATION") from None


class BigQueryTransport:
    """ADC only, fixed Google host, bounded response, no redirects or payload logs."""
    def request(self, method, url, payload, correlation_id):
        import google.auth
        from google.auth.transport.requests import AuthorizedSession
        try:
            credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/bigquery.readonly"])
            with AuthorizedSession(credentials, refresh_timeout=5) as session:
                session.trust_env = False
                with session.request(method, url, json=payload, timeout=(3, 8), stream=True,
                                     allow_redirects=False, headers={"X-Correlation-ID": correlation_id}) as response:
                    if response.status_code != 200:
                        raise SourceDataError("BIGQUERY_UNAVAILABLE")
                    body = response.raw.read(4_194_305, decode_content=True)
                    if len(body) > 4_194_304:
                        raise SourceDataError("BIGQUERY_RESPONSE_LIMIT")
                    return json.loads(body)
        except SourceDataError:
            raise
        except Exception:
            raise SourceDataError("BIGQUERY_UNAVAILABLE") from None


def validate_schema(schema):
    fields = schema.get("fields", [])
    if len(fields) != len(SOURCE_FIELDS):
        raise SourceDataError("BIGQUERY_SCHEMA_DRIFT")
    for field, (name, kind) in zip(fields, SOURCE_FIELDS):
        if (field.get("name"), field.get("type"), field.get("mode", "NULLABLE")) != (name, kind, "NULLABLE"):
            raise SourceDataError("BIGQUERY_SCHEMA_DRIFT")
        if field.get("fields"):
            raise SourceDataError("BIGQUERY_SCHEMA_DRIFT")


class BigQueryLedgerReader:
    def __init__(self, config, transport=None):
        self.config = config
        self.transport = transport or BigQueryTransport()

    def read(self, payload):
        request = LedgerReadRequest.model_validate(payload)
        try:
            return self._read(request)
        except SourceDataError:
            raise
        except Exception:
            # Never expose response data or source identity in dependency exceptions.
            raise SourceDataError("INVALID_BIGQUERY_RESULT") from None

    def _read(self, request):
        config = self.config
        root = f"https://bigquery.googleapis.com/bigquery/v2/projects/{config.project}"
        metadata = self.transport.request("GET", f"{root}/datasets/{config.dataset}/tables/{config.table}",
                                          None, request.correlation_id)
        expected = dict(projectId=config.project, datasetId=config.dataset, tableId=config.table)
        if metadata.get("tableReference") != expected or metadata.get("type") != "TABLE":
            raise SourceDataError("BIGQUERY_SOURCE_MISMATCH")
        if metadata.get("location", "").lower() != config.location.lower():
            raise SourceDataError("BIGQUERY_LOCATION_MISMATCH")
        validate_schema(metadata.get("schema", {}))
        columns = ", ".join(name for name, _ in SOURCE_FIELDS)
        # Identifiers are validated configuration; all request values are named parameters.
        query = (f"SELECT {columns} FROM `{config.project}.{config.dataset}.{config.table}` "
                 "WHERE id_usuario = @source_user_id AND anomesdia >= @from_time AND anomesdia < @to_time "
                 "ORDER BY anomesdia LIMIT 1001")
        params = [{"name": name, "parameterType": {"type": kind}, "parameterValue": {"value": value}}
                  for name, kind, value in (("source_user_id", "STRING", request.source_user_id),
                                            ("from_time", "TIMESTAMP", request.from_time),
                                            ("to_time", "TIMESTAMP", request.to_time))]
        result = self.transport.request("POST", root + "/queries", dict(
            query=query, queryParameters=params, parameterMode="NAMED", useLegacySql=False,
            location=config.location, maximumBytesBilled=str(config.maximum_bytes_billed),
            timeoutMs=5000, jobTimeoutMs="5000", maxResults=1001,
            requestId=request.correlation_id), request.correlation_id)
        if result.get("errors"):
            raise SourceDataError("BIGQUERY_QUERY_FAILED")
        if result.get("jobComplete") is not True:
            raise SourceDataError("BIGQUERY_QUERY_TIMEOUT")
        validate_schema(result.get("schema", {}))
        rows = result.get("rows", [])
        total = result.get("totalRows")
        if not isinstance(total, str) or not re.fullmatch(r"\d{1,4}", total):
            raise SourceDataError("BIGQUERY_INCOMPLETE_RESULT")
        if result.get("pageToken") or len(rows) != int(total) or len(rows) > 1000:
            raise SourceDataError("BIGQUERY_INCOMPLETE_RESULT")
        entries = []
        start = datetime.fromisoformat(request.from_time.replace("Z", "+00:00"))
        end = datetime.fromisoformat(request.to_time.replace("Z", "+00:00"))
        for row in rows:
            cells = row["f"]
            if len(cells) != len(SOURCE_FIELDS) or any(set(cell) != {"v"} for cell in cells):
                raise SourceDataError("INVALID_SOURCE_ROW")
            entry = normalize_entry({name: cell["v"] for (name, _), cell in zip(SOURCE_FIELDS, cells)},
                                    request.source_user_id)
            if entry.occurred_at is None or not start <= datetime.fromisoformat(entry.occurred_at.replace("Z", "+00:00")) < end:
                raise SourceDataError("BIGQUERY_WINDOW_MISMATCH")
            entries.append(entry)
        return CompetitionLedger(schema_version="1.0", kind="competition_ledger", correlation_id=request.correlation_id,
            customer_id=request.customer_id, provenance="COMPETITION_SYNTHETIC_BIGQUERY", currency="BRL",
            source_money_unit="major", source_numeric_storage="FLOAT64_APPROXIMATE",
            normalization="DECIMAL_STRING_HALF_UP_CENTS_V1", from_time=request.from_time, to_time=request.to_time,
            entries=entries, complete_financial_context=False)
