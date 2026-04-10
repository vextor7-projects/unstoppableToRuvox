export const API_ROUTES = {
  AUTH: {
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    REFRESH: '/auth/refresh',
    LOGOUT: '/auth/logout',
  },
  USERS: {
    ME: '/users/me',
    SEARCH: '/users/search',
  },
  SECURITY: {
    CHANGE_PIN: '/security/pin/change',
    TOTP_ENABLE: '/security/totp/enable',
    TOTP_VERIFY: '/security/totp/verify',
    TOTP_DISABLE: '/security/totp/disable',
    TOTP_BACKUP: '/security/totp/backup-codes',
    KYC_SUBMIT: '/security/kyc/submit',
    KYC_STATUS: '/security/kyc/status',
    WHITELIST: '/security/whitelist',
  },
  WALLETS: {
    ROOT: '/wallets', // GET /wallets/me, POST /wallets
    PORTFOLIOS: '/wallets/portfolios',
    BALANCE: (address: string) => `/wallets/${address}/balance`,
    HISTORY: (address: string) => `/wallets/${address}/history`,
  },
  TRANSACTIONS: {
    PREPARE: '/transactions/prepare',
    BROADCAST: '/transactions/broadcast',
    STATUS: (txHash: string) => `/transactions/status/${txHash}`,
    CANCEL: '/transactions/prepare/cancel',
  },
  EXCHANGE: {
    WEBHOOK: '/exchange/webhooks/onramp',
    BALANCE: '/exchange/balance',
    INTERNAL_TRANSFER: '/exchange/internal_transfer',
    DEPOSITS: '/exchange/deposits',
    WITHDRAWALS: '/exchange/withdrawals',
    DEPOSIT_ADDRESS: '/exchange/deposit/address',
  },
  PAYMENTS: {
    SESSION: '/payments/session',
    EXECUTE: (sessionId: string) => `/payments/execute/${sessionId}`,
  },
  INVOICES: {
    ROOT: '/invoices',
    PAY: (invoiceId: string) => `/invoices/${invoiceId}/pay`,
  },
  SUBSCRIPTIONS: {
    ROOT: '/subscriptions',
    PULL_PAYMENTS: '/subscriptions/pull-payments/approve',
  },
  MERCHANTS: {
    REGISTER: '/merchants/register',
    ME: '/merchants/me',
    DASHBOARD: '/merchants/dashboard',
    SETTLEMENT: '/merchants/settlement',
    EMPLOYEES: '/merchants/employees',
  },
  MARKET: {
    COINS: '/market/coins',
    ALERTS: '/market/alerts',
    CHART: (coinId: string) => `/market/coins/${coinId}/chart`,
  },
  STAKING: {
    OPTIONS: '/staking/options',
    STAKE: '/staking/stake',
    UNSTAKE: '/staking/unstake',
    POSITIONS: '/staking/positions',
  },
  NFTS: {
    ROOT: '/nfts',
    PREPARE_TRANSFER: '/nfts/prepare-transfer',
  },
} as const;