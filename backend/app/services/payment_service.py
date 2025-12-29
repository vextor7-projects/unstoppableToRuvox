import uuid
import logging
import json
from datetime import timedelta
from typing import Optional, Dict, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import encrypt_data
from app.crud.crud_payment import crud_payment_session
from app.schemas.payment import PaymentSessionCreateRequest, PaymentSessionResponse
from app.utils.enums import PaymentSessionStatus, Chain
from app.utils.constants import PAYMENT_SESSION_EXPIRY_MINUTES
from app.utils.exceptions import NotFoundException, BadRequestException, EncryptionException
from app.utils.helpers import get_utc_now
from app.services.dex_aggregator_service import DexAggregatorService

logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.dex_service = DexAggregatorService()

    async def create_payment_session(
        self, 
        request: PaymentSessionCreateRequest,
        creator_user_id: Optional[uuid.UUID] = None
    ) -> PaymentSessionResponse:
        expires_at = get_utc_now() + timedelta(minutes=PAYMENT_SESSION_EXPIRY_MINUTES)
        
        # Determine Token Amount (Basic 1:1 for USD/USDC for now)
        if request.fiat_currency == "USD" and "USD" in request.token_symbol.upper():
             amount_token = request.amount_fiat
        else:
             amount_token = request.amount_fiat

        payload_data = {
            "sid": str(uuid.uuid4()),
            "amt": str(request.amount_fiat),
            "cur": request.fiat_currency,
            "tok": request.token_symbol,
            "exp": expires_at.timestamp(),
            "mid": str(request.merchant_id) if request.merchant_id else None
        }
        
        encrypted_payload = encrypt_data(json.dumps(payload_data))
        if not encrypted_payload:
            raise EncryptionException("Failed to generate secure QR payload.")
            
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
        session = await crud_payment_session.get(self.db, id=session_id)
        if not session:
            raise NotFoundException("Payment session not found.")
            
        if session.status == PaymentSessionStatus.PENDING and session.expires_at < get_utc_now():
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
        user_token_address: str 
    ) -> Dict[str, Any]:
        """
        Calculates required input tokens to pay the merchant's exact output amount.
        """
        session = await crud_payment_session.get(self.db, id=session_id)
        if not session:
            raise NotFoundException("Payment session not found.")
            
        target_amount = session.amount_token # e.g. 10.0 USDC
        target_token_symbol = session.token_symbol # "USDC"
        
        merchant_token_address = self._get_token_address(target_token_symbol, user_chain)
        if not merchant_token_address:
            raise BadRequestException(f"Settlement token {target_token_symbol} not supported on {user_chain}")

        if user_token_address == merchant_token_address:
            return {
                "input_amount": target_amount,
                "input_token": user_token_symbol,
                "output_amount": target_amount,
                "quote": None
            }

        # Convert target amount to atomic units (e.g. USDC has 6 decimals)
        decimals = 6 if "USD" in target_token_symbol else 18
        amount_out_atomic = int(target_amount * (10 ** decimals))
        
        # Use ExactOut mode
        quote = await self.dex_service.get_quote(
            chain=user_chain,
            token_in_address=user_token_address,
            token_out_address=merchant_token_address,
            amount_atomic=amount_out_atomic,
            swap_mode="ExactOut"
        )
        
        return quote

    def _get_token_address(self, symbol: str, chain: Chain) -> Optional[str]:
        # Production: fetch from DB
        if chain == Chain.SOLANA:
            if symbol == "USDC": return "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
            if symbol == "SOL": return "So11111111111111111111111111111111111111112"
        return None

    async def complete_session(self, session_id: uuid.UUID, tx_hash: str) -> None:
        session = await crud_payment_session.get(self.db, id=session_id)
        if session and session.status == PaymentSessionStatus.PENDING:
            session.status = PaymentSessionStatus.COMPLETED
            self.db.add(session)
            await self.db.commit()

    # async def create_payment_session(
    #     self, 
    #     request: PaymentSessionCreateRequest,
    #     creator_user_id: Optional[uuid.UUID] = None
    # ) -> PaymentSessionResponse:
    #     """
    #     Create a new payment session and generate the QR payload.
        
    #     The payload typically includes:
    #     - session_id
    #     - amount
    #     - currency
    #     - merchant/user details
    #     - signature (optional, for tamper-proofing)
    #     """
        
    #     # 1. Calculate Expiry
    #     expires_at = get_utc_now() + timedelta(minutes=PAYMENT_SESSION_EXPIRY_MINUTES)
        
    #     # 2. Determine Token Amount
    #     # For V1, we assume 1:1 mapping for USD -> USDC if the request asks for it.
    #     # A real oracle would be needed here if fiat_currency != "USD" or token != stablecoin.
    #     # We default to USDC for simplicity as per spec.
    #     if request.fiat_currency == "USD" and "USD" in request.token_symbol.upper():
    #          amount_token = request.amount_fiat
    #     else:
    #          # Placeholder for dynamic price conversion
    #          # e.g. Convert 10 EUR to USDC
    #          # For now, we assume USD input.
    #          amount_token = request.amount_fiat

    #     # 3. Construct Payload Data
    #     payload_data = {
    #         "sid": str(uuid.uuid4()), # Temporary ID for payload structure if needed before DB commit, or we use DB ID
    #         "amt": str(request.amount_fiat),
    #         "cur": request.fiat_currency,
    #         "tok": request.token_symbol,
    #         "exp": expires_at.timestamp(),
    #         "mid": str(request.merchant_id) if request.merchant_id else None
    #     }
        
    #     # Serialize and Encrypt Payload (for QR Code)
    #     # We encrypt to ensure that only our app can read/validate the details from the QR,
    #     # preventing tampering or malicious QR generation if the key is secure.
    #     payload_json = json.dumps(payload_data)
    #     encrypted_payload = encrypt_data(payload_json)
        
    #     if not encrypted_payload:
    #         raise EncryptionException("Failed to generate secure QR payload.")
            
    #     # 4. Save Session to DB
    #     session = await crud_payment_session.create_session(
    #         self.db,
    #         obj_in=request,
    #         creator_user_id=creator_user_id,
    #         merchant_id=request.merchant_id,
    #         amount_token=amount_token,
    #         qr_nfc_payload=encrypted_payload,
    #         expires_at=expires_at
    #     )
        
    #     return PaymentSessionResponse.model_validate(session)


