from decimal import Decimal
from typing import List, Dict, Any

from app.services.blockchain.rpc_client import rpc_client
from app.utils.enums import Chain
from app.utils.exceptions import RpcNodeException, TransactionFailedException

class BitcoinService:
    """
    Service for handling Bitcoin blockchain interactions.
    """

    def __init__(self):
        self.chain = Chain.BITCOIN
        self.BYTES_PER_INPUT = 148
        self.BYTES_PER_OUTPUT = 34
        self.BYTES_BASE = 10

    async def get_balance(self, address: str) -> Decimal:
        utxos = await self.get_utxos(address)
        total_sats = sum(utxo["value_sats"] for utxo in utxos)
        return Decimal(total_sats) / Decimal(100_000_000)

    async def get_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Fetch UTXOs. In Production, this MUST use an Indexer (Blockbook/Electrum).
        This implementation assumes a 'scantxoutset' or equivalent indexer call is available via RPC.
        """
        try:
            # Note: Standard Bitcoin Core 'scantxoutset' is slow. 
            # In a real deployment, replace this method call with a call to your Indexer API.
            # Example: QuickNode offers 'bb_getUtxos'.
            result = await rpc_client.make_request(self.chain, "bb_getUtxos", [address])
            
            utxos = []
            for item in result:
                utxos.append({
                    "tx_hash": item.get("txid"),
                    "vout": item.get("vout"),
                    "value_sats": int(item.get("value")),
                    "script_pub_key": item.get("scriptPubKey"),
                    "confirmations": item.get("confirmations", 0)
                })
            return utxos
        except RpcNodeException:
            return []

    async def broadcast_transaction(self, signed_hex: str) -> str:
        try:
            tx_hash = await rpc_client.send_raw_transaction(self.chain, signed_hex)
            return tx_hash
        except RpcNodeException as e:
            raise TransactionFailedException(f"Bitcoin Broadcast Failed: {e.detail}")

    async def estimate_fee(self, num_inputs: int, num_outputs: int = 2) -> int:
        """
        Estimate mining fee in Satoshis.
        """
        vsize = (num_inputs * self.BYTES_PER_INPUT) + (num_outputs * self.BYTES_PER_OUTPUT) + self.BYTES_BASE
        
        try:
            # estimatesmartfee [blocks]
            fee_response = await rpc_client.make_request(self.chain, "estimatesmartfee", [2])
            
            if fee_response and "feerate" in fee_response:
                btc_per_kvb = Decimal(fee_response["feerate"])
                # Convert BTC/kB to sats/B
                sats_per_byte = int((btc_per_kvb * Decimal(100_000_000)) / 1000)
                sats_per_byte = max(sats_per_byte, 1)
            else:
                # Conservative fallback if node is syncing or empty mempool
                sats_per_byte = 20 
                
        except RpcNodeException:
            sats_per_byte = 20 # Fallback
            
        return int(vsize * sats_per_byte)

bitcoin_service = BitcoinService()