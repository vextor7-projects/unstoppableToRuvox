// src/utils/blockchain.ts
import { ChainId, CHAINS } from '@/constants/chains';

/**
 * Shortens a wallet address
 * Example: 0x1234...abcd
 */
export const shortenAddress = (address: string, chars = 4): string => {
  if (!address) return '';
  if (address.length < chars * 2 + 2) return address;
  return `${address.slice(0, chars + 2)}...${address.slice(-chars)}`;
};

/**
 * Validates an address format based on chain
 * (Simple regex validation, use libraries for checksums)
 */
export const isValidAddress = (address: string, chainId: ChainId): boolean => {
  switch (chainId) {
    case 'ethereum':
    case 'polygon':
    case 'base':
      return /^0x[a-fA-F0-9]{40}$/.test(address);
    case 'solana':
      // Base58 check (simplified length check)
      return /^[1-9A-HJ-NP-Za-km-z]{32,44}$/.test(address);
    case 'bitcoin':
      // Basic P2PKH, P2SH, Bech32 check
      return /^(1|3|bc1)[a-zA-HJ-NP-Z0-9]{25,62}$/.test(address);
    default:
      return true;
  }
};

/**
 * Generates an explorer link for a transaction
 */
export const getExplorerTxUrl = (chainId: ChainId, txHash: string): string => {
  const chain = CHAINS[chainId];
  if (!chain) return '';
  
  // Handling specific url patterns
  if (chainId === 'solana') {
    return `${chain.explorerUrl}/tx/${txHash}`;
  }
  return `${chain.explorerUrl}/tx/${txHash}`;
};

/**
 * Generates an explorer link for an address
 */
export const getExplorerAddressUrl = (chainId: ChainId, address: string): string => {
  const chain = CHAINS[chainId];
  if (!chain) return '';
  
  if (chainId === 'solana') {
    return `${chain.explorerUrl}/account/${address}`;
  }
  return `${chain.explorerUrl}/address/${address}`;
};

/**
 * Parses a URI (e.g., BIP21 for Bitcoin or EIP-681 for Ethereum)
 * Returns object with address and amount
 */
export const parsePaymentUri = (uri: string): { address: string; amount?: string; chainId?: ChainId } | null => {
  // Basic implementation
  if (uri.startsWith('ethereum:')) {
    const parts = uri.split(':');
    const addressPart = parts[1].split('?')[0]; // simple split
    return { address: addressPart, chainId: 'ethereum' };
  }
  if (uri.startsWith('solana:')) {
    const parts = uri.split(':');
    return { address: parts[1], chainId: 'solana' };
  }
  // Fallback to plain address
  return { address: uri };
};