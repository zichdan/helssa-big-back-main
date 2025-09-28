"""
Celery configuration for Helssa project
"""
import os
from celery import Celery
from django.conf import settings

# تنظیم متغیر محیطی برای Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'helssa.settings')

# ایجاد instance از Celery
app = Celery('helssa')

# خواندن تنظیمات از Django settings با namespace CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')

# یافتن خودکار task ها از اپ‌های Django
app.autodiscover_tasks()

# تعریف task برای debug
@app.task(bind=True)
def debug_task(self):
    """تسک تست برای اشکال‌زدایی"""
    print(f'Request: {self.request!r}')