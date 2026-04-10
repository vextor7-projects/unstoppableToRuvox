// src/types/wallet.ts

export type ChainId = 'solana' | 'ethereum' | 'polygon' | 'base' | 'bitcoin';

export enum TransactionStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  FAILED = 'failed',
}

export enum TransactionType {
  SEND = 'send',
  RECEIVE = 'receive',
  SWAP = 'swap',
  DEPOSIT = 'deposit', // Internal Ledger
  WITHDRAWAL = 'withdrawal', // Internal Ledger
}

export interface Token {
  address: string; // 'native' or contract address
  symbol: string;
  name: string;
  decimals: number;
  logoURI?: string;
  chainId: ChainId;
  priceUsd?: number;
  balance: string; // Raw balance (BigInt string)
  balanceFormatted: number; // Human readable
  valueUsd: number;
}

export interface Wallet {
  id: string;
  portfolioId: string;
  name: string;
  address: string;
  chainId: ChainId;
  publicKey: string;
  isWatchOnly: boolean;
  tokens: Token[];
  totalValueUsd: number;
  createdAt: string;
}

export interface Portfolio {
  id: string;
  name: string;
  isDefault: boolean;
  wallets: Wallet[];
  totalBalanceUsd: number;
  totalBalanceBtc?: number; // Optional reference
  change24hPercentage?: number;
}

export interface Transaction {
  id: string;
  hash: string;
  chainId: ChainId;
  fromAddress: string;
  toAddress: string;
  tokenAddress?: string; // Null for native
  amount: string; // Raw amount
  amountFormatted: number;
  fee?: string;
  symbol: string;
  status: TransactionStatus;
  type: TransactionType;
  timestamp: number; // Unix timestamp
  blockNumber?: number;
  description?: string; // For internal notes or merchant names
}

export interface FeeEstimate {
  gasPrice: string;
  gasLimit: string;
  networkFee: string; // In native currency
  totalUsd: number;
  timeEstimateSeconds: number;
}