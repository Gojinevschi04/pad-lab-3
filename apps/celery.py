import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tickets.settings")

app = Celery("tickets")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "expire-unpaid-tickets-every-ten-minutes": {
        "task": "tickets.core.tasks.expire_unpaid_tickets",
        "schedule": crontab(minute="*/15"),  # every 15 minutes
    },
    "send-trip-reminders-every-hour": {
        "task": "tickets.core.tasks.send_upcoming_trip_reminders",
        "schedule": crontab(hour="*"),  # every hour
    },
}
