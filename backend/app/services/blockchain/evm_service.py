


from decimal import Decimal
from typing import List, Dict, Any, Optional

from app.services.blockchain.rpc_client import rpc_client
from app.utils.enums import Chain, TransactionStatus
from app.utils.exceptions import RpcNodeException, TransactionFailedException

class EvmService:
    """
    Service for handling EVM-compatible blockchain interactions.
    """

    def __init__(self):
        self.ERC20_BALANCE_OF = "0x70a08231"
        self.ERC20_DECIMALS = "0x313ce567"
        self.ERC20_SYMBOL = "0x95d89b41"

    async def get_native_balance(self, chain: Chain, address: str) -> Decimal:
        wei_balance = await rpc_client.get_balance(chain, address)
        return Decimal(wei_balance) / Decimal(10**18)

    async def broadcast_transaction(self, chain: Chain, signed_tx_hex: str) -> str:
        """
        Broadcast a signed raw transaction to the EVM network.
        """
        try:
            return await rpc_client.send_raw_transaction(chain, signed_tx_hex)
        except RpcNodeException as e:
            raise TransactionFailedException(f"EVM Broadcast Failed: {e.detail}")

    async def get_token_balance(
        self, chain: Chain, token_address: str, owner_address: str
    ) -> Decimal:
        decimals = await self._get_token_decimals(chain, token_address)
        
        clean_address = owner_address.replace("0x", "")
        padded_address = clean_address.zfill(64)
        data = self.ERC20_BALANCE_OF + padded_address
        
        try:
            result = await rpc_client.make_request(
                chain, 
                "eth_call", 
                [{"to": token_address, "data": data}, "latest"]
            )
            
            if not result or result == "0x":
                return Decimal(0)
                
            raw_balance = int(result, 16)
            return Decimal(raw_balance) / Decimal(10**decimals)
            
        except RpcNodeException:
            return Decimal(0)

    async def get_gas_price(self, chain: Chain) -> Dict[str, int]:
        try:
            block = await rpc_client.make_request(chain, "eth_getBlockByNumber", ["latest", False])
            base_fee = int(block.get("baseFeePerGas", "0x0"), 16)
            
            # Simple heuristic for priority fee
            priority_fee_val = 2_000_000_000 # 2 Gwei default
            
            return {
                "base_fee": base_fee,
                "max_priority_fee": priority_fee_val,
                "is_eip1559": True
            }
        except (RpcNodeException, AttributeError):
            # Legacy fallback
            try:
                gas_price_hex = await rpc_client.make_request(chain, "eth_gasPrice", [])
                return {
                    "gas_price": int(gas_price_hex, 16),
                    "is_eip1559": False
                }
            except Exception:
                # Absolute fallback if RPC fails (prevent crash)
                return {
                    "gas_price": 50_000_000_000, # 50 Gwei
                    "is_eip1559": False
                }

    async def estimate_gas_limit(
        self, chain: Chain, from_addr: str, to_addr: str, data: str = "0x", value_wei: int = 0
    ) -> int:
        tx_obj = {
            "from": from_addr,
            "to": to_addr,
            "data": data,
            "value": hex(value_wei)
        }
        try:
            result = await rpc_client.make_request(chain, "eth_estimateGas", [tx_obj])
            return int(result, 16)
        except RpcNodeException:
            return 21000 # Standard transfer fallback

    
    async def get_transaction_receipt(self, chain: Chain, tx_hash: str) -> Optional[Dict[str, Any]]:
        """
        Check the status of a broadcasted transaction.
        """
        receipt = await rpc_client.make_request(chain, "eth_getTransactionReceipt", [tx_hash])
        
        if not receipt:
            return None
            
        status_int = int(receipt.get("status", "0x0"), 16)
        return {
            "status": TransactionStatus.COMPLETED if status_int == 1 else TransactionStatus.FAILED,
            "block_number": int(receipt.get("blockNumber"), 16),
            "gas_used": int(receipt.get("gasUsed"), 16),
            "logs": receipt.get("logs", [])
        }



    async def _get_token_decimals(self, chain: Chain, token_address: str) -> int:
        try:
            result = await rpc_client.make_request(
                chain, 
                "eth_call", 
                [{"to": token_address, "data": self.ERC20_DECIMALS}, "latest"]
            )
            if result and result != "0x":
                return int(result, 16)
        except Exception:
            pass
        return 18

evm_service = EvmService()