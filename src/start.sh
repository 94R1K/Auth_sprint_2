#!/bin/sh
set -e

echo "Applying database migrations..."
alembic upgrade head

echo "Loading permissions and roles..."
python -m cli load_data

python -m cli create_superuser

echo "Starting Gunicorn..."
exec "$@"
