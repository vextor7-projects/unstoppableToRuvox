import uuid
from typing import List, Optional, Dict, Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.crud.base import BaseCRUD
from app.models.compliance import (
    TravelRuleRecord,
    BlockchainScreening,
    SuspiciousActivity,
    ComplianceReport,
    RegulatorySubmission,
)
from app.utils.enums import (
    Chain,
    ComplianceStatus,
    RiskRating,
    ScreeningAction,
    SuspiciousActivityStatus,
    ReportStatus,
)

# --- CRUD for TravelRuleRecord ---


class CRUDTravelRule(BaseCRUD[TravelRuleRecord, BaseModel, BaseModel]):
    """
    CRUD operations for the TravelRuleRecord model.
    """

    async def create_record(
        self, db: AsyncSession, *, record_data: Dict[str, Any]
    ) -> TravelRuleRecord:
        """
        Create a new Travel Rule record.
        'record_data' is a dictionary containing all fields for the model.
        """
        db_obj = self.model(**record_data, status=ComplianceStatus.PENDING)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[TravelRuleRecord]:
        """
        Get all Travel Rule records for a specific user.
        """
        stmt = (
            select(self.model)
            .filter(self.model.sender_user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_pending_review(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[TravelRuleRecord]:
        """
        Get all Travel Rule records pending admin review.
        """
        stmt = (
            select(self.model)
            .filter(self.model.status == ComplianceStatus.PENDING)
            .order_by(self.model.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for BlockchainScreening ---


class CRUDBlockchainScreening(BaseCRUD[BlockchainScreening, BaseModel, BaseModel]):
    """
    CRUD operations for the BlockchainScreening model.
    """

    async def create_screening_record(
        self, db: AsyncSession, *, screening_data: Dict[str, Any]
    ) -> BlockchainScreening:
        """
        Log a new blockchain address screening result.
        'screening_data' is a dictionary containing all fields for the model.
        """
        db_obj = self.model(**screening_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_latest_by_address(
        self, db: AsyncSession, *, address: str, chain: Chain
    ) -> Optional[BlockchainScreening]:
        """
        Get the most recent screening result for a specific address and chain.
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.address == address,
                self.model.chain == chain
            )
            .order_by(self.model.screening_date.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_flagged_for_review(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[BlockchainScreening]:
        """
        Get all screening records that were flagged for manual review.
        """
        stmt = (
            select(self.model)
            .filter(self.model.action_taken == ScreeningAction.FLAG_FOR_REVIEW)
            .order_by(self.model.screening_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for SuspiciousActivity ---


class CRUDSuspiciousActivity(BaseCRUD[SuspiciousActivity, BaseModel, BaseModel]):
    """
    CRUD operations for the SuspiciousActivity model.
    """

    async def create_log(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        detection_reason: str,
        details: Optional[str] = None
    ) -> SuspiciousActivity:
        """
        Log a new suspicious activity.
        """
        db_obj = self.model(
            user_id=user_id,
            detection_reason=detection_reason,
            details=details,
            status=SuspiciousActivityStatus.FLAGGED,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_flagged(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[SuspiciousActivity]:
        """
        Get all suspicious activity logs that are flagged for review.
        """
        stmt = (
            select(self.model)
            .filter(self.model.status == SuspiciousActivityStatus.FLAGGED)
            .order_by(self.model.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for ComplianceReport ---


class CRUDComplianceReport(BaseCRUD[ComplianceReport, BaseModel, BaseModel]):
    """
    CRUD operations for the ComplianceReport model.
    """

    async def create_report(
        self, db: AsyncSession, *, report_data: Dict[str, Any]
    ) -> ComplianceReport:
        """
        Store a new generated compliance report (e.g., SAR, CTR draft).
        'report_data' contains fields like 'report_type', 'report_data_encrypted'.
        """
        db_obj = self.model(**report_data, status=ReportStatus.DRAFT)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_pending_submission(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[ComplianceReport]:
        """
        Get all reports in DRAFT status, ready for review and submission.
        """
        stmt = (
            select(self.model)
            .filter(self.model.status == ReportStatus.DRAFT)
            .order_by(self.model.generated_at.asc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for RegulatorySubmission ---


class CRUDRegulatorySubmission(
    BaseCRUD[RegulatorySubmission, BaseModel, BaseModel]
):
    """
    CRUD operations for the RegulatorySubmission model.
    """

    async def create_submission_log(
        self, db: AsyncSession, *, log_data: Dict[str, Any]
    ) -> RegulatorySubmission:
        """
        Log that a report or filing was submitted to a regulatory body.
        'log_data' contains fields like 'filing_name', 'jurisdiction', etc.
        """
        db_obj = self.model(**log_data, status="SUBMITTED")
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instantiate the CRUD objects for use in the application
crud_travel_rule = CRUDTravelRule(TravelRuleRecord)
crud_blockchain_screening = CRUDBlockchainScreening(BlockchainScreening)
crud_suspicious_activity = CRUDSuspiciousActivity(SuspiciousActivity)
crud_compliance_report = CRUDComplianceReport(ComplianceReport)
crud_regulatory_submission = CRUDRegulatorySubmission(RegulatorySubmission)