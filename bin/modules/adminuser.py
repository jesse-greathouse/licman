import os
import sys
from pathlib import Path

# Ensure `src/` is in sys.path so `backend.config.settings` is importable
APP_ROOT = Path(__file__).resolve().parents[2]
SRC_DIR = APP_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")

import django
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from modules import config

def main(update: bool = False):
    django.setup()

    cfg = config.get_configuration()["django"]
    username = cfg["ADMIN_USERNAME"]
    email = cfg["ADMIN_EMAIL"]
    password = cfg["ADMIN_PASSWORD"]

    User = get_user_model()

    try:
        user = User.objects.get(username=username)
        if update:
            user.email = email
            user.set_password(password)
            user.save()
            print(f"✅ Updated existing superuser: {username}")
        else:
            print(f"ℹ️ Superuser '{username}' already exists. Use `bin/adminuser --update` to modify.")
    except User.DoesNotExist:
        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            print(f"✅ Created new superuser: {username}")
        except IntegrityError as e:
            print(f"❌ Failed to create superuser: {e}")
