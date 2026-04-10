// src/utils/storage.ts
import { MMKV } from 'react-native-mmkv';

export const storage = new MMKV({
  id: 'ruvox-storage',
  encryptionKey: 'ruvox-secure-key-v1', // In production, generate this via Keychain/Keystore
});

/**
 * Type-safe wrapper for MMKV storage
 */
export const LocalStorage = {
  /**
   * Set a string, number, or boolean value
   */
  set: (key: string, value: string | number | boolean) => {
    storage.set(key, value);
  },

  /**
   * Set a complex object (automatically stringifies)
   */
  setObject: <T>(key: string, value: T) => {
    try {
      const jsonValue = JSON.stringify(value);
      storage.set(key, jsonValue);
    } catch (e) {
      console.error(`Failed to save object to storage: ${key}`, e);
    }
  },

  /**
   * Get a string value
   */
  getString: (key: string): string | undefined => {
    return storage.getString(key);
  },

  /**
   * Get a number value
   */
  getNumber: (key: string): number => {
    return storage.getNumber(key) || 0;
  },

  /**
   * Get a boolean value
   */
  getBoolean: (key: string): boolean => {
    return storage.getBoolean(key) || false;
  },

  /**
   * Get an object value
   */
  getObject: <T>(key: string): T | null => {
    const json = storage.getString(key);
    if (!json) return null;
    try {
      return JSON.parse(json) as T;
    } catch (e) {
      console.error(`Failed to parse object from storage: ${key}`, e);
      return null;
    }
  },

  /**
   * Delete a specific key
   */
  delete: (key: string) => {
    storage.delete(key);
  },

  /**
   * Clear all storage
   */
  clearAll: () => {
    storage.clearAll();
  },

  /**
   * Check if a key exists
   */
  contains: (key: string): boolean => {
    return storage.contains(key);
  },
};