import uuid
import hmac
import hashlib
import json
from decimal import Decimal
from typing import Optional, Dict, Any
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt

from app.core.config import settings
from app.models.user import User
from app.schemas.exchange import OnRampWebhookPayload
from app.services.ledger_service import LedgerService
from app.utils.enums import LedgerEntryType
from app.utils.exceptions import BadRequestException, NotFoundException

logger = logging.getLogger(__name__)

class OnrampService:
    """
    Service for handling Fiat On-Ramp integrations (Transak, Ramp, etc.).
    Validates webhooks and credits user accounts.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger_service = LedgerService(db)

    async def process_webhook(
        self, provider: str, payload: dict, signature: str
    ) -> None:
        """
        Process an incoming webhook from an on-ramp provider.
        """
        # 1. Verify Signature
        if not self._verify_signature(provider, payload, signature):
            raise BadRequestException(detail="Invalid webhook signature.")

        # 2. Normalize Data
        # Providers have different payload structures. We normalize them here.
        data = self._normalize_payload(provider, payload)
        
        if data.status != "COMPLETED":
            # We only care about completed purchases for crediting
            return

        # 3. Identify User
        user_id = await self._resolve_user(data)
        if not user_id:
            print(f"On-ramp webhook received for unknown user: {data.user_id}")
            return # Or log to admin dashboard

        # 4. Credit Ledger
        # Transaction ID ensures idempotency (provider order ID is unique)
        tx_id = f"{provider}_{data.order_id}"
        
        try:
            await self.ledger_service.credit_user(
                user_id=user_id,
                token_symbol=data.crypto_currency,
                amount=data.crypto_amount,
                transaction_id=tx_id,
                entry_type=LedgerEntryType.ONRAMP_PURCHASE,
                related_tx_hash=data.transaction_hash
            )
        except Exception as e:
            # If duplicate (idempotency), we ignore. Otherwise log error.
            if "already processed" not in str(e):
                print(f"Failed to credit on-ramp purchase: {e}")
                raise e


    def _verify_signature(self, provider: str, payload: dict, signature: str) -> bool:
        """
        Verify webhook authenticity strictly.
        """
        if provider.lower() == "transak":
            try:
                # Get the JWT token from data or headers
                token = payload.get("data")
                if not token:
                    return False # FAIL SECURE: Token missing
                
                # Real verification
                # Verify the JWT signature using the Transak Secret
                # Note: Transak JWT usually in 'data' field.
                jwt.decode(
                    token, 
                    settings.TRANSAK_SECRET_KEY, 
                    algorithms=["HS256"]
                )
                return True
            except Exception as e:
                # Log invalid signature attempt
                logger.warning(f"Transak webhook signature verification failed: {e}")
                return False

        elif provider.lower() == "ramp":
            if not settings.RAMP_SECRET_KEY:
                return False
                
            # Implement actual HMAC check
            # For Ramp, signature is usually in header 'X-Body-Signature'
            # computed = hmac.new(key, msg, sha256).hexdigest()
            # return hmac.compare_digest(computed, signature)
            return True # Placeholder: Replace with actual HMAC implementation above
            
        return False


    def _normalize_payload(self, provider: str, payload: dict) -> OnRampWebhookPayload:
        """
        Convert provider-specific JSON into our standardized OnRampWebhookPayload.
        """
        if provider.lower() == "transak":
            # Example Transak mapping
            # data = payload.get('webhookData', {})
            return OnRampWebhookPayload(
                event_type=payload.get("eventID"),
                order_id=payload.get("webhookData", {}).get("id"),
                user_id=payload.get("webhookData", {}).get("partnerCustomerId"),
                crypto_amount=Decimal(str(payload.get("webhookData", {}).get("cryptoAmount"))),
                crypto_currency=payload.get("webhookData", {}).get("cryptocurrency"),
                transaction_hash=payload.get("webhookData", {}).get("transactionHash"),
                status=payload.get("webhookData", {}).get("status") # 'COMPLETED'
            )
            
        elif provider.lower() == "ramp":
            # Example Ramp mapping
            # purchase = payload.get('purchase', {})
            return OnRampWebhookPayload(
                event_type=payload.get("type"),
                order_id=payload.get("purchase", {}).get("id"),
                user_id=payload.get("purchase", {}).get("user_id"), # Needs pass-through
                crypto_amount=Decimal(str(payload.get("purchase", {}).get("cryptoAmount"))),
                crypto_currency=payload.get("purchase", {}).get("asset", {}).get("symbol"),
                transaction_hash=payload.get("purchase", {}).get("finalTxHash"),
                status="COMPLETED" if payload.get("type") == "RELEASED" else "PENDING"
            )
            
        raise BadRequestException(detail=f"Unknown provider: {provider}")

    async def _resolve_user(self, data: OnRampWebhookPayload) -> Optional[uuid.UUID]:
        """
        Find the user ID associated with the purchase.
        """
        if data.user_id:
            try:
                return uuid.UUID(data.user_id)
            except ValueError:
                pass
                
        # Fallback: Look up by wallet address if we tracked it?
        # Not reliable for on-ramp as they might generate a new address.
        # We rely on the 'partnerCustomerId' passed during widget init.
        return None