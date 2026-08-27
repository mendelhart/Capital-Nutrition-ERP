#!/usr/bin/env bash
# Start/stop a local PostgreSQL 16 for development, without Docker.
# Use docker-compose.yml instead if Docker is available.
set -euo pipefail

PGDATA="${PGDATA:-$(cd "$(dirname "$0")/.." && pwd)/pgdata}"
PGBIN="${PGBIN:-/usr/lib/postgresql/16/bin}"
PGPORT="${PGPORT:-5432}"

case "${1:-start}" in
  init)
    "$PGBIN/initdb" -D "$PGDATA" -A trust -U postgres
    ;;
  start)
    [ -d "$PGDATA" ] || "$0" init
    "$PGBIN/pg_ctl" -D "$PGDATA" -l "$PGDATA/server.log" -o "-p $PGPORT" start
    ;;
  stop)
    "$PGBIN/pg_ctl" -D "$PGDATA" stop
    ;;
  *)
    echo "usage: $0 {init|start|stop}" >&2; exit 1
    ;;
esac
