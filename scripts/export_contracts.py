"""Exporta JSON Schema dos modelos ou confere drift sem modificar arquivos."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from packages.contracts.models import CONTRACTS  # noqa: E402
from packages.contracts.ledger import LEDGER_CONTRACTS  # noqa: E402

EXPORTED_CONTRACTS = CONTRACTS + LEDGER_CONTRACTS


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    target = Path("packages/contracts/schemas/v1")
    if not args.check:
        target.mkdir(parents=True, exist_ok=True)
    for model in EXPORTED_CONTRACTS:
        schema = model.model_json_schema()
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        text = json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        path = target / (model.__name__ + ".json")
        if args.check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit(f"schema drift: {path}")
        else:
            path.write_text(text)
    print(f"{len(EXPORTED_CONTRACTS)} versioned contracts {'verified' if args.check else 'exported'}")
