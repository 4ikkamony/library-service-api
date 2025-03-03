import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings.dev")

try:
    app = Celery("library_service_api")
    app.config_from_object("django.conf:settings", namespace="CELERY")
    app.autodiscover_tasks()
    logger.info("Celery configured successfully")
except Exception as e:
    logger.error(f"Error configuring Celery: {str(e)}")
    raise
