import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bibliflow.settings.dev')

app = Celery('bibliflow')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

app.conf.beat_schedule = {
    'cleanup-completed-imports': {
        'task': 'apps.imports.tasks.cleanup_completed_imports',
        'schedule': 86400,  # Daily
    },
}

app.conf.task_routes = {
    'apps.imports.tasks.process_csv_import': {'queue': 'imports'},
    'apps.imports.tasks.cleanup_completed_imports': {'queue': 'maintenance'},
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')