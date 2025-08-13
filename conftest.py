import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'metrics.settings.development')

if not settings.configured:
    django.setup()