from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    security,
    wallets,
    transactions,
    exchange,
    payments,
    invoices,
    subscriptions,
    merchants,
    market,
    staking,
    nfts,
    admin
)
from app.api.v1 import websockets

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(security.router, prefix="/security", tags=["Security"])
api_router.include_router(wallets.router, prefix="/wallets", tags=["Wallets"])
api_router.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
api_router.include_router(exchange.router, prefix="/exchange", tags=["Exchange"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
api_router.include_router(merchants.router, prefix="/merchants", tags=["Merchants"])
api_router.include_router(market.router, prefix="/market", tags=["Market Data"])
api_router.include_router(staking.router, prefix="/staking", tags=["Staking & VIP"])
api_router.include_router(nfts.router, prefix="/nfts", tags=["NFTs"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
# WebSockets typically don't have a prefix like /api/v1 inside the router if mounted globally,
# but here we mount them under the API version for consistency.
api_router.include_router(websockets.router, tags=["WebSockets"])