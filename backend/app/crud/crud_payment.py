import uuid
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.models.payment import (
    PaymentSession,
    PaymentTransaction,
    SwapTransaction,
    FeeDistribution,
)
from app.schemas.payment import PaymentSessionCreateRequest
from app.utils.enums import PaymentSessionStatus
from app.utils.helpers import get_utc_now

# --- CRUD for PaymentSession ---


class CRUDPaymentSession(
    BaseCRUD[PaymentSession, PaymentSessionCreateRequest, BaseModel]
):
    """
    CRUD operations for the PaymentSession model.
    """

    async def create_session(
        self,
        db: AsyncSession,
        *,
        obj_in: PaymentSessionCreateRequest,
        creator_user_id: Optional[uuid.UUID],
        merchant_id: Optional[uuid.UUID],
        amount_token: Decimal,
        qr_nfc_payload: str,
        expires_at: datetime
    ) -> PaymentSession:
        """
        Create a new payment session.
        """
        db_obj = PaymentSession(
            **obj_in.model_dump(),
            creator_user_id=creator_user_id,
            merchant_id=merchant_id,
            amount_token=amount_token,
            qr_nfc_payload=qr_nfc_payload,
            expires_at=expires_at,
            status=PaymentSessionStatus.PENDING
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_client_session_id(
        self, db: AsyncSession, *, client_session_id: str
    ) -> Optional[PaymentSession]:
        """
        Get a payment session by the client-provided idempotency key.
        """
        stmt = select(self.model).filter(
            self.model.client_session_id == client_session_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_session(
        self, db: AsyncSession, *, session_id: uuid.UUID
    ) -> Optional[PaymentSession]:
        """
        Get a payment session by its ID, but only if it is still PENDING
        and has not expired.
        """
        now = get_utc_now()
        stmt = select(self.model).filter(
            self.model.id == session_id,
            self.model.status == PaymentSessionStatus.PENDING,
            self.model.expires_at > now,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_session_with_details(
        self, db: AsyncSession, *, session_id: uuid.UUID
    ) -> Optional[PaymentSession]:
        """
        Get a payment session and eagerly load related creator and merchant info.
        """
        stmt = (
            select(self.model)
            .options(
                selectinload(self.model.creator_user),
                selectinload(self.model.merchant),
            )
            .filter(self.model.id == session_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# --- CRUD for PaymentTransaction ---


class CRUDPaymentTransaction(BaseCRUD[PaymentTransaction, BaseModel, BaseModel]):
    """
    CRUD operations for the PaymentTransaction model.
    """

    async def create_transaction(
        self, db: AsyncSession, *, tx_data: Dict[str, Any]
    ) -> PaymentTransaction:
        """
        Log a new payment transaction.
        'tx_data' is a dictionary containing all fields for the model.
        """
        db_obj = PaymentTransaction(**tx_data)
        db.add(db_obj)
        # Note: We don't commit here, assuming this is part of a larger
        # service-layer transaction (e.g., updating session, swap, fees)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_tx_hash(
        self, db: AsyncSession, *, tx_hash: str
    ) -> Optional[PaymentTransaction]:
        """
        Get a payment transaction by its on-chain transaction hash.
        """
        stmt = select(self.model).filter(self.model.tx_hash == tx_hash)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# --- CRUD for SwapTransaction ---


class CRUDSwapTransaction(BaseCRUD[SwapTransaction, BaseModel, BaseModel]):
    """
    CRUD operations for the SwapTransaction model.
    """

    async def create_swap(
        self, db: AsyncSession, *, swap_data: Dict[str, Any]
    ) -> SwapTransaction:
        """
        Log a new swap associated with a payment transaction.
        'swap_data' is a dictionary containing all fields for the model.
        """
        db_obj = SwapTransaction(**swap_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# --- CRUD for FeeDistribution ---


class CRUDFeeDistribution(BaseCRUD[FeeDistribution, BaseModel, BaseModel]):
    """
    CRUD operations for the FeeDistribution model.
    """

    async def create_fee_distribution(
        self, db: AsyncSession, *, fee_data: Dict[str, Any]
    ) -> FeeDistribution:
        """
        Log a new fee distribution from a payment transaction.
        'fee_data' is a dictionary containing all fields for the model.
        """
        db_obj = FeeDistribution(**fee_data)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# Instantiate the CRUD objects for use in the application
crud_payment_session = CRUDPaymentSession(PaymentSession)
crud_payment_transaction = CRUDPaymentTransaction(PaymentTransaction)
crud_swap_transaction = CRUDSwapTransaction(SwapTransaction)
crud_fee_distribution = CRUDFeeDistribution(FeeDistribution)