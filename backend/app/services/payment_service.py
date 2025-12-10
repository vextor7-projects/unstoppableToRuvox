import uuid
import logging
import json
import base64
from datetime import timedelta, datetime
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import encrypt_data
from app.crud.crud_payment import crud_payment_session
from app.models.payment import PaymentSession
from app.schemas.payment import (
    PaymentSessionCreateRequest, 
    PaymentSessionResponse, 
    PaymentStatusUpdate
)
from app.utils.enums import PaymentSessionStatus, Chain
from app.utils.constants import PAYMENT_SESSION_EXPIRY_MINUTES
from app.utils.exceptions import (
    NotFoundException, 
    BadRequestException, 
    EncryptionException
)
from app.utils.helpers import get_utc_now
from app.services.dex_aggregator_service import DexAggregatorService

# Configure logger
logger = logging.getLogger(__name__)

class PaymentService:
    """
    Service to manage QR/NFC payment sessions and payment verification.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.dex_service = DexAggregatorService()

    async def create_payment_session(
        self, 
        request: PaymentSessionCreateRequest,
        creator_user_id: Optional[uuid.UUID] = None
    ) -> PaymentSessionResponse:
        """
        Create a new payment session and generate the QR payload.
        
        The payload typically includes:
        - session_id
        - amount
        - currency
        - merchant/user details
        - signature (optional, for tamper-proofing)
        """
        
        # 1. Calculate Expiry
        expires_at = get_utc_now() + timedelta(minutes=PAYMENT_SESSION_EXPIRY_MINUTES)
        
        # 2. Determine Token Amount
        # For V1, we assume 1:1 mapping for USD -> USDC if the request asks for it.
        # A real oracle would be needed here if fiat_currency != "USD" or token != stablecoin.
        # We default to USDC for simplicity as per spec.
        if request.fiat_currency == "USD" and "USD" in request.token_symbol.upper():
             amount_token = request.amount_fiat
        else:
             # Placeholder for dynamic price conversion
             # e.g. Convert 10 EUR to USDC
             # For now, we assume USD input.
             amount_token = request.amount_fiat

        # 3. Construct Payload Data
        payload_data = {
            "sid": str(uuid.uuid4()), # Temporary ID for payload structure if needed before DB commit, or we use DB ID
            "amt": str(request.amount_fiat),
            "cur": request.fiat_currency,
            "tok": request.token_symbol,
            "exp": expires_at.timestamp(),
            "mid": str(request.merchant_id) if request.merchant_id else None
        }
        
        # Serialize and Encrypt Payload (for QR Code)
        # We encrypt to ensure that only our app can read/validate the details from the QR,
        # preventing tampering or malicious QR generation if the key is secure.
        payload_json = json.dumps(payload_data)
        encrypted_payload = encrypt_data(payload_json)
        
        if not encrypted_payload:
            raise EncryptionException("Failed to generate secure QR payload.")
            
        # 4. Save Session to DB
        session = await crud_payment_session.create_session(
            self.db,
            obj_in=request,
            creator_user_id=creator_user_id,
            merchant_id=request.merchant_id,
            amount_token=amount_token,
            qr_nfc_payload=encrypted_payload,
            expires_at=expires_at
        )
        
        return PaymentSessionResponse.model_validate(session)

    async def get_payment_session(self, session_id: uuid.UUID) -> PaymentSessionResponse:
        """
        Retrieve a payment session by ID.
        Checks for expiration.
        """
        session = await crud_payment_session.get(self.db, id=session_id)
        if not session:
            raise NotFoundException("Payment session not found.")
            
        if session.status == PaymentSessionStatus.PENDING:
            if session.expires_at < get_utc_now():
                session.status = PaymentSessionStatus.EXPIRED
                self.db.add(session)
                await self.db.commit()
                await self.db.refresh(session)
        
        return PaymentSessionResponse.model_validate(session)

    async def get_swap_quote_for_payment(
        self,
        session_id: uuid.UUID,
        user_token_symbol: str,
        user_chain: Chain,
        user_token_address: str # Mint address or Contract address
    ) -> Dict[str, Any]:
        """
        Calculate how much of a User's token (e.g., SOL) is needed 
        to pay the Merchant's required amount (e.g., 10 USDC).
        """
        session = await crud_payment_session.get(self.db, id=session_id)
        if not session:
            raise NotFoundException("Payment session not found.")
            
        # Merchant wants this:
        target_amount = session.amount_token # e.g. 10.0 USDC
        target_token_symbol = session.token_symbol # "USDC"
        
        # In a real scenario, we need the Mint Address of the Merchant's USDC on the User's Chain.
        # This requires a mapping of "USDC" -> "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" on Solana.
        # For this implementation, we assume a helper or constant map exists.
        # We will hardcode Solana USDC for demonstration or throw if unknown.
        
        merchant_token_address = self._get_token_address(target_token_symbol, user_chain)
        
        if not merchant_token_address:
            raise BadRequestException(f"Settlement token {target_token_symbol} not supported on {user_chain}")

        # We need to find how much Input is needed for exact Output.
        # Most aggregators support "Exact Output" swaps, but some (like Jupiter) optimized for Exact Input.
        # If Exact Output is not supported, we might need to estimate.
        # Jupiter V6 Quote API supports `swapMode=ExactOut`.
        
        # Note: This requires the DexService to support `swapMode` parameter. 
        # If the current DexService implementation only assumes ExactInput, 
        # we might need to fetch price and calculate estimated input, adding buffer.
        
        # For now, we will call the quote service assuming the user wants to know 
        # "If I pay with X SOL, do I get 10 USDC?" -> No, we need "How much SOL for 10 USDC?"
        
        # Since our `DexAggregatorService` (implemented above) takes `amount_in_atomic`, 
        # it is built for Exact Input. 
        # To support payments efficiently, we usually query a price feed first 
        # (e.g. 1 SOL = 150 USDC), calculate approx SOL (0.066), and then quote 
        # for that amount to see if output >= 10.0.
        
        # Simplified approach for this file: 
        # Return data indicating this feature requires 'ExactOut' support in the aggregator 
        # or a price feed service.
        
        return {
            "message": "Exact Output quoting logic to be implemented with Price Feed integration.",
            "target_amount": target_amount,
            "target_token": target_token_symbol
        }

    def _get_token_address(self, symbol: str, chain: Chain) -> Optional[str]:
        """
        Helper to get contract address for common tokens.
        In production, this should come from a DB Token table.
        """
        # Simplified Map
        if chain == Chain.SOLANA:
            if symbol == "USDC": return "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            if symbol == "SOL": return "So11111111111111111111111111111111111111112"
        return None

    async def complete_session(self, session_id: uuid.UUID, tx_hash: str) -> None:
        """
        Mark a session as completed after verifying the transaction on-chain.
        This is typically called by a background worker or webhook.
        """
        session = await crud_payment_session.get(self.db, id=session_id)
        if session and session.status == PaymentSessionStatus.PENDING:
            session.status = PaymentSessionStatus.COMPLETED
            # We could verify tx_hash on chain here using BlockchainService
            # But to keep response fast, we assume the caller (worker) verified it.
            self.db.add(session)
            await self.db.commit()