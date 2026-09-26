#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
scan_dir=$(mktemp -d)
trap 'rm -rf "$scan_dir"' EXIT
version=8.30.1
archive="gitleaks_${version}_linux_x64.tar.gz"
curl --fail --silent --show-error --location --max-time 90 \
  "https://github.com/gitleaks/gitleaks/releases/download/v${version}/${archive}" -o "$scan_dir/$archive"
printf '%s  %s\n' '551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb' "$scan_dir/$archive" | sha256sum --check --status
tar -xzf "$scan_dir/$archive" -C "$scan_dir" gitleaks
python3 scripts/publication_check.py --expand-to "$scan_dir/expanded"
"$scan_dir/gitleaks" dir "$scan_dir/expanded" --redact --no-banner
"$scan_dir/gitleaks" dir . --redact --no-banner
"$scan_dir/gitleaks" git . --log-opts=HEAD --redact --no-banner
