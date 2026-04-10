// src/utils/crypto.ts
import * as Crypto from 'expo-crypto';

/**
 * Hash a string using SHA-256
 * Useful for checking PINs locally or data integrity
 */
export const hashString = async (text: string): Promise<string> => {
  const digest = await Crypto.digestStringAsync(
    Crypto.CryptoDigestAlgorithm.SHA256,
    text
  );
  return digest;
};

/**
 * Verify a plain text against a hash
 */
export const verifyHash = async (text: string, hash: string): Promise<boolean> => {
  const newHash = await hashString(text);
  return newHash === hash;
};

/**
 * Generates a random UUID (v4)
 * Useful for idempotent keys
 */
export const generateUUID = (): string => {
  return Crypto.randomUUID();
};

/**
 * Generates a random string of specified length
 */
export const generateRandomString = (length: number): string => {
  const charset = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  const randomValues = new Uint8Array(length);
  // Note: getRandomValues is available in RN globally with imports in index.js, 
  // but expo-crypto doesn't expose a sync random bytes easily for strings. 
  // Using Math.random for non-crypto secure string generation (e.g. IDs).
  // For crypto secure, use getRandomValues from polyfill.
  for (let i = 0; i < length; i++) {
    result += charset.charAt(Math.floor(Math.random() * charset.length));
  }
  return result;
};