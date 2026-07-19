from celery import Celery

from backend import config

app = Celery("intervai")
app.config_from_object({
    "broker_url": config.CELERY_BROKER_URL,
    "result_backend": config.CELERY_RESULT_BACKEND,
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "timezone": "UTC",
    "enable_utc": True,
})

app.autodiscover_tasks(["backend.workers"])
