#!/usr/bin/env bash
set -e

cd /home/ubuntu/ajio-shopping
git pull origin main
docker compose up -d --build
docker compose exec -T web python manage.py migrate --noinput
docker compose exec -T web python manage.py collectstatic --noinput
docker compose restart web
