import { NativeModules, Platform } from 'react-native';

const { TrustWalletCore } = NativeModules;

// Interface defining the expected Native Module methods
interface TrustWalletCoreInterface {
  createWallet(strength: number, passphrase: string): Promise<{ mnemonic: string; seed: string }>;
  importWallet(mnemonic: string, passphrase: string): Promise<boolean>;
  deriveAddress(coinType: number, seed: string): Promise<string>;
  signTransaction(coinType: number, seed: string, transaction: string): Promise<string>;
  getPublicKey(coinType: number, seed: string): Promise<string>;
}

// Fallback/Mock for Development if Native Module is missing
const MockTWC: TrustWalletCoreInterface = {
  createWallet: async () => ({ mnemonic: 'mock mock ...', seed: 'mock_seed' }),
  importWallet: async () => true,
  deriveAddress: async () => '0xMockAddress',
  signTransaction: async () => '0xSignedTx',
  getPublicKey: async () => '0xPublicKey',
};

const TWCore = (TrustWalletCore as TrustWalletCoreInterface) || MockTWC;

export const walletCoreService = {
  createMnemonic: async (strength = 128): Promise<string> => {
    const { mnemonic } = await TWCore.createWallet(strength, '');
    return mnemonic;
  },

  getAddress: async (coinType: number, mnemonic: string): Promise<string> => {
    // In a real TWC impl, we'd usually pass the mnemonic or a handle. 
    // This assumes the Native Module handles seed generation internally from mnemonic.
    // For simplicity here, we assume the native method takes mnemonic directly.
    return await TWCore.deriveAddress(coinType, mnemonic); // NOTE: Requires Native Implementation tweak
  },
  
  sign: async (coinType: number, mnemonic: string, txData: string): Promise<string> => {
    return await TWCore.signTransaction(coinType, mnemonic, txData);
  }
};