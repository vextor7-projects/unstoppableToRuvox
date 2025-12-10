import uuid
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.wallet import Wallet
from app.models.ledger import InternalLedger, WithdrawalRequest, DepositTransaction
from app.schemas.exchange import (
    InternalTransferRequest, 
    InternalTransferResponse,
    DepositAddressResponse,
    InternalBalanceResponse,
    WithdrawalRequestCreate
)
from app.services.ledger_service import LedgerService
from app.services.wallet_service import WalletService
from app.services.security_service import SecurityService
from app.utils.enums import Chain, LedgerEntryType, WithdrawalStatus
from app.utils.exceptions import (
    BadRequestException, 
    NotFoundException, 
    InsufficientBalanceException,
    InvalidTotpCodeException
)

class ExchangeService:
    """
    High-level service for Exchange operations (Deposits, Withdrawals, Internal Transfers).
    Orchestrates Ledger, Wallet, and Security services.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger_service = LedgerService(db)
        self.wallet_service = WalletService(db)
        self.security_service = SecurityService(db)

    async def get_deposit_address(self, user_id: uuid.UUID, chain: Chain) -> DepositAddressResponse:
        """
        Get (or generate) a deposit address for a specific chain.
        In a non-custodial/hybrid setup, we might use a specific wallet 
        in the user's portfolio designated for deposits, or a one-time address.
        
        For this architecture (Stage 5), we likely use the user's main wallet address
        on that chain, which we monitor for incoming deposits.
        """
        # Find the user's wallet for this chain
        # Assuming the "Main" portfolio is default
        stmt = select(Wallet).join(Wallet.portfolio).where(
            Wallet.portfolio.has(user_id=user_id),
            Wallet.chain == chain
        )
        result = await self.db.execute(stmt)
        wallet = result.scalars().first()
        
        if not wallet:
            # If no wallet exists, we could auto-create one, or ask user to import.
            # For smooth UX, let's assume we return a "setup required" error or auto-create.
            # Here we assume wallets are created at onboarding.
            raise NotFoundException(detail=f"No {chain} wallet found for this user.")
            
        return DepositAddressResponse(
            chain=chain,
            address=wallet.address,
            qr_code_data=f"{chain.lower()}:{wallet.address}" # Basic URI format
        )

    async def internal_transfer(
        self, sender_id: uuid.UUID, request: InternalTransferRequest
    ) -> InternalTransferResponse:
        """
        Execute an instant off-chain transfer to another user.
        """
        # LedgerService handles the debit/credit atomicity and user lookup
        debit, credit = await self.ledger_service.process_internal_transfer(
            sender_id=sender_id,
            recipient_identifier=request.recipient_identifier,
            token_symbol=request.token_symbol,
            amount=request.amount
        )
        
        # Normalize response using Pydantic schemas
        # (We return the DB objects, Pydantic 'from_attributes' handles conversion)
        return InternalTransferResponse(
            sender_ledger_entry=debit,
            recipient_ledger_entry=credit,
            message=f"Successfully sent {request.amount} {request.token_symbol}"
        )

    async def request_withdrawal(
        self, user_id: uuid.UUID, request: WithdrawalRequestCreate
    ) -> WithdrawalRequest:
        """
        Request a withdrawal. Enforces 2FA if enabled.
        """
        # 1. Check if user has 2FA enabled
        # We need to look up the user's security setting
        # Assuming we can access security_service or query UserSecurity directly
        
        # (Using the injected security_service)
        # Note: We need a way to check 'is_enabled' without verifying a code first.
        # Ideally SecurityService exposes `is_2fa_enabled(user_id)`.
        # For now, we fetch the record manually or add helper to SecurityService.
        
        security_record = await self.security_service._get_or_create_security_record(user_id)
        
        if security_record.totp_enabled:
            if not request.totp_code:
                raise InvalidTotpCodeException(detail="2FA code required.")
            
            # Verify STRICTLY
            is_valid = await self.security_service.verify_totp(
                user_id, request.totp_code, strict=True
            )
            if not is_valid:
                raise InvalidTotpCodeException()
        
        # 2. Create Request via Ledger Service
        withdrawal = await self.ledger_service.request_withdrawal(
            user_id=user_id,
            token_symbol=request.token_symbol,
            amount=request.amount,
            to_address=request.to_address,
            chain=request.chain
        )
        
        # Commit transaction (End of flow)
        await self.db.commit()
        
        return withdrawal
    

    async def get_internal_balance(self, user_id: uuid.UUID, token_symbol: str) -> InternalBalanceResponse:
        """
        Get the user's off-chain balance for a token.
        """
        balance = await self.ledger_service.get_balance(user_id, token_symbol)
        return InternalBalanceResponse(
            token_symbol=token_symbol,
            balance=balance,
            usd_value=None # Pricing service integration needed for this
        )

    async def get_deposit_history(self, user_id: uuid.UUID, limit: int = 20) -> List[DepositTransaction]:
        """
        Get history of on-chain deposits credited to the user.
        """
        stmt = select(DepositTransaction).where(
            DepositTransaction.user_id == user_id
        ).order_by(desc(DepositTransaction.detected_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_withdrawal_history(self, user_id: uuid.UUID, limit: int = 20) -> List[WithdrawalRequest]:
        """
        Get history of withdrawal requests.
        """
        stmt = select(WithdrawalRequest).where(
            WithdrawalRequest.user_id == user_id
        ).order_by(desc(WithdrawalRequest.requested_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()