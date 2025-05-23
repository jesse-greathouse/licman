import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
app = Celery("backend")

# Pull config from Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discover tasks in all registered Django apps
app.autodiscover_tasks()
