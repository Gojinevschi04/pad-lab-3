import os

from django.core.wsgi import get_wsgi_application

# configure_otel()
# cehck if is debug -> run with otel

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tickets.settings")

application = get_wsgi_application()
