import { api } from '@/api';
import { API_ROUTES } from '@/constants/apiRoutes';

export const securityApi = {
  changePin: async (oldPin: string, newPin: string) => {
    return (await api.post(API_ROUTES.SECURITY.CHANGE_PIN, { old_pin: oldPin, new_pin: newPin })).data;
  },

  enableTotp: async () => {
    return (await api.post(API_ROUTES.SECURITY.TOTP_ENABLE)).data; // Returns secret/qr
  },

  verifyTotp: async (code: string) => {
    return (await api.post(API_ROUTES.SECURITY.TOTP_VERIFY, { code })).data;
  },

  disableTotp: async (code: string) => {
    return (await api.post(API_ROUTES.SECURITY.TOTP_DISABLE, { code })).data;
  },

  submitKyc: async (formData: FormData) => {
    return (await api.post(API_ROUTES.SECURITY.KYC_SUBMIT, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })).data;
  },

  getKycStatus: async () => {
    return (await api.get(API_ROUTES.SECURITY.KYC_STATUS)).data;
  },
};