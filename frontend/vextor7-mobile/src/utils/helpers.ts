// src/utils/helpers.ts
import { format } from 'date-fns';

/**
 * Format a number as currency (e.g., $1,234.56)
 */
export const formatCurrency = (amount: number, currency = 'USD'): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
};

/**
 * Format crypto amount (e.g., 0.0045 BTC)
 * Handles small numbers and large integers gracefully
 */
export const formatCrypto = (amount: number, symbol: string, decimals = 4): string => {
  if (amount === 0) return `0 ${symbol}`;
  
  if (amount < 0.0001) {
    return `< 0.0001 ${symbol}`;
  }

  return `${new Intl.NumberFormat('en-US', {
    maximumFractionDigits: decimals,
  }).format(amount)} ${symbol}`;
};

/**
 * Formats a date string or timestamp
 */
export const formatDate = (date: string | number | Date, formatStr = 'MMM dd, yyyy HH:mm'): string => {
  const d = new Date(date);
  return format(d, formatStr);
};

/**
 * Masks a string (e.g., email or phone)
 * j***@gmail.com
 */
export const maskString = (str: string, visibleStart = 1, visibleEnd = 4): string => {
  if (!str || str.length <= visibleStart + visibleEnd) return str;
  return `${str.slice(0, visibleStart)}****${str.slice(-visibleEnd)}`;
};

/**
 * Sleep function for delays (useful in sagas or retries)
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise((resolve) => setTimeout(resolve, ms));
};

/**
 * Retry a promise n times
 */
export const retryPromise = async <T>(
  fn: () => Promise<T>,
  retries = 3,
  delayMs = 1000
): Promise<T> => {
  try {
    return await fn();
  } catch (error) {
    if (retries <= 1) throw error;
    await sleep(delayMs);
    return retryPromise(fn, retries - 1, delayMs);
  }
};