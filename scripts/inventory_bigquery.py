"""Read-only metadata capture. No SQL, rows, credentials or partial success output."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import quote


class InventoryError(Exception):
    pass


def collect(project, dataset, get, expected_location=None):
    if not re.fullmatch(r"[a-z][a-z0-9-]{4,61}[a-z0-9]", project or ""):
        raise InventoryError("INVALID_PROJECT")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,1024}", dataset or ""):
        raise InventoryError("INVALID_DATASET")
    root = f"https://bigquery.googleapis.com/bigquery/v2/projects/{project}/datasets/{dataset}"
    metadata = get(root, {"datasetView": "METADATA"})
    expected_ref = {"projectId": project, "datasetId": dataset}
    if metadata.get("datasetReference") != expected_ref or not metadata.get("location"):
        raise InventoryError("DATASET_IDENTITY_OR_LOCATION_MISSING")
    if expected_location and metadata["location"].lower() != expected_location.lower():
        raise InventoryError("DATASET_LOCATION_MISMATCH")
    tables, tokens, token, expected_count = {}, set(), None, None
    for _ in range(1000):
        params = {"maxResults": 1000}
        if token:
            params["pageToken"] = token
        page = get(root + "/tables", params)
        count = page.get("totalItems")
        if type(count) is not int or count < 0:
            raise InventoryError("TABLE_COUNT_MISSING")
        if expected_count is not None and count != expected_count:
            raise InventoryError("DATASET_CHANGED_DURING_CAPTURE")
        expected_count = count
        for item in page.get("tables", []):
            ref = item.get("tableReference", {})
            table_id = ref.get("tableId")
            if not isinstance(table_id, str) or not table_id or len(table_id) > 1024:
                raise InventoryError("INVALID_TABLE_REFERENCE")
            if ref != expected_ref | {"tableId": table_id} or table_id in tables:
                raise InventoryError("DUPLICATE_OR_FOREIGN_TABLE")
            table = get(root + "/tables/" + quote(table_id, safe=""), {})
            if table.get("tableReference") != ref or not table.get("type"):
                raise InventoryError("TABLE_IDENTITY_OR_TYPE_MISSING")
            schema = table.get("schema")
            if not isinstance(schema, dict) or not isinstance(schema.get("fields"), list):
                raise InventoryError("TABLE_SCHEMA_MISSING")
            # Preserve complete nested schema; omit IAM bindings, view SQL and external URLs.
            tables[table_id] = {"table_id": table_id, "type": table["type"], "schema": schema,
                                "etag": table.get("etag"), "last_modified": table.get("lastModifiedTime")}
        token = page.get("nextPageToken")
        if not token:
            break
        if not isinstance(token, str) or token in tokens:
            raise InventoryError("PAGINATION_LOOP")
        tokens.add(token)
    else:
        raise InventoryError("PAGINATION_LIMIT")
    if len(tables) != expected_count:
        raise InventoryError("INCOMPLETE_TABLE_INVENTORY")
    ordered = [tables[key] for key in sorted(tables)]
    schemas = [{key: table[key] for key in ("table_id", "type", "schema")} for table in ordered]
    digest = hashlib.sha256(json.dumps(schemas, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    return {"inventory_version": "1.0", "status": "CAPTURED_REQUIRES_REVIEW",
            "captured_at": datetime.now(timezone.utc).isoformat(), "project": project,
            "dataset": dataset, "location": metadata["location"], "table_count": len(tables),
            "schema_sha256": digest, "tables": ordered,
            "scope": "All tables/views visible to this identity; no row data; not an atomic snapshot"}


def adc_session():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform.read-only"])
    session = AuthorizedSession(credentials, refresh_timeout=5)
    session.trust_env = False
    return session


def metadata_get(session, url, params):
    with session.get(url, params=params, timeout=(3, 15), stream=True, allow_redirects=False) as response:
        if response.status_code != 200:
            raise InventoryError(f"BIGQUERY_METADATA_HTTP_{response.status_code}")
        body = response.raw.read(4_194_305, decode_content=True)
        if len(body) > 4_194_304:
            raise InventoryError("METADATA_RESPONSE_TOO_LARGE")
        return json.loads(body)


def write_private(path, report):
    payload = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation: never silently overwrite the original inventory.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(payload)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=".artifacts/bigquery-inventory.json")
    args = parser.parse_args()
    try:
        with adc_session() as session:
            report = collect(os.getenv("ITA_BIGQUERY_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT"),
                             os.getenv("ITA_BIGQUERY_DATASET"),
                             lambda url, params: metadata_get(session, url, params),
                             os.getenv("ITA_BIGQUERY_LOCATION"))
        write_private(args.output, report)
    except InventoryError as error:
        print(str(error))  # Controlled codes only, never the response body.
        return 1
    except FileExistsError:
        print("OUTPUT_EXISTS_CHOOSE_NEW_PATH")
        return 1
    except Exception:
        print("INVENTORY_UNAVAILABLE_CHECK_ADC_ACCESS_AND_CONFIGURATION")
        return 1
    print(f"CAPTURED_REQUIRES_REVIEW tables={report['table_count']} schema_sha256={report['schema_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
