import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'library_system.settings')

app = Celery('library_system')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.beat_schedule = {
    "run-reminders":{
        "task":"send_overdue_reminders",
        "schedule":crontab(day_of_week='0-6', hour=6, minute=30)
    }
}
