import logging
import json
from asgiref.sync import async_to_sync
from sqlalchemy import select, and_

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.compliance import TravelRuleRecord, ComplianceReport
from app.utils.enums import ComplianceStatus, ReportType, ReportStatus
from app.core.security import encrypt_data, decrypt_data

logger = logging.getLogger(__name__)

@celery_app.task
def export_travel_rule_reports():
    """
    Periodic task to aggregate pending Travel Rule records and 
    generate a compliance report.
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            # 1. Fetch records ready for export
            stmt = select(TravelRuleRecord).where(
                TravelRuleRecord.status == ComplianceStatus.PENDING
            ).limit(100) # Batch size
            
            result = await db.execute(stmt)
            records = result.scalars().all()
            
            if not records:
                return

            logger.info(f"Generating Travel Rule report for {len(records)} records.")
            
            report_data = []
            
            for record in records:
                # Decrypt PII to include in the secure report (IVMS101 format)
                sender_pii = decrypt_data(record.sender_pii_encrypted)
                recipient_pii = decrypt_data(record.recipient_pii_encrypted)
                
                if sender_pii and recipient_pii:
                    report_data.append({
                        "internal_id": str(record.id),
                        "sender": json.loads(sender_pii),
                        "recipient": json.loads(recipient_pii),
                        "vasp": record.destination_vasp
                    })
                
                # Mark as processed locally
                record.status = ComplianceStatus.COMPLETED
                db.add(record)
            
            # 2. Create Compliance Report Record
            # We encrypt the aggregated report again before storage
            full_report_json = json.dumps(report_data)
            encrypted_report = encrypt_data(full_report_json)
            
            report = ComplianceReport(
                report_type=ReportType.TRAVEL_RULE,
                report_data_encrypted=encrypted_report,
                status=ReportStatus.DRAFT
            )
            db.add(report)
            
            await db.commit()
            logger.info("Travel Rule report generated successfully.")

    async_to_sync(_run)()