// src/types/navigation.ts
import { NavigatorScreenParams } from '@react-navigation/native';
import { Transaction, Wallet, Token } from './wallet';

export type RootStackParamList = {
  Auth: NavigatorScreenParams<AuthStackParamList>;
  Main: NavigatorScreenParams<MainTabParamList>;
  NotFound: undefined;
};

export type AuthStackParamList = {
  Welcome: undefined;
  Login: undefined;
  Register: undefined;
  PinSetup: { isUpdate?: boolean };
  RecoveryPhrase: { mode: 'create' | 'import' };
  VerifyRecoveryPhrase: { mnemonic: string };
};

export type MainTabParamList = {
  WalletTab: NavigatorScreenParams<WalletStackParamList>;
  SwapTab: NavigatorScreenParams<SwapStackParamList>;
  PayTab: NavigatorScreenParams<PaymentStackParamList>;
  MarketTab: NavigatorScreenParams<MarketStackParamList>;
  SettingsTab: NavigatorScreenParams<SettingsStackParamList>;
};

export type WalletStackParamList = {
  WalletHome: undefined;
  AssetDetails: { token: Token; walletId: string };
  TransactionHistory: { walletId: string };
  Receive: { walletId: string; token?: Token };
  Send: { walletId?: string; preSelectedToken?: Token };
  PortfolioSettings: undefined;
};

export type SendStackParamList = {
  SendAmount: { token: Token; walletId: string };
  SendAddress: { token: Token; walletId: string; amount: string };
  SendConfirm: { 
    token: Token; 
    walletId: string; 
    amount: string; 
    toAddress: string;
    memo?: string;
  };
  SendSuccess: { txHash: string };
};

export type SwapStackParamList = {
  SwapHome: undefined;
  SelectToken: { mode: 'input' | 'output' };
  SwapReview: { quote: any }; // Define specific quote type if available
  SwapSuccess: { txHash: string };
};

export type PaymentStackParamList = {
  PaymentHome: undefined;
  ScanQR: undefined;
  GenerateQR: { amount?: string; token?: Token };
  NFCReader: undefined;
  InvoiceList: undefined;
  InvoiceDetails: { invoiceId: string };
};

export type MarketStackParamList = {
  MarketHome: undefined;
  CoinDetails: { coinId: string };
  PriceAlerts: undefined;
};

export type SettingsStackParamList = {
  SettingsHome: undefined;
  Profile: undefined;
  Security: undefined;
  Preferences: undefined;
  ManageWallets: undefined;
  Support: undefined;
  About: undefined;
};