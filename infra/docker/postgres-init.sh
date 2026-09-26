#!/usr/bin/env bash
set -euo pipefail
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<'SQL'
SELECT format('CREATE ROLE ita_demo LOGIN PASSWORD %L', pg_read_file('/run/app-secret/password')) \gexec
CREATE DATABASE ita_demo OWNER ita_demo;
SQL
