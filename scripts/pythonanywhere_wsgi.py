import os
import sys

username = "yourusername"
project_root = f"/home/{username}/shubh_bill"
backend_root = f"{project_root}/backend"

if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shubh_bill.settings")
os.environ.setdefault("DJANGO_DEBUG", "false")
os.environ.setdefault("DJANGO_ALLOWED_HOSTS", f"{username}.pythonanywhere.com")
os.environ.setdefault("DJANGO_CORS_ALLOWED_ORIGINS", f"https://{username}.pythonanywhere.com")
os.environ.setdefault("SQLITE_PATH", f"{backend_root}/db.sqlite3")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()
