import logging
import boto3
from botocore.exceptions import ClientError
from typing import List, Optional, Dict, Any
# For FCM (Firebase Cloud Messaging)
import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings
from app.utils.exceptions import ServiceUnavailableException

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for sending emails (AWS SES) and push notifications (Firebase FCM).
    """
    
    def __init__(self):
        # Initialize AWS SES Client
        self.ses_client = None
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            try:
                self.ses_client = boto3.client(
                    "ses",
                    region_name=settings.AWS_SES_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                )
            except Exception as e:
                logger.error(f"Failed to initialize AWS SES: {e}")

        # Initialize Firebase Admin SDK (Singleton check)
        if not firebase_admin._apps:
            if settings.FCM_SERVICE_ACCOUNT_KEY_PATH:
                try:
                    cred = credentials.Certificate(settings.FCM_SERVICE_ACCOUNT_KEY_PATH)
                    firebase_admin.initialize_app(cred)
                except Exception as e:
                    logger.error(f"Failed to initialize Firebase Admin: {e}")

    async def send_email(self, to_email: str, subject: str, body_text: str, body_html: Optional[str] = None):
        """
        Send a transactional email via AWS SES.
        """
        if not self.ses_client:
            logger.warning("SES client not configured. Email skipped.")
            return

        # Determine charset
        charset = "UTF-8"
        
        try:
            response = self.ses_client.send_email(
                Source=settings.EMAILS_FROM_EMAIL or "noreply@vextor7.com",
                Destination={"ToAddresses": [to_email]},
                Message={
                    "Subject": {"Data": subject, "Charset": charset},
                    "Body": {
                        "Text": {"Data": body_text, "Charset": charset},
                        "Html": {"Data": body_html or body_text, "Charset": charset},
                    },
                },
            )
            logger.info(f"Email sent to {to_email}: MessageId={response.get('MessageId')}")
        except ClientError as e:
            logger.error(f"AWS SES Error: {e.response['Error']['Message']}")
            # In a task, we might retry or fail silently depending on importance
            raise ServiceUnavailableException("Email Service", str(e))

    async def send_push_notification(
        self, 
        fcm_token: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Send a push notification to a single device via FCM.
        """
        if not firebase_admin._apps:
            logger.warning("Firebase not configured. Push notification skipped.")
            return

        try:
            # Convert all data values to strings (FCM requirement)
            data_str = {k: str(v) for k, v in data.items()} if data else {}
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data_str,
                token=fcm_token,
            )
            response = messaging.send(message)
            logger.info(f"Push notification sent: {response}")
        except Exception as e:
            logger.error(f"FCM Error: {e}")
            # Often tokens become invalid, we might need logic to remove them from DB here.
            pass