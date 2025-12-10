import logging
from asgiref.sync import async_to_sync
from typing import Optional

from app.tasks.celery_app import celery_app
from app.services.notification_service import NotificationService

# Configure logger
logger = logging.getLogger(__name__)

# Instantiate service (stateless logic)
notification_service = NotificationService()

@celery_app.task(acks_late=True, bind=True, max_retries=3)
def send_email_task(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None):
    """
    Celery task to send email asynchronously.
    """
    try:
        async_to_sync(notification_service.send_email)(
            to_email, subject, body_text, body_html
        )
    except Exception as e:
        logger.error(f"Email Task Failed (To: {to_email}): {e}")
        # Retry with exponential backoff (1m, 2m, 4m)
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@celery_app.task(acks_late=True, bind=True, max_retries=3)
def send_push_task(self, fcm_token: str, title: str, body: str, data: dict = None):
    """
    Celery task to send push notification.
    """
    try:
        async_to_sync(notification_service.send_push_notification)(
            fcm_token, title, body, data
        )
    except Exception as e:
        # PRODUCTION FIX: Log the error instead of swallowing it
        logger.error(f"Push Notification Failed: {e}")
        # Retry only for network/server errors, not invalid tokens
        # We assume ServiceUnavailableException logic is handled in service
        raise self.retry(exc=e, countdown=30)