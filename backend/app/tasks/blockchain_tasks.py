import asyncio
import logging
from typing import List
from asgiref.sync import async_to_sync
from sqlalchemy import select

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.models.ledger import DepositTransaction
from app.models.wallet import Portfolio
from app.services.exchange_service import ExchangeService
from app.services.wallet_service import WalletService
from app.services.blockchain.rpc_client import rpc_client
from app.utils.enums import DepositStatus, Chain
from app.utils.constants import CONFIRMATION_THRESHOLDS

logger = logging.getLogger(__name__)

@celery_app.task
def monitor_deposits():
    """
    Periodic task to check confirmations for PENDING deposits.
    
    Strategy:
    1. Fetch all DepositTransactions with status=PENDING.
    2. Group by Chain.
    3. Query RPC for transaction status/confirmations.
    4. If confirmed >= threshold, call exchange_service.process_deposit().
    """
    async def _run():
        async with AsyncSessionLocal() as db:
            exchange_service = ExchangeService(db)
            
            # 1. Fetch Pending Deposits
            stmt = select(DepositTransaction).where(
                DepositTransaction.status == DepositStatus.PENDING
            )
            result = await db.execute(stmt)
            pending_deposits = result.scalars().all()
            
            if not pending_deposits:
                return

            logger.info(f"Monitoring {len(pending_deposits)} pending deposits.")

            # 2. Process each
            for deposit in pending_deposits:
                try:
                    current_confs = await _get_confirmations(deposit.chain, deposit.tx_hash)
                    
                    # Update confirmation count in DB
                    deposit.confirmations = current_confs
                    
                    required = CONFIRMATION_THRESHOLDS.get(deposit.chain.value, 1)
                    
                    if current_confs >= required:
                        logger.info(f"Deposit {deposit.tx_hash} confirmed ({current_confs}/{required}). Processing...")
                        await exchange_service.ledger_service.process_deposit(deposit.id)
                    else:
                        # Just save the updated confirmation count
                        db.add(deposit)
                        await db.commit()
                        
                except Exception as e:
                    logger.error(f"Error monitoring deposit {deposit.tx_hash}: {e}")
                    continue

    async_to_sync(_run)()

async def _get_confirmations(chain: Chain, tx_hash: str) -> int:
    """
    Helper to fetch confirmation count from RPC.
    """
    try:
        if chain in [Chain.ETHEREUM, Chain.BASE, Chain.POLYGON]:
            receipt = await rpc_client.make_request(chain, "eth_getTransactionReceipt", [tx_hash])
            if not receipt:
                return 0
            
            block_number = int(receipt["blockNumber"], 16)
            latest_block_hex = await rpc_client.make_request(chain, "eth_blockNumber", [])
            latest_block = int(latest_block_hex, 16)
            
            return max(0, latest_block - block_number + 1)

        elif chain == Chain.SOLANA:
            # Solana uses 'getSignatureStatuses'
            resp = await rpc_client.make_request(chain, "getSignatureStatuses", [[tx_hash]])
            if resp and resp["value"] and resp["value"][0]:
                status = resp["value"][0]
                if status["confirmationStatus"] == "finalized":
                    return 32 # Max threshold
                return status.get("confirmations", 0) or 0
            return 0

        elif chain == Chain.BITCOIN:
            # For Bitcoin, we need gettransaction or similar if indexed, 
            # or calculate tip - height. 
            # Assuming we use a provider like QuickNode/Blockbook:
            resp = await rpc_client.make_request(chain, "bb_getTx", [tx_hash])
            if resp:
                return resp.get("confirmations", 0)
            return 0
            
        return 0
    except Exception:
        return 0

@celery_app.task
def sync_all_wallets():
    """
    Periodic task to refresh balances.
    OPTIMIZATION: Process in batches to avoid O(N) memory usage and RPC throttling.
    """
    async def _run():
        batch_size = 50
        offset = 0
        
        while True:
            async with AsyncSessionLocal() as db:
                wallet_service = WalletService(db)
                
                # Fetch batch of portfolio IDs
                stmt = select(Portfolio.id).limit(batch_size).offset(offset)
                result = await db.execute(stmt)
                portfolio_ids = result.scalars().all()
                
                if not portfolio_ids:
                    break # Done
                
                # Process batch
                tasks = []
                for pid in portfolio_ids:
                    tasks.append(wallet_service.sync_portfolio_balances(pid))
                
                # Run batch concurrently
                # Note: We use return_exceptions=True so one failure doesn't stop the batch
                await asyncio.gather(*tasks, return_exceptions=True)
                
                offset += batch_size
                await asyncio.sleep(1) # Rate limit protection

    async_to_sync(_run)()