import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { marketApi } from '@/api/services/marketApi';

interface MarketState {
  coins: any[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
}

const initialState: MarketState = {
  coins: [],
  status: 'idle',
};

export const fetchMarketData = createAsyncThunk('market/fetchCoins', async (page: number = 1) => {
  const response = await marketApi.getCoins(page);
  return response;
});

const marketSlice = createSlice({
  name: 'market',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchMarketData.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchMarketData.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.coins = action.payload;
      })
      .addCase(fetchMarketData.rejected, (state) => {
        state.status = 'failed';
      });
  },
});

export default marketSlice.reducer;