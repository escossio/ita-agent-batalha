#!/usr/bin/env bash
set -euo pipefail
sha=${1:-}
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || { echo 'usage: ci-distributed.sh <full-sha>'; exit 64; }
: "${ITA_CI_WORKERS:?Set space-separated compatible SSH worker aliases externally}"
mkdir -p .artifacts
for worker in $ITA_CI_WORKERS; do
  [[ "$worker" =~ ^[a-zA-Z0-9_.-]+$ ]] || { echo 'invalid worker alias'; exit 64; }
  if ! ssh -o BatchMode=yes -o ConnectTimeout=5 "$worker" 'docker info >/dev/null && docker compose version >/dev/null && command -v git >/dev/null && command -v python3 >/dev/null' 2>/dev/null; then
    echo 'Worker unavailable; checking next compatible worker.'
    continue
  fi
  set +e
  ssh -o BatchMode=yes -o ConnectTimeout=5 "$worker" bash -s -- "$sha" > ".artifacts/distributed-${sha}.log" 2>&1 <<'REMOTE'
set -euo pipefail
sha=$1
[[ "$sha" =~ ^[0-9a-f]{40}$ ]] || exit 64
run_dir=$(mktemp -d /tmp/ita-ci.XXXXXXXX)
trap 'rm -rf "$run_dir"' EXIT
git init -q "$run_dir/repo"
cd "$run_dir/repo"
git remote add origin https://github.com/escossio/ita-agent-batalha.git
git fetch -q --depth=1 origin "$sha"
git checkout -q --detach FETCH_HEAD
[[ "$(git rev-parse HEAD)" == "$sha" ]]
export ITA_CI_WORKER=1
bash infra/docker/verify.sh
REMOTE
  result=$?
  set -e
  if [[ $result == 255 ]]; then echo 'Worker transport failed; trying next compatible worker.'; continue; fi
  tail -n 25 ".artifacts/distributed-${sha}.log"
  # Real test/build failure is not retried on another worker or treated as success.
  if [[ $result != 0 ]]; then exit "$result"; fi
  printf '{"sha":"%s","suite":"foundation","status":"PASS"}\n' "$sha" > ".artifacts/distributed-${sha}.json"
  exit 0
done
echo 'BLOCKED: no compatible worker available. No local fallback.' >&2
exit 69
