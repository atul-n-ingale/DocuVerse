from celery import Celery

from app.core.config import settings

# Create Celery client
celery_client = Celery(
    "docuverse_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Global instance
_celery_client: Celery = celery_client


def get_celery_client() -> Celery:
    """Get the Celery client instance."""
    return _celery_client
