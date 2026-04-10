export type ChainId = 'solana' | 'ethereum' | 'polygon' | 'base' | 'bitcoin';

export interface ChainConfig {
  id: ChainId;
  name: string;
  symbol: string;
  decimals: number;
  rpcUrl: string;
  explorerUrl: string;
  logo: string; // Placeholder for asset path
  isEVM: boolean;
}

export const CHAINS: Record<ChainId, ChainConfig> = {
  solana: {
    id: 'solana',
    name: 'Solana',
    symbol: 'SOL',
    decimals: 9,
    rpcUrl: process.env.EXPO_PUBLIC_SOLANA_RPC_URL || 'https://api.mainnet-beta.solana.com',
    explorerUrl: 'https://solscan.io',
    logo: 'solana-logo.png',
    isEVM: false,
  },
  ethereum: {
    id: 'ethereum',
    name: 'Ethereum',
    symbol: 'ETH',
    decimals: 18,
    rpcUrl: process.env.EXPO_PUBLIC_ETH_RPC_URL || 'https://mainnet.infura.io/v3/YOUR-KEY',
    explorerUrl: 'https://etherscan.io',
    logo: 'eth-logo.png',
    isEVM: true,
  },
  polygon: {
    id: 'polygon',
    name: 'Polygon',
    symbol: 'MATIC',
    decimals: 18,
    rpcUrl: process.env.EXPO_PUBLIC_POLYGON_RPC_URL || 'https://polygon-rpc.com',
    explorerUrl: 'https://polygonscan.com',
    logo: 'polygon-logo.png',
    isEVM: true,
  },
  base: {
    id: 'base',
    name: 'Base',
    symbol: 'ETH',
    decimals: 18,
    rpcUrl: process.env.EXPO_PUBLIC_BASE_RPC_URL || 'https://mainnet.base.org',
    explorerUrl: 'https://basescan.org',
    logo: 'base-logo.png',
    isEVM: true,
  },
  bitcoin: {
    id: 'bitcoin',
    name: 'Bitcoin',
    symbol: 'BTC',
    decimals: 8,
    rpcUrl: '', // Bitcoin usually uses Indexers (Blockbook/Electrum) rather than standard RPC for mobile
    explorerUrl: 'https://mempool.space',
    logo: 'btc-logo.png',
    isEVM: false,
  },
};

export const SUPPORTED_CHAINS = Object.values(CHAINS);