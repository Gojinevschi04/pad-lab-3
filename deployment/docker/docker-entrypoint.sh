#!/bin/sh

set -e

echo "Collecting static files..."
python -m tickets collectstatic --no-input
python -m tickets migrate --no-input
python -m tickets createsuperuser --no-input || true

exec "$@"
