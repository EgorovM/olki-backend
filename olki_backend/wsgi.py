"""
WSGI config for olki_backend project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "olki_backend.settings")

application = get_wsgi_application()
