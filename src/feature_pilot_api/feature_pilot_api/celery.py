import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'feature_pilot_api.settings')

app = Celery('feature_pilot_api')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 