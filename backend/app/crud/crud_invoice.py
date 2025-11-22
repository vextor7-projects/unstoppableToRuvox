import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.crud.base import BaseCRUD
from app.helpers import generate_unique_id
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate
from app.utils.enums import InvoiceStatus


class CRUDInvoice(BaseCRUD[Invoice, InvoiceCreate, InvoiceUpdate]):
    """
    CRUD operations for the Invoice model.
    """

    async def create_with_user(
        self,
        db: AsyncSession,
        *,
        obj_in: InvoiceCreate,
        creator_user_id: uuid.UUID
    ) -> Invoice:
        """
        Create a new invoice linked to a creator user.
        This method automatically generates a unique, shareable payment_link_id
        and sets the initial status to PENDING.
        
        :param db: The asynchronous database session.
        :param obj_in: The Pydantic schema containing the invoice creation data.
        :param creator_user_id: The UUID of the user creating the invoice.
        :return: The newly created Invoice object.
        """
        # Generate a unique, shareable link ID (e.g., "inv_...")
        payment_link_id = generate_unique_id("inv_")
        
        # Create the Invoice model instance
        db_obj = self.model(
            **obj_in.model_dump(),
            creator_user_id=creator_user_id,
            payment_link_id=payment_link_id,
            status=InvoiceStatus.PENDING  # Default status on creation
        )
        
        # Add, commit, and refresh
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        
        return db_obj

    async def get_by_payment_link_id(
        self, db: AsyncSession, *, payment_link_id: str
    ) -> Optional[Invoice]:
        """
        Get a single invoice by its public, shareable payment_link_id.
        This method eagerly loads the creator_user relationship, which
        is needed for the public payment page to display the creator's name.
        
        :param db: The asynchronous database session.
        :param payment_link_id: The unique string ID of the payment link.
        :return: The Invoice object if found, otherwise None.
        """
        stmt = (
            select(self.model)
            .options(selectinload(self.model.creator_user))
            .filter(self.model.payment_link_id == payment_link_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_creator(
        self,
        db: AsyncSession,
        *,
        creator_user_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """
        Get all invoices created by a specific user, paginated.
        Results are ordered by the most recent first.
        
        :param db: The asynchronous database session.
        :param creator_user_id: The UUID of the user who created the invoices.
        :param skip: Number of invoices to skip (offset).
        :param limit: Maximum number of invoices to return.
        :return: A list of Invoice objects.
        """
        stmt = (
            select(self.model)
            .filter(self.model.creator_user_id == creator_user_id)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    async def get_by_payer_email(
        self,
        db: AsyncSession,
        *,
        payer_email: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Invoice]:
        """
        Get all invoices sent to a specific payer email address, paginated.
        
        :param db: The asynchronous database session.
        :param payer_email: The email address of the payer.
        :param skip: Number of invoices to skip (offset).
        :param limit: Maximum number of invoices to return.
        :return: A list of Invoice objects.
        """
        stmt = (
            select(self.model)
            .filter(self.model.payer_email == payer_email)
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()


# Instantiate the CRUD object for use in the application
crud_invoice = CRUDInvoice(Invoice)