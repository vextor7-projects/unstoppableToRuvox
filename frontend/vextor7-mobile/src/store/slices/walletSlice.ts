import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { walletApi } from '@/api/services/walletApi';

interface Wallet {
  id: string;
  address: string;
  chain: string;
  balance: number;
}

interface Portfolio {
  id: string;
  name: string;
  wallets: Wallet[];
  totalBalanceUsd: number;
}

interface WalletState {
  portfolios: Portfolio[];
  activePortfolioId: string | null;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: WalletState = {
  portfolios: [],
  activePortfolioId: null,
  status: 'idle',
  error: null,
};

export const fetchPortfolios = createAsyncThunk(
  'wallet/fetchPortfolios',
  async (_, { rejectWithValue }) => {
    try {
      const data = await walletApi.getPortfolios();
      return data;
    } catch (err: any) {
      return rejectWithValue(err.message);
    }
  }
);

const walletSlice = createSlice({
  name: 'wallet',
  initialState,
  reducers: {
    setActivePortfolio: (state, action: PayloadAction<string>) => {
      state.activePortfolioId = action.payload;
    },
    updateBalance: (state, action: PayloadAction<{ portfolioId: string; walletId: string; balance: number }>) => {
      const { portfolioId, walletId, balance } = action.payload;
      const portfolio = state.portfolios.find((p) => p.id === portfolioId);
      if (portfolio) {
        const wallet = portfolio.wallets.find((w) => w.id === walletId);
        if (wallet) {
          wallet.balance = balance;
        }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPortfolios.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchPortfolios.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.portfolios = action.payload;
        if (!state.activePortfolioId && action.payload.length > 0) {
          state.activePortfolioId = action.payload[0].id;
        }
      })
      .addCase(fetchPortfolios.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      });
  },
});

export const { setActivePortfolio, updateBalance } = walletSlice.actions;
export default walletSlice.reducer;