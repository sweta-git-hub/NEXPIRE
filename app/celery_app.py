import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "nexpire",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Real tasks (expiry-risk scan, SMS dispatch, etc.) get added here
# starting Phase 2/3 - this stub just proves the worker boots and
# can talk to Redis.


@celery_app.task
def ping():
    return "pong"
