from celery import Celery
import os

# Use Azure Redis in production, local Redis in development
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'pdf_tools',
    broker=os.getenv('CELERY_BROKER_URL', redis_url),
    backend=os.getenv('CELERY_RESULT_BACKEND', redis_url)
)

celery_app.conf.task_routes = {
    'tasks.*': {'queue': 'pdf_processing'}
}

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Europe/Berlin',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    task_soft_time_limit=240,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'cleanup-temp-files-every-30-minutes': {
        'task': 'tasks.cleanup_old_files',
        'schedule': crontab(minute='*/30'),
        'args': ('temp', 1),
    },
    'cleanup-upload-files-every-30-minutes': {
        'task': 'tasks.cleanup_old_files',
        'schedule': crontab(minute='*/30'),
        'args': ('uploads', 1),
    },
}
