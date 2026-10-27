#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

scripts/init.sh
scripts/migrate.sh
exec .venv/bin/python manage.py runserver "$@"
