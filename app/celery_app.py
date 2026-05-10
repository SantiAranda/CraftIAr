from celery import Celery
from celery.schedules import crontab
from django.conf import settings

app = Celery(
    "config",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

app.conf.beat_schedule = {
    'update_product_embeddings': {
        'task': 'app.tasks.update_product_embeddings',
        'schedule': crontab(hour=2, minute=0),  # Run daily at 2:00 AM
    }
}
# Set the timezone for Celery beat scheduling (Argentina)
app.conf.timezone = 'UTC-3' #type: ignore