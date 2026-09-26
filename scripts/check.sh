#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
case "${1:-}" in
  lint) python3 -m ruff check .; git diff --check ;;
  unit-contract) python3 -m unittest discover -s tests -v; python3 scripts/export_contracts.py --check ;;
  architecture) python3 scripts/architecture_check.py ;;
  build)
    [[ "${ITA_CI_WORKER:-}" == 1 ]] || { echo 'Build requires distributed/hosted worker'; exit 64; }
    python3 scripts/build_bundle.py
    bash infra/docker/verify.sh
    ;;
  secret-scan) bash scripts/secret_scan.sh ;;
  *) echo 'usage: check.sh lint|unit-contract|architecture|build|secret-scan' >&2; exit 64 ;;
esac
