"""Celery configuration and task registration."""
import os
from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.core.settings')

# Create Celery app
app = Celery('zeitwise')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configure task queues
def create_queues():
    return [
        Queue(
            'default',
            Exchange('default'),
            routing_key='default',
            queue_arguments={'x-max-priority': 10}
        ),
        Queue(
            'memes',
            Exchange('memes'),
            routing_key='memes',
            queue_arguments={'x-max-priority': 10}
        ),
    ]

# Setup task queues
app.conf.task_queues = create_queues()
app.conf.task_default_queue = 'default'
app.conf.task_default_exchange = 'default'
app.conf.task_default_routing_key = 'default'

# Task settings
app.conf.task_acks_late = True
app.conf.task_reject_on_worker_lost = True
app.conf.worker_prefetch_multiplier = 1
app.conf.worker_max_tasks_per_child = 100
app.conf.worker_max_memory_per_child = 250000  # 250MB

# Beat settings for periodic tasks
app.conf.beat_schedule = {
    # Add periodic tasks here if needed
    # 'example-task': {
    #     'task': 'app.tasks.example_task',
    #     'schedule': crontab(minute=0, hour=0),  # Daily at midnight
    # },
}

# Autodiscover tasks in all installed apps
def autodiscover_tasks():
    """Auto-discover tasks in all installed apps."""
    return app.autodiscover_tasks(['app.tasks'])

# Load task modules from all registered Django app configs.
autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Debug task to check Celery is working."""
    print(f'Request: {self.request!r}')
