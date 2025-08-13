from .defaults_metrics import *

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

COMPRESS_ENABLED = True

PRODUCTION_APPS = (
)
INSTALLED_APPS += PRODUCTION_APPS

CACHES['task_search_results'] = {
    "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
    "LOCATION": "/var/tmp/django_cache/task_search_results",
    'TIMEOUT': 900
}
