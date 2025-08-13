
FROM python:slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       libffi-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/app

COPY requirements.txt /opt/app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install --prefix=/install -r /opt/app/requirements.txt


FROM python:slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=metrics.settings.production

ARG APP_USER=appuser
ARG APP_UID=10001
RUN useradd -u ${APP_UID} -m ${APP_USER}

WORKDIR /app

ENV PATH="/install/bin:${PATH}" \
    PYTHONPATH="/install/lib/python3.13/site-packages"
COPY --from=builder /install /install

COPY --chown=${APP_UID}:${APP_UID} . /app

RUN mkdir -p /app/staticfiles && chown ${APP_UID}:${APP_UID} /app/staticfiles

USER ${APP_USER}

ARG BUILD_COLLECTSTATIC=true
RUN if [ "$BUILD_COLLECTSTATIC" = "true" ]; then \
      python manage.py collectstatic --noinput || true; \
    fi

EXPOSE 8000

ENV GUNICORN_WORKERS=5 \
    GUNICORN_THREADS=10 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_MAX_REQUESTS=2000 \
    GUNICORN_MAX_REQUESTS_JITTER=200 \
    GUNICORN_GRACEFUL_TIMEOUT=120 \
    GUNICORN_PRELOAD=false

CMD ["sh", "-c", "gunicorn metrics.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT} --max-requests ${GUNICORN_MAX_REQUESTS} --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER} ${GUNICORN_PRELOAD:+--preload}"]
