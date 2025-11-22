import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import desc

from app.crud.base import BaseCRUD
from app.models.staking_vip import StakingPosition, InterestAccrual
from app.schemas.staking import StakeRequest, UnstakeRequest


# --- CRUD for StakingPosition ---


class CRUDStakingPosition(
    BaseCRUD[StakingPosition, StakeRequest, BaseModel]
):
    """
    CRUD operations for the StakingPosition model.
    Note: 'UpdateSchema' is BaseModel as updates (like partial unstake)
    are handled by custom logic, not a generic update.
    """

    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: StakeRequest,
        user_id: uuid.UUID,
        apy_at_stake: Decimal,
        protocol_address: Optional[str] = None
    ) -> StakingPosition:
        """
        Create a new staking position for a user.

        :param db: The asynchronous database session.
        :param obj_in: The Pydantic schema containing staking request details.
        :param user_id: The UUID of the user.
        :param apy_at_stake: The APY at the moment of staking.
        :param protocol_address: Optional address of the DeFi protocol.
        :return: The newly created StakingPosition object.
        """
        db_obj = self.model(
            user_id=user_id,
            token_symbol=obj_in.token_symbol,
            chain=obj_in.chain,
            amount=obj_in.amount,
            apy_at_stake=apy_at_stake,
            is_compounding=obj_in.enable_compounding,
            protocol_address=protocol_address,
        )
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
    ) -> List[StakingPosition]:
        """
        Get all staking positions for a specific user, paginated.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_with_accruals(
        self,
        db: AsyncSession,
        *,
        user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[StakingPosition]:
        """
        Get all staking positions for a user, eagerly loading
        recent interest accruals for each position.
        """
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.interest_accruals).order_by(
                    InterestAccrual.created_at.desc()
                )
            )
            .filter(self.model.user_id == user_id)
            .order_by(self.model.start_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        # Use unique() to avoid duplicate StakingPosition due to joins
        return result.scalars().unique().all()


# --- CRUD for InterestAccrual ---


class CRUDInterestAccrual(BaseCRUD[InterestAccrual, BaseModel, BaseModel]):
    """
    CRUD operations for the InterestAccrual model.
    These are typically only created internally by a background task.
    """

    async def create_accrual(
        self,
        db: AsyncSession,
        *,
        staking_position_id: uuid.UUID,
        amount: Decimal,
        apy_at_accrual: Decimal
    ) -> InterestAccrual:
        """
        Log a new interest accrual for a staking position.
        
        :param db: The asynchronous database session.
        :param staking_position_id: The ID of the parent staking position.
        :param amount: The amount of interest earned.
        :param apy_at_accrual: The APY at the time of this accrual.
        :return: The newly created InterestAccrual object.
        """
        db_obj = self.model(
            staking_position_id=staking_position_id,
            amount=amount,
            apy_at_accrual=apy_at_accrual,
        )
        db.add(db_obj)
        # Note: This does not commit. The calling service/task
        # should commit after processing a batch of accruals.
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_position(
        self,
        db: AsyncSession,
        *,
        staking_position_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[InterestAccrual]:
        """
        Get paginated history of interest accruals for a single position.
        """
        stmt = (
            select(self.model)
            .filter(self.model.staking_position_id == staking_position_id)
            .order_by(self.model.accrual_date.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# Instantiate the CRUD objects for use in the application
crud_staking_position = CRUDStakingPosition(StakingPosition)
crud_interest_accrual = CRUDInterestAccrual(InterestAccrual)