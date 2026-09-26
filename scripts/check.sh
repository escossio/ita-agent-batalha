#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
case "${1:-}" in
  lint) python3 -m ruff check .; git diff --check ;;
  unit-contract) python3 -m unittest discover -s tests -v ;;
  architecture) python3 scripts/architecture_check.py ;;
  build) python3 scripts/build_bundle.py ;;
  secret-scan) bash scripts/secret_scan.sh ;;
  *) echo 'usage: check.sh lint|unit-contract|architecture|build|secret-scan' >&2; exit 64 ;;
esac
