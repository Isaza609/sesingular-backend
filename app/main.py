from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.core.config import get_settings
from app.modules.admin.router import router as admin_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import public_router as catalog_router
from app.modules.catalog.router import seller_router as seller_catalog_router
from app.modules.inventory.router import public_router as inventory_public_router
from app.modules.inventory.router import seller_router as inventory_seller_router
from app.modules.orders.router import buyer_router as buyer_router
from app.modules.orders.router import seller_router as order_seller_router
from app.modules.payments.router import router as payments_router
from app.modules.reviews.router import router as reviews_router
from app.modules.seller.router import router as seller_router

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Marketplace Singular — API Python",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

prefix = f"/{settings.api_prefix.strip('/')}"
app.include_router(health_router, prefix=prefix)
app.include_router(auth_router, prefix=prefix)
app.include_router(admin_router, prefix=prefix)
app.include_router(catalog_router, prefix=prefix)
app.include_router(seller_catalog_router, prefix=prefix)
app.include_router(inventory_public_router, prefix=prefix)
app.include_router(inventory_seller_router, prefix=prefix)
app.include_router(buyer_router, prefix=prefix)
app.include_router(order_seller_router, prefix=prefix)
app.include_router(seller_router, prefix=prefix)
app.include_router(payments_router, prefix=prefix)
app.include_router(reviews_router, prefix=prefix)
