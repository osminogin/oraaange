import os

import environ
from celery import Celery

# Set environment for clean start
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oraaange.settings')

# Django environ
root = environ.Path(__file__) - 2
environ.Env.read_env(root('.env'))

# Celery app init
app = Celery('oraaange')
app.config_from_object('django.conf:settings', namespace='CELERY')

# Throw exception on task error in eager mode
app.conf.task_eager_propagates = True

# Auto-discover celery tasks
app.autodiscover_tasks()
