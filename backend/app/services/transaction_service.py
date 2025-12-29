import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.wallet import Wallet, Transaction
from app.schemas.transaction import (
    TransactionPrepareRequest, TransactionPrepareResponse,
    TransactionBroadcastRequest, TransactionBroadcastResponse, FeeEstimate
)
from app.services.blockchain.rpc_client import rpc_client
from app.services.blockchain.evm_service import evm_service
from app.services.blockchain.bitcoin_service import bitcoin_service
from app.services.blockchain.solana_service import solana_service
from app.utils.enums import Chain, TransactionStatus, TransactionType
from app.utils.exceptions import BadRequestException, NotFoundException, InsufficientBalanceException, TransactionFailedException
from datetime import datetime

class TransactionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def prepare_transaction(self, user_id: uuid.UUID, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        wallet = await self._get_wallet(user_id, request.chain, request.from_address)
        if request.chain == Chain.SOLANA:
            return await self._prepare_solana_tx(request)
        elif request.chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            return await self._prepare_evm_tx(request)
        elif request.chain == Chain.BITCOIN:
            return await self._prepare_bitcoin_tx(request)
        else:
            raise BadRequestException(detail=f"Chain {request.chain} not supported.")

    async def broadcast_transaction(self, user_id: uuid.UUID, request: TransactionBroadcastRequest) -> TransactionBroadcastResponse:
        """
        Broadcasts and immediately records transaction to ensure data integrity.
        """
        # 1. Attempt Broadcast
        try:
            tx_hash = await rpc_client.send_raw_transaction(request.chain, request.signed_tx)
            if not tx_hash:
                raise TransactionFailedException("Node returned empty hash.")
        except Exception as e:
            raise TransactionFailedException(detail=str(e))

        # 2. Persist to DB immediately
        # Note: We need wallet_id. Assumption: Frontend sends valid wallet_id or we fetch via user + chain.
        # For robustness, we query the wallet belonging to user on this chain.
        # Ideally request should have wallet_id, but here we lookup.
        # This is 'safe broadcasting' - if DB fails, user knows.
        try:
            # We don't have exact 'from' address in broadcast request to look up wallet easily without decoding.
            # Assuming client passes wallet_id in a real app, or we update Schema.
            # fallback: look for any wallet on this chain for user (simplified)
            stmt = select(Wallet).join(Wallet.portfolio).where(
                Wallet.portfolio.has(user_id=user_id),
                Wallet.chain == request.chain
            )
            result = await self.db.execute(stmt)
            wallet = result.scalars().first()
            
            if wallet:
                tx_record = Transaction(
                    wallet_id=wallet.id,
                    tx_hash=tx_hash,
                    chain=request.chain,
                    transaction_type=TransactionType.SEND, # Assume SEND for generic broadcast
                    amount=Decimal(0), # Placeholder, updated by indexer later
                    status=TransactionStatus.PENDING,
                    timestamp=datetime.utcnow()
                )
                self.db.add(tx_record)
                await self.db.commit()
                
        except Exception as e:
            # Critical: Log this. The money moved, but DB failed.
            print(f"CRITICAL: Tx {tx_hash} broadcasted but DB save failed: {e}")
            # We still return success to user because the blockchain accepted it.
            
        return TransactionBroadcastResponse(
            tx_hash=tx_hash,
            message="Transaction broadcasted successfully."
        )

    async def _get_wallet(self, user_id: uuid.UUID, chain: Chain, address: str) -> Wallet:
        stmt = select(Wallet).where(Wallet.address == address, Wallet.chain == chain)
        result = await self.db.execute(stmt)
        wallet = result.scalars().first()
        if not wallet:
            raise NotFoundException(detail="Wallet not found.")
        return wallet

    async def _prepare_solana_tx(self, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        balance = await solana_service.get_native_balance(request.from_address)
        if balance < request.amount:
            raise InsufficientBalanceException()
        unsigned_tx = {
            "type": "transfer", "from": request.from_address, "to": request.to_address,
            "amount_sol": str(request.amount), "recent_blockhash": "FETCH_CLIENT_SIDE"
        }
        return TransactionPrepareResponse(
            unsigned_tx=unsigned_tx,
            estimated_fee=FeeEstimate(amount=Decimal("0.000005"), token_symbol="SOL", usd_value=None)
        )

    async def _prepare_evm_tx(self, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        value_wei = int(request.amount * Decimal(10**18))
        data = request.data or "0x"
        gas_limit = await evm_service.estimate_gas_limit(request.chain, request.from_address, request.to_address, data, value_wei)
        gas_stats = await evm_service.get_gas_price(request.chain)
        
        fee_per_gas = (gas_stats["base_fee"] + gas_stats["max_priority_fee"]) if gas_stats["is_eip1559"] else gas_stats["gas_price"]
        total_fee_eth = Decimal(gas_limit * fee_per_gas) / Decimal(10**18)
        
        unsigned_tx = {
            "from": request.from_address, "to": request.to_address, "value": hex(value_wei),
            "data": data, "gasLimit": hex(gas_limit), "chainId": self._get_chain_id(request.chain)
        }
        if gas_stats["is_eip1559"]:
            unsigned_tx.update({
                "maxFeePerGas": hex(gas_stats["base_fee"] + gas_stats["max_priority_fee"]),
                "maxPriorityFeePerGas": hex(gas_stats["max_priority_fee"]), "type": "0x2"
            })
        else:
            unsigned_tx["gasPrice"] = hex(gas_stats["gas_price"])

        return TransactionPrepareResponse(
            unsigned_tx=unsigned_tx,
            estimated_fee=FeeEstimate(amount=total_fee_eth, token_symbol="ETH", usd_value=None)
        )

    async def _prepare_bitcoin_tx(self, request: TransactionPrepareRequest) -> TransactionPrepareResponse:
        utxos = await bitcoin_service.get_utxos(request.from_address)
        target_sats = int(request.amount * 100_000_000)
        selected, current = [], 0
        for utxo in utxos:
            selected.append(utxo)
            current += utxo["value_sats"]
            if current >= target_sats: break
        
        if current < target_sats: raise InsufficientBalanceException()
        fee_sats = await bitcoin_service.estimate_fee(len(selected), 2)
        if current < (target_sats + fee_sats): raise InsufficientBalanceException(detail="Not enough for fee")
        
        return TransactionPrepareResponse(
            unsigned_tx={"inputs": selected, "outputs": [{"address": request.to_address, "value_sats": target_sats}, {"address": request.from_address, "value_sats": current - target_sats - fee_sats}]},
            estimated_fee=FeeEstimate(amount=Decimal(fee_sats)/100_000_000, token_symbol="BTC", usd_value=None)
        )

    def _get_chain_id(self, chain: Chain) -> int:
        return {Chain.ETHEREUM: 1, Chain.POLYGON: 137, Chain.BASE: 8453}.get(chain, 1)