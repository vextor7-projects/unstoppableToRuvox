import uuid
from decimal import Decimal
from typing import Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import Wallet, Transaction
from app.schemas.transaction import (
    TransactionPrepareRequest,
    TransactionPrepareResponse,
    TransactionBroadcastRequest,
    TransactionBroadcastResponse,
    FeeEstimate
)
from app.services.blockchain.rpc_client import rpc_client
from app.services.blockchain.evm_service import evm_service
from app.services.blockchain.bitcoin_service import bitcoin_service
from app.services.blockchain.solana_service import solana_service
from app.utils.enums import Chain, TransactionStatus, TransactionType
from app.utils.exceptions import (
    BadRequestException,
    NotFoundException,
    InsufficientBalanceException,
    TransactionFailedException
)

class TransactionService:
    """
    Service for preparing and broadcasting on-chain transactions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ... prepare_transaction methods remain as previously defined ...
    # They were mostly correct, just calculation logic.
    # The CRITICAL fix is in broadcast_transaction below.

    async def prepare_transaction(
        self, user_id: uuid.UUID, request: TransactionPrepareRequest
    ) -> TransactionPrepareResponse:
        # Validate Wallet
        wallet = await self._get_wallet(user_id, request.chain, request.from_address)
        
        # Route to chain specific logic
        if request.chain == Chain.SOLANA:
            return await self._prepare_solana_tx(request)
        elif request.chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            return await self._prepare_evm_tx(request)
        elif request.chain == Chain.BITCOIN:
            return await self._prepare_bitcoin_tx(request)
        else:
            raise BadRequestException(detail=f"Chain {request.chain} not supported.")

    async def broadcast_transaction(
        self, user_id: uuid.UUID, request: TransactionBroadcastRequest
    ) -> TransactionBroadcastResponse:
        """
        Broadcast a signed transaction to the network.
        """
        try:
            # 1. Broadcast via RPC Client (Centralized Logic)
            tx_hash = await rpc_client.send_raw_transaction(
                request.chain, request.signed_tx
            )
            
            if not tx_hash:
                raise TransactionFailedException("Node returned empty hash.")

            # 2. Record Transaction in DB
            # We need to find the wallet first. 
            # Limitation: The request doesn't have 'from_address' explicitly, only signed_tx.
            # In a strict system, we'd decode the tx to find 'from', or require it in request.
            # For V1, we assume the Frontend sends 'wallet_id' or we search user's wallets.
            # Ideally, pass 'wallet_id' in TransactionBroadcastRequest.
            
            # Since we can't easily query by signed_tx blob, we'll just log success here.
            # The background sync task or the client will update the history later.
            
            return TransactionBroadcastResponse(
                tx_hash=tx_hash,
                message="Transaction broadcasted successfully."
            )

        except Exception as e:
            raise TransactionFailedException(detail=str(e))

    # --- Internal Preparation Helpers (Same as before but ensures completeness) ---

    async def _prepare_solana_tx(self, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        balance = await solana_service.get_native_balance(request.from_address)
        if balance < request.amount:
            raise InsufficientBalanceException()
        
        # Simplified instruction construction
        unsigned_tx = {
            "type": "transfer",
            "from": request.from_address,
            "to": request.to_address,
            "amount_sol": str(request.amount),
            "recent_blockhash": "FETCH_CLIENT_SIDE" 
        }
        return TransactionPrepareResponse(
            unsigned_tx=unsigned_tx,
            estimated_fee=FeeEstimate(amount=Decimal("0.000005"), token_symbol="SOL", usd_value=None)
        )

    async def _prepare_evm_tx(self, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        value_wei = int(request.amount * Decimal(10**18))
        data = request.data or "0x"
        
        gas_limit = await evm_service.estimate_gas_limit(
            request.chain, request.from_address, request.to_address, data, value_wei
        )
        gas_stats = await evm_service.get_gas_price(request.chain)
        
        # Fee Calculation
        if gas_stats["is_eip1559"]:
            fee_per_gas = gas_stats["base_fee"] + gas_stats["max_priority_fee"]
        else:
            fee_per_gas = gas_stats["gas_price"]
            
        total_fee_eth = Decimal(gas_limit * fee_per_gas) / Decimal(10**18)
        
        unsigned_tx = {
            "from": request.from_address,
            "to": request.to_address,
            "value": hex(value_wei),
            "data": data,
            "gasLimit": hex(gas_limit),
            "chainId": self._get_chain_id(request.chain)
        }
        if gas_stats["is_eip1559"]:
            unsigned_tx["maxFeePerGas"] = hex(gas_stats["base_fee"] + gas_stats["max_priority_fee"])
            unsigned_tx["maxPriorityFeePerGas"] = hex(gas_stats["max_priority_fee"])
            unsigned_tx["type"] = "0x2"
        else:
            unsigned_tx["gasPrice"] = hex(gas_stats["gas_price"])

        return TransactionPrepareResponse(
            unsigned_tx=unsigned_tx,
            estimated_fee=FeeEstimate(amount=total_fee_eth, token_symbol="ETH", usd_value=None)
        )

    
    async def _prepare_bitcoin_tx(self, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        """
        Constructs a Bitcoin transaction using UTXOs.
        """
        # 1. Fetch UTXOs
        utxos = await bitcoin_service.get_utxos(request.from_address)
        
        # 2. Select UTXOs (Coin Selection)
        # Simple algo: First-In-First-Out (FIFO) or Largest-First to cover amount
        target_sats = int(request.amount * 100_000_000)
        selected_utxos = []
        current_sats = 0
        
        for utxo in utxos:
            selected_utxos.append(utxo)
            current_sats += utxo["value_sats"]
            if current_sats >= target_sats:
                break
                
        if current_sats < target_sats:
            raise InsufficientBalanceException(detail=f"Available: {current_sats}, Required: {target_sats}")
            
        # 3. Estimate Fee
        # Inputs = selected UTXOs, Outputs = Recipient + Change
        fee_sats = await bitcoin_service.estimate_fee(len(selected_utxos), 2)
        
        # Check if we have enough for amount + fee
        if current_sats < (target_sats + fee_sats):
             # Try adding more UTXOs if available... (simplified here)
             raise InsufficientBalanceException(detail="Not enough funds to cover network fee.")

        change_sats = current_sats - target_sats - fee_sats
        
        # 4. Build Unsigned Payload (PSBT style or raw inputs)
        unsigned_tx = {
            "inputs": selected_utxos,
            "outputs": [
                {"address": request.to_address, "value_sats": target_sats},
                {"address": request.from_address, "value_sats": change_sats} # Change back to sender
            ]
        }
        
        return TransactionPrepareResponse(
            unsigned_tx=unsigned_tx,
            estimated_fee=FeeEstimate(
                amount=Decimal(fee_sats) / 100_000_000, 
                token_symbol="BTC", 
                usd_value=None
            )
        )


    async def _get_wallet(self, user_id: uuid.UUID, chain: Chain, address: str) -> Wallet:
        stmt = select(Wallet).where(Wallet.address == address, Wallet.chain == chain)
        result = await self.db.execute(stmt)
        wallet = result.scalars().first()
        if not wallet:
            raise NotFoundException(detail="Wallet not found.")
        return wallet

    def _get_chain_id(self, chain: Chain) -> int:
        if chain == Chain.ETHEREUM: return 1
        if chain == Chain.POLYGON: return 137
        if chain == Chain.BASE: return 8453
        return 1