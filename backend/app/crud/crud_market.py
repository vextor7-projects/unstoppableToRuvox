import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.crud.base import BaseCRUD
from app.models.market import PriceAlert, PriceSnapshot
from app.schemas.market import PriceAlertCreate, PriceAlertUpdate
from app.utils.enums import PriceAlertStatus

# --- CRUD for PriceAlert ---


class CRUDPriceAlert(BaseCRUD[PriceAlert, PriceAlertCreate, PriceAlertUpdate]):
    """
    CRUD operations for the PriceAlert model.
    """

    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: PriceAlertCreate,
        user_id: uuid.UUID
    ) -> PriceAlert:
        """
        Create a new price alert linked to a user.
        The alert defaults to ACTIVE status upon creation.
        """
        db_obj = self.model(
            **obj_in.model_dump(),
            user_id=user_id,
            status=PriceAlertStatus.ACTIVE
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
    ) -> List[PriceAlert]:
        """
        Get all price alerts for a specific user, paginated.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_user_and_id(
        self, db: AsyncSession, *, id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[PriceAlert]:
        """
        Get a single price alert by its ID, ensuring it belongs to the user.
        """
        stmt = select(self.model).filter(
            self.model.id == id, self.model.user_id == user_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_alerts(
        self, db: AsyncSession, *, limit: int = 1000, skip: int = 0
    ) -> List[PriceAlert]:
        """
        Get a batch of all active price alerts from all users.
        Used by a background task to check against current market prices.
        """
        stmt = (
            select(self.model)
            .filter(self.model.status == PriceAlertStatus.ACTIVE)
            .order_by(self.model.coin_id)
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for PriceSnapshot ---


class CRUDPriceSnapshot(BaseCRUD[PriceSnapshot, BaseModel, BaseModel]):
    """
    CRUD operations for the PriceSnapshot model.
    These are log-only and created by a background service.
    """

    async def create_snapshot(
        self, db: AsyncSession, *, snapshot_data: Dict[str, Any]
    ) -> PriceSnapshot:
        """
        Create a new price snapshot.
        'snapshot_data' is a dictionary with coin_id, currency, price, etc.
        
        Note: This assumes the `PriceSnapshot` model uses the `id` from `Base`
        as its primary key.
        """
        db_obj = self.model(**snapshot_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_latest_snapshot(
        self, db: AsyncSession, *, coin_id: str, currency: str
    ) -> Optional[PriceSnapshot]:
        """
        Get the most recent price snapshot for a specific coin/currency pair.
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.coin_id == coin_id, self.model.currency == currency
            )
            .order_by(self.model.snapshot_at.desc())
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_historical_snapshots(
        self,
        db: AsyncSession,
        *,
        coin_id: str,
        currency: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PriceSnapshot]:
        """
        Get paginated historical price snapshots for a coin/currency pair.
        """
        stmt = (
            select(self.model)
            .filter(
                self.model.coin_id == coin_id, self.model.currency == currency
            )
            .order_by(self.model.snapshot_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# Instantiate the CRUD objects for use in the application
crud_price_alert = CRUDPriceAlert(PriceAlert)
crud_price_snapshot = CRUDPriceSnapshot(PriceSnapshot)