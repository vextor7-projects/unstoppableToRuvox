import uuid
from typing import List, Optional, Dict, Any, Tuple, Union
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import update, and_, desc

from app.crud.base import BaseCRUD
from app.core.security import get_password_hash
from app.utils.helpers import generate_secure_random_string
from app.models.merchant import (
    Merchant,
    MerchantKyc,
    MerchantSettlement,
    SettlementDetail,
    MerchantEmployee,
    MerchantTerminal,
)
from app.schemas.merchant import (
    MerchantCreate,
    MerchantUpdate,
    MerchantKycSubmit,
    MerchantKycReview,
    MerchantSettlementCreate,
    MerchantEmployeeCreate,
    MerchantEmployeeUpdate,
    MerchantTerminalCreate,
    MerchantTerminalUpdate,
)
from app.utils.enums import KycStatus, SettlementStatus

# --- CRUD for Merchant ---


class CRUDMerchant(BaseCRUD[Merchant, MerchantCreate, MerchantUpdate]):
    """
    CRUD operations for the Merchant model.
    """

    async def create_with_user(
        self, db: AsyncSession, *, obj_in: MerchantCreate, user_id: uuid.UUID
    ) -> Merchant:
        """
        Create a new merchant profile, linked one-to-one with a user account.
        """
        db_obj = self.model(
            **obj_in.model_dump(),
            user_id=user_id,
            kyc_status=KycStatus.NOT_STARTED
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_user_id(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> Optional[Merchant]:
        """
        Get a merchant profile by its user_id (which is its primary key).
        """
        return await db.get(self.model, user_id)

    async def get_by_user_id_with_all(
        self, db: AsyncSession, *, user_id: uuid.UUID
    ) -> Optional[Merchant]:
        """
        Get a merchant profile, eagerly loading all related employees,
        terminals, and recent settlements.
        """
        stmt = (
            select(self.model)
            .filter(self.model.user_id == user_id)
            .options(
                selectinload(self.model.employees),
                selectinload(self.model.terminals),
                selectinload(self.model.settlements)
                .selectinload(MerchantSettlement.details)
                .limit(20),  # Limit details to avoid over-fetching
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# --- CRUD for MerchantKyc ---


class CRUDMerchantKyc(
    BaseCRUD[MerchantKyc, MerchantKycSubmit, MerchantKycReview]
):
    """
    CRUD operations for the MerchantKyc model.
    """

    async def create_with_merchant(
        self,
        db: AsyncSession,
        *,
        obj_in: MerchantKycSubmit,
        merchant_user_id: uuid.UUID
    ) -> MerchantKyc:
        """
        Create a new merchant KYC submission.
        """
        db_obj = self.model(
            **obj_in.model_dump(),
            merchant_user_id=merchant_user_id,
            status=KycStatus.PENDING
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_merchant_id(
        self, db: AsyncSession, *, merchant_user_id: uuid.UUID
    ) -> List[MerchantKyc]:
        """
        Get all KYC submissions for a specific merchant.
        """
        stmt = (
            select(self.model)
            .filter(self.model.merchant_user_id == merchant_user_id)
            .order_by(self.model.created_at.desc())
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for MerchantSettlement ---


class CRUDMerchantSettlement(
    BaseCRUD[MerchantSettlement, MerchantSettlementCreate, BaseModel]
):
    """
    CRUD operations for the MerchantSettlement model.
    """

    async def create_settlement(
        self, db: AsyncSession, *, obj_in: MerchantSettlementCreate
    ) -> MerchantSettlement:
        """
        Create a new merchant settlement record.
        """
        db_obj = self.model(
            **obj_in.model_dump(), status=SettlementStatus.PENDING
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_merchant_id(
        self,
        db: AsyncSession,
        *,
        merchant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[MerchantSettlement]:
        """
        Get paginated settlement history for a specific merchant.
        """
        stmt = (
            select(self.model)
            .filter(self.model.merchant_id == merchant_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def create_settlement_detail(
        self,
        db: AsyncSession,
        *,
        settlement_id: uuid.UUID,
        payment_transaction_id: uuid.UUID
    ) -> SettlementDetail:
        """
        Create a new SettlementDetail, linking a payment to a settlement.
        Does not commit, as it's part of a batch.
        """
        db_obj = SettlementDetail(
            settlement_id=settlement_id,
            payment_transaction_id=payment_transaction_id,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj


# --- CRUD for MerchantEmployee ---


class CRUDMerchantEmployee(
    BaseCRUD[MerchantEmployee, MerchantEmployeeCreate, MerchantEmployeeUpdate]
):
    """
    CRUD operations for the MerchantEmployee model.
    """

    async def create_with_merchant(
        self,
        db: AsyncSession,
        *,
        obj_in: MerchantEmployeeCreate,
        merchant_id: uuid.UUID
    ) -> MerchantEmployee:
        """
        Create a new merchant employee, hashing their password.
        """
        hashed_password = get_password_hash(obj_in.password)
        db_obj = self.model(
            **obj_in.model_dump(exclude={"password"}),
            merchant_id=merchant_id,
            hashed_password=hashed_password,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_by_email(
        self, db: AsyncSession, *, email: str
    ) -> Optional[MerchantEmployee]:
        """
        Get a merchant employee by their email address.
        """
        stmt = select(self.model).filter(self.model.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_merchant_id(
        self, db: AsyncSession, *, merchant_id: uuid.UUID
    ) -> List[MerchantEmployee]:
        """
        Get all employees for a specific merchant.
        """
        stmt = select(self.model).filter(self.model.merchant_id == merchant_id)
        result = await db.execute(stmt)
        return result.scalars().all()


# --- CRUD for MerchantTerminal ---


class CRUDMerchantTerminal(
    BaseCRUD[MerchantTerminal, MerchantTerminalCreate, MerchantTerminalUpdate]
):
    """
    CRUD operations for the MerchantTerminal model.
    """

    async def create_with_merchant(
        self,
        db: AsyncSession,
        *,
        obj_in: MerchantTerminalCreate,
        merchant_id: uuid.UUID
    ) -> Tuple[MerchantTerminal, str]:
        """
        Create a new merchant terminal (POS).
        Generates a new API key, hashes it for storage,
        and returns the terminal object and the plain-text key.
        The plain-text key is *only* available at creation time.
        """
        # Generate a new, secure API key
        plain_api_key = f"ter_{generate_secure_random_string(40)}"
        
        # Hash the API key for storage
        hashed_api_key = get_password_hash(plain_api_key)

        db_obj = self.model(
            **obj_in.model_dump(),
            merchant_id=merchant_id,
            hashed_api_key=hashed_api_key,
            is_active=True
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj, plain_api_key

    async def get_by_merchant_id(
        self, db: AsyncSession, *, merchant_id: uuid.UUID
    ) -> List[MerchantTerminal]:
        """
        Get all terminals for a specific merchant.
        """
        stmt = select(self.model).filter(self.model.merchant_id == merchant_id)
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_id_and_merchant_id(
        self, db: AsyncSession, *, terminal_id: uuid.UUID, merchant_id: uuid.UUID
    ) -> Optional[MerchantTerminal]:
        """
        Get a specific terminal by its ID, ensuring it belongs to the merchant.
        """
        stmt = select(self.model).filter(
            self.model.id == terminal_id, self.model.merchant_id == merchant_id
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()


# Instantiate the CRUD objects
crud_merchant = CRUDMerchant(Merchant)
crud_merchant_kyc = CRUDMerchantKyc(MerchantKyc)
crud_merchant_settlement = CRUDMerchantSettlement(MerchantSettlement)
crud_merchant_employee = CRUDMerchantEmployee(MerchantEmployee)
crud_merchant_terminal = CRUDMerchantTerminal(MerchantTerminal)