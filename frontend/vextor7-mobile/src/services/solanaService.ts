import { Connection, PublicKey, Transaction, SystemProgram, LAMPORTS_PER_SOL } from '@solana/web3.js';
import { CHAINS } from '@/constants/chains';

const connection = new Connection(CHAINS.solana.rpcUrl, 'confirmed');

export const solanaService = {
  getBalance: async (address: string): Promise<number> => {
    const pubKey = new PublicKey(address);
    const balance = await connection.getBalance(pubKey);
    return balance / LAMPORTS_PER_SOL;
  },

  validateAddress: (address: string): boolean => {
    try {
      new PublicKey(address);
      return true;
    } catch (e) {
      return false;
    }
  },

  createTransferTransaction: async (
    fromAddress: string,
    toAddress: string,
    amount: number
  ) => {
    const fromPubkey = new PublicKey(fromAddress);
    const toPubkey = new PublicKey(toAddress);
    
    const { blockhash } = await connection.getLatestBlockhash();
    
    const transaction = new Transaction().add(
      SystemProgram.transfer({
        fromPubkey,
        toPubkey,
        lamports: amount * LAMPORTS_PER_SOL,
      })
    );
    
    transaction.recentBlockhash = blockhash;
    transaction.feePayer = fromPubkey;
    
    return transaction;
  },

  // Used for signing via Wallet Core later, just prepares the buffer
  serializeTransaction: (transaction: Transaction): Buffer => {
    return transaction.serialize({ requireAllSignatures: false });
  }
};