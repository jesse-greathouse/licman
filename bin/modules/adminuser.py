import sys
from pathlib import Path
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import django

# Determine project root (assumes this file is in bin/modules/ under the project root)
APP_ROOT = Path(__file__).resolve().parents[2]
BIN_DIR = APP_ROOT / "bin"
MODULES_DIR = BIN_DIR / "modules"

if str(BIN_DIR) not in sys.path:
    sys.path.insert(0, str(BIN_DIR))

from modules import cfg

def main(update: bool = False):
    django.setup()

    cnf = cfg.get_configuration().get("django", {})
    username = cnf.get("ADMIN_USERNAME")
    email = cnf.get("ADMIN_EMAIL")
    password = cnf.get("ADMIN_PASSWORD")

    if not username or not email or not password:
        sys.stderr.write("❌ Missing ADMIN_USERNAME, ADMIN_EMAIL, or ADMIN_PASSWORD in configuration.\n")
        sys.exit(1)

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

if __name__ == "__main__":
    update_flag = "--update" in sys.argv
    main(update=update_flag)
