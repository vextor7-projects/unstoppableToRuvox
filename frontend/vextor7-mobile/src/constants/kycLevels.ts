export enum KycLevel {
  NONE = 0,
  TIER_1 = 1, // Email/Phone Verification
  TIER_2 = 2, // ID Document
  TIER_3 = 3, // Proof of Address + Liveness
}

export const KYC_LIMITS = {
  [KycLevel.NONE]: {
    dailyWithdrawal: 0,
    dailySwap: 0,
    fiatOnRamp: false,
  },
  [KycLevel.TIER_1]: {
    dailyWithdrawal: 1000, // USD
    dailySwap: 5000,
    fiatOnRamp: true,
  },
  [KycLevel.TIER_2]: {
    dailyWithdrawal: 10000,
    dailySwap: 50000,
    fiatOnRamp: true,
  },
  [KycLevel.TIER_3]: {
    dailyWithdrawal: 100000,
    dailySwap: 1000000,
    fiatOnRamp: true,
  },
} as const;