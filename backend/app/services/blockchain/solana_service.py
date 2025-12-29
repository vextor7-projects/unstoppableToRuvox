import asyncio
from decimal import Decimal
from typing import List, Dict, Any, Optional
from app.services.blockchain.rpc_client import rpc_client
from app.utils.enums import Chain, TransactionType, TransactionStatus
from app.utils.exceptions import RpcNodeException, TransactionFailedException

class SolanaService:
    def __init__(self):
        self.chain = Chain.SOLANA
        self.semaphore = asyncio.Semaphore(5) # Rate limit: 5 concurrent requests

    async def get_native_balance(self, address: str) -> Decimal:
        lamports = await rpc_client.get_balance(self.chain, address)
        return Decimal(lamports) / Decimal(1_000_000_000)

    async def get_token_accounts(self, owner_address: str) -> List[Dict[str, Any]]:
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
            raise

    async def broadcast_transaction(self, signed_tx_base64: str) -> str:
        try:
            tx_hash = await rpc_client.send_raw_transaction(self.chain, signed_tx_base64)
            return tx_hash
        except RpcNodeException as e:
            raise TransactionFailedException(f"Solana Broadcast Failed: {e.detail}")

    async def _fetch_tx_details(self, signature: str, address: str) -> Optional[Dict[str, Any]]:
        """Helper to fetch single tx with semaphore."""
        async with self.semaphore:
            try:
                result = await rpc_client.make_request(
                    self.chain, 
                    "getTransaction", 
                    [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
                )
                return self._parse_transaction(result, address)
            except Exception as e:
                print(f"Failed to fetch tx {signature}: {e}")
                return None

    async def get_transaction_history(self, address: str, limit: int = 10) -> List[Dict[str, Any]]:
        sig_params = [address, {"limit": limit}]
        signatures_info = await rpc_client.make_request(self.chain, "getSignaturesForAddress", sig_params)
        
        if not signatures_info:
            return []
            
        signatures = [info["signature"] for info in signatures_info]
        
        # Use semaphore-controlled fetch
        tasks = [self._fetch_tx_details(sig, address) for sig in signatures]
        results = await asyncio.gather(*tasks)
        
        return [tx for tx in results if tx is not None]

    def _parse_transaction(self, tx_data: Dict[str, Any], context_address: str) -> Optional[Dict[str, Any]]:
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
        
        # 'accountKeys' logic handling for jsonParsed
        account_keys_raw = message.get("accountKeys", [])
        account_keys = []
        for k in account_keys_raw:
            if isinstance(k, dict):
                account_keys.append(k.get("pubkey"))
            else:
                account_keys.append(str(k))
        
        try:
            # Simple SOL balance change calculation
            pre_balances = meta.get("preBalances", [])
            post_balances = meta.get("postBalances", [])
            idx = account_keys.index(context_address)
            diff = post_balances[idx] - pre_balances[idx]
            
            amount_decimal = Decimal(abs(diff)) / Decimal(1_000_000_000)
            tx_type = TransactionType.RECEIVE if diff > 0 else TransactionType.SEND
                
            return {
                "tx_hash": tx_hash,
                "chain": self.chain,
                "transaction_type": tx_type,
                "amount": amount_decimal,
                "token_symbol": "SOL", 
                "status": status,
                "timestamp": block_time,
                "block_number": slot,
                "from_address": account_keys[0],
            }
        except (ValueError, IndexError):
            return None

solana_service = SolanaService()