import asyncio
from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.services.blockchain.rpc_client import rpc_client
from app.utils.enums import Chain, TransactionType, TransactionStatus
from app.utils.constants import CRYPTO_DECIMAL_PRECISION
from app.utils.exceptions import RpcNodeException, TransactionFailedException

class SolanaService:
    """
    Service for handling high-level Solana blockchain interactions.
    Optimized for concurrency.
    """

    def __init__(self):
        self.chain = Chain.SOLANA

    async def get_native_balance(self, address: str) -> Decimal:
        """
        Get the native SOL balance for an address.
        """
        lamports = await rpc_client.get_balance(self.chain, address)
        # 1 SOL = 1,000,000,000 lamports
        return Decimal(lamports) / Decimal(1_000_000_000)

    async def get_token_accounts(self, owner_address: str) -> List[Dict[str, Any]]:
        """
        Get all SPL token accounts owned by an address.
        """
        params = [
            owner_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
        
        try:
            result = await rpc_client.make_request(self.chain, "getTokenAccountsByOwner", params)
            
            accounts = result.get("value", [])
            parsed_tokens = []
            
            for acc in accounts:
                data = acc.get("account", {}).get("data", {})
                # Handle cases where parsing failed or data format differs
                if isinstance(data, dict):
                    info = data.get("parsed", {}).get("info", {})
                    mint = info.get("mint")
                    token_amount = info.get("tokenAmount", {})
                    
                    amount = token_amount.get("uiAmount")
                    decimals = token_amount.get("decimals")
                    
                    if mint and amount is not None:
                        parsed_tokens.append({
                            "mint": mint,
                            "amount": Decimal(str(amount)),
                            "decimals": decimals,
                            "address": acc.get("pubkey")
                        })
                    
            return parsed_tokens
            
        except RpcNodeException:
            # Re-raise to ensure caller knows sync failed
            raise

    async def broadcast_transaction(self, signed_tx_base64: str) -> str:
        """
        Broadcast a signed transaction to the Solana network.
        """
        try:
            # Uses the send_raw_transaction logic added to RpcClient in Phase 3
            tx_hash = await rpc_client.send_raw_transaction(self.chain, signed_tx_base64)
            return tx_hash
        except RpcNodeException as e:
            raise TransactionFailedException(f"Solana Broadcast Failed: {e.detail}")

    async def get_transaction_history(self, address: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent transaction history for an address using CONCURRENT requests.
        """
        # 1. Get signatures (ordered new to old)
        sig_params = [address, {"limit": limit}]
        signatures_info = await rpc_client.make_request(self.chain, "getSignaturesForAddress", sig_params)
        
        if not signatures_info:
            return []
            
        signatures = [info["signature"] for info in signatures_info]
        
        # 2. Fetch details concurrently (Critical Performance Fix)
        # We create a list of coroutines
        tasks = []
        for sig in signatures:
            tasks.append(
                rpc_client.make_request(
                    self.chain, 
                    "getTransaction", 
                    [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                )
            )
        
        # Run all requests in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        parsed_txs = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Log error but don't break the whole list
                print(f"Failed to fetch tx {signatures[i]}: {result}")
                continue
                
            if result:
                parsed = self._parse_transaction(result, address)
                if parsed:
                    parsed_txs.append(parsed)
                    
        return parsed_txs

    def _parse_transaction(self, tx_data: Dict[str, Any], context_address: str) -> Optional[Dict[str, Any]]:
        """
        Normalize Solana transaction data.
        """
        if not tx_data:
            return None
            
        meta = tx_data.get("meta", {})
        transaction = tx_data.get("transaction", {})
        message = transaction.get("message", {})
        
        tx_hash = transaction.get("signatures", [""])[0]
        slot = tx_data.get("slot")
        block_time = tx_data.get("blockTime")
        
        err = meta.get("err")
        status = TransactionStatus.FAILED if err else TransactionStatus.COMPLETED
        
        # Calculate Balance Changes
        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])
        
        # 'accountKeys' structure differs between 'json' and 'jsonParsed'
        # In jsonParsed, accountKeys is a list of dicts or objects
        account_keys_raw = message.get("accountKeys", [])
        account_keys = []
        
        # Normalize account keys extraction
        for k in account_keys_raw:
            if isinstance(k, dict):
                account_keys.append(k.get("pubkey"))
            else:
                account_keys.append(str(k))
        
        try:
            idx = account_keys.index(context_address)
            pre_bal = pre_balances[idx]
            post_bal = post_balances[idx]
            diff = post_bal - pre_bal
            
            amount_decimal = Decimal(abs(diff)) / Decimal(1_000_000_000)
            
            tx_type = TransactionType.OTHER
            if diff > 0:
                tx_type = TransactionType.RECEIVE
            elif diff < 0:
                tx_type = TransactionType.SEND
                
            return {
                "tx_hash": tx_hash,
                "chain": self.chain,
                "transaction_type": tx_type,
                "amount": amount_decimal,
                "token_symbol": "SOL", 
                "status": status,
                "timestamp": block_time,
                "block_number": slot,
                "from_address": account_keys[0], # Signer
            }
            
        except (ValueError, IndexError):
            return None

solana_service = SolanaService()