import uuid
from typing import List, Dict, Any, Optional
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.models.user import User
from app.models.payment import PaymentTransaction
from app.models.merchant import Merchant
from app.models.compliance import SuspiciousActivity
from app.schemas.user import User as UserSchema
from app.utils.enums import UserStatus, TransactionStatus, SuspiciousActivityStatus
from app.utils.exceptions import NotFoundException, BadRequestException
from app.utils.helpers import get_utc_now

class AdminService:
    """
    Service for Administrative tasks.
    Production-ready metrics and user management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_dashboard_stats(self) -> Dict[str, Any]:
        """
        Aggregates high-level metrics.
        FIX: Returns volume broken down by currency instead of incorrect sum.
        """
        # 1. Total Users
        user_count = await self.db.scalar(select(func.count(User.id)))
        
        # 2. Active Merchants
        merchant_count = await self.db.scalar(select(func.count(Merchant.user_id)))
        
        # 3. Transaction Volume by Token (Correct approach)
        # Group by token_symbol (e.g., USDC, SOL, BTC)
        stmt = (
            select(
                PaymentTransaction.token_paid_symbol, 
                func.sum(PaymentTransaction.amount_paid)
            )
            .where(PaymentTransaction.status == TransactionStatus.COMPLETED)
            .group_by(PaymentTransaction.token_paid_symbol)
        )
        volume_result = await self.db.execute(stmt)
        volumes = []
        for row in volume_result:
            volumes.append({
                "symbol": row[0],
                "total": row[1]
            })
        
        # 4. Pending Compliance Issues
        compliance_count = await self.db.scalar(
            select(func.count(SuspiciousActivity.id))
            .where(SuspiciousActivity.status == SuspiciousActivityStatus.FLAGGED)
        )

        return {
            "total_users": user_count,
            "active_merchants": merchant_count,
            "volumes_by_currency": volumes,
            "pending_compliance_reviews": compliance_count,
            "generated_at": get_utc_now()
        }

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> List[UserSchema]:
        stmt = select(User).offset(skip).limit(limit).order_by(desc(User.created_at))
        result = await self.db.execute(stmt)
        return [UserSchema.model_validate(u) for u in result.scalars().all()]

    async def update_user_status(self, user_id: uuid.UUID, status: UserStatus) -> UserSchema:
        user = await self.db.get(User, user_id)
        if not user:
            raise NotFoundException("User not found.")
            
        if user.is_superuser:
            raise BadRequestException("Cannot change status of superuser accounts.")
            
        user.status = status
        self.db.add(user)
        # Flush/Commit handled here as it's a single atomic admin action
        await self.db.commit()
        await self.db.refresh(user)
        return UserSchema.model_validate(user)

    async def get_suspicious_activities(self, status: Optional[SuspiciousActivityStatus] = None) -> List[Dict[str, Any]]:
        stmt = select(SuspiciousActivity)
        if status:
            stmt = stmt.where(SuspiciousActivity.status == status)
        stmt = stmt.order_by(desc(SuspiciousActivity.created_at))
        result = await self.db.execute(stmt)
        
        activities = result.scalars().all()
        return [
            {
                "id": act.id,
                "user_id": act.user_id,
                "reason": act.detection_reason,
                "details": act.details,
                "status": act.status,
                "created_at": act.created_at
            }
            for act in activities
        ]

    async def resolve_suspicious_activity(
        self, activity_id: uuid.UUID, resolution: SuspiciousActivityStatus, notes: str, admin_name: str
    ) -> None:
        activity = await self.db.get(SuspiciousActivity, activity_id)
        if not activity:
            raise NotFoundException("Activity record not found.")
            
        activity.status = resolution
        activity.review_notes = notes
        activity.reviewed_by = admin_name
        activity.reviewed_at = get_utc_now()
        
        self.db.add(activity)
        
        # If confirmed fraud, suspend user
        if resolution == SuspiciousActivityStatus.CONFIRMED_FRAUD:
            user = await self.db.get(User, activity.user_id)
            if user:
                user.status = UserStatus.SUSPENDED
                self.db.add(user)
        
        await self.db.commit()