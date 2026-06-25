FROM node:22-alpine AS frontend-build

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund

COPY frontend/ ./
ARG VITE_API_BASE_URL=/api
ARG VITE_BASE_PATH=/static/
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_BASE_PATH=$VITE_BASE_PATH
RUN npm run build

FROM python:3.13-slim AS web

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=false
ENV FRONTEND_DIST_DIR=/frontend/dist

WORKDIR /app

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./
COPY --from=frontend-build /frontend/dist /frontend/dist

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn shubh_bill.wsgi:application --bind 0.0.0.0:8000"]
