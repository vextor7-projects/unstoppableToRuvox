import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import { Appearance } from 'react-native';

interface UiState {
  theme: 'light' | 'dark';
  isNetworkConnected: boolean;
  toast: {
    message: string;
    type: 'success' | 'error' | 'info';
    visible: boolean;
  };
}

const initialState: UiState = {
  theme: (Appearance.getColorScheme() as 'light' | 'dark') || 'dark',
  isNetworkConnected: true,
  toast: {
    message: '',
    type: 'info',
    visible: false,
  },
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setTheme: (state, action: PayloadAction<'light' | 'dark'>) => {
      state.theme = action.payload;
    },
    setNetworkStatus: (state, action: PayloadAction<boolean>) => {
      state.isNetworkConnected = action.payload;
    },
    showToast: (state, action: PayloadAction<{ message: string; type: 'success' | 'error' | 'info' }>) => {
      state.toast = { ...action.payload, visible: true };
    },
    hideToast: (state) => {
      state.toast.visible = false;
    },
  },
});

export const { setTheme, setNetworkStatus, showToast, hideToast } = uiSlice.actions;
export default uiSlice.reducer;