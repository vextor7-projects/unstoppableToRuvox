import { ethers } from 'ethers';
import { CHAINS, ChainId } from '@/constants/chains';

const getProvider = (chainId: ChainId) => {
  return new ethers.JsonRpcProvider(CHAINS[chainId].rpcUrl);
};

export const evmService = {
  getBalance: async (chainId: ChainId, address: string): Promise<string> => {
    const provider = getProvider(chainId);
    const balance = await provider.getBalance(address);
    return ethers.formatEther(balance);
  },

  validateAddress: (address: string): boolean => {
    return ethers.isAddress(address);
  },

  estimateGas: async (chainId: ChainId, to: string, data: string, from: string, value: string) => {
    const provider = getProvider(chainId);
    const gas = await provider.estimateGas({
      to,
      data,
      from,
      value: ethers.parseEther(value)
    });
    return gas.toString();
  },
  
  // Prepare transaction object for signing
  prepareTransaction: async (chainId: ChainId, from: string, to: string, amount: string) => {
    const provider = getProvider(chainId);
    const nonce = await provider.getTransactionCount(from);
    const feeData = await provider.getFeeData();
    
    return {
      to,
      value: ethers.parseEther(amount),
      nonce,
      gasPrice: feeData.gasPrice,
      chainId: chainId === 'ethereum' ? 1 : chainId === 'polygon' ? 137 : 8453, // Example IDs
    };
  }
};