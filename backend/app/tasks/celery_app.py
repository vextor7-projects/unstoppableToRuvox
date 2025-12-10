from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery instance
celery_app = Celery("ruvox_tasks", broker=str(settings.CELERY_BROKER_URL))

# Configure Celery
celery_app.conf.update(
    result_backend=str(settings.CELERY_RESULT_BACKEND),
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Retry connection on startup
    broker_connection_retry_on_startup=True,
)

# --- Periodic Tasks (Celery Beat) ---
celery_app.conf.beat_schedule = {
    # Run subscription processing every hour
    "process-recurring-subscriptions": {
        "task": "app.tasks.subscription_tasks.process_due_subscriptions",
        "schedule": crontab(minute=0), # Every hour on the minute 0
    },
    # Run blockchain deposit monitor every minute (or faster if needed)
    "monitor-blockchain-deposits": {
        "task": "app.tasks.blockchain_tasks.monitor_deposits",
        "schedule": 60.0, # Every 60 seconds
    },
    # Run merchant settlement daily at midnight
    "process-merchant-settlements": {
        "task": "app.tasks.payment_tasks.process_merchant_settlements",
        "schedule": crontab(minute=0, hour=0),
    },
    # Sync balances periodically (e.g., every 6 hours as a failsafe)
    # Note: We rely on real-time/webhook updates mostly, this is a backup.
    "sync-portfolio-balances": {
        "task": "app.tasks.blockchain_tasks.sync_all_wallets",
        "schedule": crontab(minute=0, hour="*/6"),
    }
}

# Auto-discover tasks in these modules
celery_app.autodiscover_tasks([
    "app.tasks.notification_tasks",
    "app.tasks.blockchain_tasks",
    "app.tasks.subscription_tasks",
    "app.tasks.compliance_tasks",
    # "app.tasks.payment_tasks" # To be implemented if needed
])