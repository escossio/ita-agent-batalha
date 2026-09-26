"""Somente Data recebe credencial e executa SQL parametrizado."""
import os
from pathlib import Path
from packages.contracts.models import FinancialSnapshot


def connect():
    import psycopg
    return psycopg.connect(host=os.environ["DB_HOST"], dbname=os.environ["DB_NAME"],
                           user=os.environ["DB_USER"], password=Path(os.environ["DB_PASSWORD_FILE"]).read_text().strip(),
                           connect_timeout=2, options="-c statement_timeout=2000")


def initialize():
    fixtures = [FinancialSnapshot.model_validate_json(path.read_text())
                for path in sorted((Path(__file__).parent / "fixtures").glob("*-snapshot.json"))]
    with connect() as connection:
        connection.execute("CREATE TABLE IF NOT EXISTS demo_snapshots (customer_id text PRIMARY KEY, payload jsonb NOT NULL CHECK (payload->>'mode' = 'DEMO'))")
        for snapshot in fixtures:
            connection.execute("INSERT INTO demo_snapshots (customer_id, payload) VALUES (%s, %s::jsonb) ON CONFLICT (customer_id) DO NOTHING",
                               (snapshot.customer_id, snapshot.model_dump_json()))


def read_snapshot(customer_id):
    with connect() as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        row = connection.execute("SELECT payload FROM demo_snapshots WHERE customer_id = %s", (customer_id,)).fetchone()
    if row is None:
        return None
    value = FinancialSnapshot.model_validate(row[0])
    if value.customer_id != customer_id:
        raise ValueError("stored identity mismatch")
    return value


def ready():
    try:
        with connect() as connection:
            connection.execute("SELECT 1 FROM demo_snapshots LIMIT 1")
        return True
    except Exception:
        return False
