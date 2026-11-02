#!/bin/bash
# Vercel static build: install dependencies, collect static files, apply migrations.
# DATABASE_URL must be set in the Vercel project so migrate runs against Postgres
# (the migrations also seed the catalogue, FAQs and error codes).
set -e

# Fail early with a readable message if the project settings are incomplete.
# (Vercel sets VERCEL=1 during the build, so settings.py runs with DEBUG=False
# and refuses to start without a SECRET_KEY.)
for name in SECRET_KEY DATABASE_URL; do
  if [ -z "${!name}" ]; then
    echo "ERROR: $name is not set. In Vercel open Settings -> Environment Variables, add $name, then Redeploy." >&2
    exit 1
  fi
done

echo "Installing requirements"
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null || python3 -m pip install -r requirements.txt

echo "Collecting static files"
python3 manage.py collectstatic --noinput --clear

echo "Applying migrations"
python3 manage.py migrate --noinput
