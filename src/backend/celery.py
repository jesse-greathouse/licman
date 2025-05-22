import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "licman.settings")

app = Celery("licman")

# Pull config from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in all registered Django apps
app.autodiscover_tasks()
