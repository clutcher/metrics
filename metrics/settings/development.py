from .defaults_metrics import *

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])
CSRF_TRUSTED_ORIGINS= env.list('CSRF_TRUSTED_ORIGINS', default=[])

DEBUG = True
COMPRESS_ENABLED = False

DEVELOPMENT_APPS = (
)
INSTALLED_APPS += DEVELOPMENT_APPS
