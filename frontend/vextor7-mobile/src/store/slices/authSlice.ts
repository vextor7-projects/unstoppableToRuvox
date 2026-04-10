import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { authApi } from '@/api/services/authApi';
import { userApi } from '@/api/services/userApi';
import { clearTokens, setTokens } from '@/api';

interface User {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  kyc_level: number;
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  isAuthenticated: boolean;
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  accessToken: null,
  isAuthenticated: false,
  status: 'idle',
  error: null,
};

// Thunks
export const loginUser = createAsyncThunk(
  'auth/login',
  async (credentials: any, { rejectWithValue }) => {
    try {
      const response = await authApi.login(credentials);
      // Tokens are set in the API service or interceptor, but if authApi returns them:
      if (response.access_token) {
        await setTokens(response.access_token, response.refresh_token);
      }
      // Fetch user details immediately after login
      const user = await userApi.getMe();
      return { user, token: response.access_token };
    } catch (err: any) {
      return rejectWithValue(err.response?.data?.detail || 'Login failed');
    }
  }
);

export const logoutUser = createAsyncThunk(
  'auth/logout',
  async (_, { dispatch }) => {
    try {
      await authApi.logout();
    } catch (e) {
      // Continue cleanup even if API fails
    } finally {
      await clearTokens();
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    setToken: (state, action: PayloadAction<string>) => {
      state.accessToken = action.payload;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(loginUser.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.isAuthenticated = true;
        state.user = action.payload.user;
        state.accessToken = action.payload.token;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.accessToken = null;
        state.isAuthenticated = false;
        state.status = 'idle';
      });
  },
});

export const { setUser, setToken } = authSlice.actions;
export default authSlice.reducer;