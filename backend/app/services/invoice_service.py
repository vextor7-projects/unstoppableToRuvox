import uuid
from typing import List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_invoice import crud_invoice
from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceCreate, InvoiceUpdate, InvoicePublicView
from app.utils.enums import InvoiceStatus, LedgerEntryType
from app.utils.exceptions import NotFoundException, BadRequestException, NotAuthorizedException
from app.services.ledger_service import LedgerService

class InvoiceService:
    """
    Service for managing Invoices.
    Integrated with Ledger for settlement.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger_service = LedgerService(db)

    async def create_invoice(self, user_id: uuid.UUID, invoice_in: InvoiceCreate) -> Invoice:
        if invoice_in.due_date and invoice_in.due_date < datetime.utcnow().date():
             raise BadRequestException("Due date cannot be in the past.")
        return await crud_invoice.create_with_user(
            self.db, obj_in=invoice_in, creator_user_id=user_id
        )

    async def get_user_invoices(self, user_id: uuid.UUID, skip: int, limit: int) -> List[Invoice]:
        return await crud_invoice.get_by_creator(self.db, creator_user_id=user_id, skip=skip, limit=limit)

    async def get_invoice_details(self, invoice_id: uuid.UUID, user_id: uuid.UUID) -> Invoice:
        invoice = await crud_invoice.get(self.db, id=invoice_id)
        if not invoice:
            raise NotFoundException("Invoice not found.")
        if invoice.creator_user_id != user_id:
            raise NotAuthorizedException("You do not have permission to view this invoice.")
        return invoice

    async def get_public_invoice(self, payment_link_id: str) -> InvoicePublicView:
        invoice = await crud_invoice.get_by_payment_link_id(self.db, payment_link_id=payment_link_id)
        if not invoice:
            raise NotFoundException("Invoice not found.")
        return InvoicePublicView.model_validate(invoice)

    async def cancel_invoice(self, invoice_id: uuid.UUID, user_id: uuid.UUID) -> Invoice:
        invoice = await self.get_invoice_details(invoice_id, user_id)
        if invoice.status != InvoiceStatus.PENDING:
            raise BadRequestException(f"Cannot cancel invoice in status {invoice.status}.")
        
        updated = await crud_invoice.update(
            self.db, db_obj=invoice, obj_in=InvoiceUpdate(status=InvoiceStatus.CANCELLED)
        )
        await self.db.commit() # Commit transaction
        return updated

    async def mark_as_paid(
        self, 
        invoice_id: uuid.UUID, 
        tx_hash: str, 
        payment_transaction_id: Optional[uuid.UUID] = None
    ) -> Invoice:
        """
        Mark invoice as paid and CREDIT the merchant's ledger.
        """
        invoice = await crud_invoice.get(self.db, id=invoice_id)
        if not invoice:
            raise NotFoundException("Invoice not found.")
            
        if invoice.status == InvoiceStatus.PAID:
            return invoice # Idempotent

        # 1. Update Invoice Status
        invoice.status = InvoiceStatus.PAID
        invoice.paid_at = datetime.utcnow()
        invoice.payment_transaction_id = payment_transaction_id
        
        self.db.add(invoice)
        await self.db.flush() # Stage update

        # 2. Credit Merchant Ledger (CRITICAL FIX)
        # Use invoice ID as transaction reference to ensure idempotency in ledger service
        ledger_tx_id = f"inv_pay_{invoice.id}"
        
        await self.ledger_service.credit_user(
            user_id=invoice.creator_user_id,
            token_symbol=invoice.fiat_currency, # Assuming USD settlement for now
            amount=invoice.amount_fiat,
            transaction_id=ledger_tx_id,
            entry_type=LedgerEntryType.MERCHANT_PAYMENT,
            related_tx_hash=tx_hash
        )
        
        # 3. Commit Atomic Transaction
        await self.db.commit()
        await self.db.refresh(invoice)
        
        return invoice