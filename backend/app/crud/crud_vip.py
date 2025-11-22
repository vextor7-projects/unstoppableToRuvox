import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.crud.base import BaseCRUD
from app.models.staking_vip import VipTier, TierHistory, VipBenefitsLog
from app.utils.enums import VipTierLevel

# --- CRUD for VipTier ---


class CRUDVipTier(BaseCRUD[VipTier, BaseModel, BaseModel]):
    """
    CRUD operations for the VipTier model.
    This model is tightly coupled to the User model (1-to-1).
    Schemas are BaseModel as updates are handled by a dedicated service.
    """

    async def create_for_user(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        volume_reset_date: datetime
    ) -> VipTier:
        """
        Create the initial VIP Tier entry for a new user.
        Defaults to BRONZE.
        
        :param db: The asynchronous database session.
        :param user_id: The UUID of the user.
        :param volume_reset_date: The calculated date for the first reset.
        :return: The newly created VipTier object.
        """
        db_obj = self.model(
            user_id=user_id,
            tier=VipTierLevel.BRONZE,
            monthly_transaction_volume=Decimal("0.0"),
            current_staking_value=Decimal("0.0"),
            volume_reset_date=volume_reset_date,
        )
        db.add(db_obj)
        # Note: This should be called *during* user creation,
        # so the commit might be handled by crud_user.create.
        # We'll commit here for atomicity of this specific action.
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> Optional[VipTier]:
        """
        Get the VIP tier status for a specific user.
        """
        # The primary key of VipTier *is* the user_id.
        return await db.get(self.model, user_id)

    async def get_all_for_update_check(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 1000
    ) -> List[VipTier]:
        """
        Get a batch of all users' VIP tier info.
        Used by a background task to recalculate tiers.
        """
        stmt = select(self.model).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for TierHistory ---


class CRUDTierHistory(BaseCRUD[TierHistory, BaseModel, BaseModel]):
    """
    CRUD operations for the TierHistory model (log-only).
    """

    async def create_log(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        old_tier: Optional[VipTierLevel],
        new_tier: VipTierLevel,
        reason: str
    ) -> TierHistory:
        """
        Create an audit log entry for a change in a user's VIP tier.
        
        :param db: The asynchronous database session.
        :param user_id: The UUID of the user whose tier changed.
        :param old_tier: The user's previous tier.
        :param new_tier: The user's new tier.
        :param reason: The reason for the change (e.g., "VOLUME_INCREASED").
        :return: The newly created TierHistory log object.
        """
        db_obj = self.model(
            user_id=user_id,
            old_tier=old_tier,
            new_tier=new_tier,
            reason=reason,
        )
        db.add(db_obj)
        # Note: This does not commit. The calling service should commit
        # after both updating the VipTier and creating this log entry.
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# --- CRUD for VipBenefitsLog ---


class CRUDVipBenefitsLog(BaseCRUD[VipBenefitsLog, BaseModel, BaseModel]):
    """
    CRUD operations for the VipBenefitsLog model (log-only).
    """

    async def create_log(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        benefit_used: str,
        details: Optional[str] = None
    ) -> VipBenefitsLog:
        """
        Create a log entry when a user utilizes a specific VIP benefit.
        
        :param db: The asynchronous database session.
        :param user_id: The UUID of the user who used the benefit.
        :param benefit_used: Identifier of the benefit (e.g., "PRIORITY_WITHDRAWAL").
        :param details: Optional details (e.g., "Saved 0.50 USD on trade").
        :return: The newly created VipBenefitsLog object.
        """
        db_obj = self.model(
            user_id=user_id, benefit_used=benefit_used, details=details
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj


# Instantiate the CRUD objects for use in the application
crud_vip_tier = CRUDVipTier(VipTier)
crud_tier_history = CRUDTierHistory(TierHistory)
crud_vip_benefits_log = CRUDVipBenefitsLog(VipBenefitsLog)