from celery import Celery
from app.config import settings

celery_app = Celery(
    "face_swap_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=['app.services.ai_worker'] # Обязательно оставляем!
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)