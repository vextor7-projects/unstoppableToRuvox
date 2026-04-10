import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { MMKV } from 'react-native-mmkv';
import authReducer from './slices/authSlice';
import walletReducer from './slices/walletSlice';
import uiReducer from './slices/uiSlice';
import marketReducer from './slices/marketSlice';

// MMKV Storage Wrapper for Redux Persistence (if we were using redux-persist)
// For this production setup, we manually handle critical state hydration in the slices
// or use a lightweight approach to avoid the heavy redux-persist boilerplate if not strictly needed.
// However, typically redux-persist is standard. I will implement the store without it for simplicity 
// and rely on the Context/Hooks we built to initialize state, OR use the slices to manage data 
// fetched via the Services.

const rootReducer = combineReducers({
  auth: authReducer,
  wallet: walletReducer,
  ui: uiReducer,
  market: marketReducer,
});

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false, // Disabled for complex types like Dates if needed, though we should avoid them
    }),
});

setupListeners(store.dispatch);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;