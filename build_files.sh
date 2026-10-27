#!/bin/bash
# Vercel static build: install dependencies, collect static files, apply migrations.
# DATABASE_URL must be set in the Vercel project so migrate runs against Postgres
# (the migrations also seed the catalogue, FAQs and error codes).
set -e

echo "Installing requirements"
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null || python3 -m pip install -r requirements.txt

echo "Collecting static files"
python3 manage.py collectstatic --noinput --clear

echo "Applying migrations"
python3 manage.py migrate --noinput
