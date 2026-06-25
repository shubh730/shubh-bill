#!/usr/bin/env bash
set -euo pipefail

# Run this from a PythonAnywhere Bash console after setting PROJECT_DIR if needed:
# PROJECT_DIR=/home/yourusername/shubh_bill bash scripts/pythonanywhere_deploy.sh

PROJECT_DIR="${PROJECT_DIR:-$HOME/shubh_bill}"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="${VENV_DIR:-$HOME/.virtualenvs/shubh_bill}"
PA_DOMAIN="${PA_DOMAIN:-$USER.pythonanywhere.com}"
PA_WSGI_FILE="${PA_WSGI_FILE:-/var/www/${USER}_pythonanywhere_com_wsgi.py}"

cd "$PROJECT_DIR"
git pull --ff-only

if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/python" -m pip install -r "$BACKEND_DIR/requirements.txt"

cd "$FRONTEND_DIR"
npm ci
VITE_API_BASE_URL=/api VITE_BASE_PATH=/static/ npm run build

cd "$BACKEND_DIR"
export DJANGO_DEBUG="${DJANGO_DEBUG:-false}"
export DJANGO_ALLOWED_HOSTS="${DJANGO_ALLOWED_HOSTS:-$PA_DOMAIN}"
export DJANGO_CORS_ALLOWED_ORIGINS="${DJANGO_CORS_ALLOWED_ORIGINS:-https://$PA_DOMAIN}"

"$VENV_DIR/bin/python" manage.py migrate --noinput
"$VENV_DIR/bin/python" manage.py collectstatic --noinput

if [ -f "$PA_WSGI_FILE" ]; then
  touch "$PA_WSGI_FILE"
fi

echo "Deploy complete for $PA_DOMAIN"
