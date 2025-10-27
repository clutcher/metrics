
FROM python:slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=metrics.settings.production \
    PIP_NO_CACHE_DIR=1

ARG APP_USER=metricsuser
ARG APP_UID=10001
RUN useradd -u ${APP_UID} -m ${APP_USER}

WORKDIR /metrics

COPY requirements.txt /metrics/requirements.txt
RUN pip install --no-cache-dir -r /metrics/requirements.txt

COPY --chown=${APP_UID}:${APP_UID} . /metrics

RUN mkdir -p /metrics/staticfiles && chown ${APP_UID}:${APP_UID} /metrics/staticfiles

USER ${APP_USER}

RUN python manage.py collectstatic --noinput

EXPOSE 8000

ENV GUNICORN_WORKERS=5 \
    GUNICORN_THREADS=10 \
    GUNICORN_TIMEOUT=120 \
    GUNICORN_MAX_REQUESTS=2000 \
    GUNICORN_MAX_REQUESTS_JITTER=200 \
    GUNICORN_GRACEFUL_TIMEOUT=120 \
    GUNICORN_PRELOAD=false

CMD ["sh", "-c", "gunicorn metrics.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS} --threads ${GUNICORN_THREADS} --timeout ${GUNICORN_TIMEOUT} --graceful-timeout ${GUNICORN_GRACEFUL_TIMEOUT} --max-requests ${GUNICORN_MAX_REQUESTS} --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER} ${GUNICORN_PRELOAD:+--preload}"]
