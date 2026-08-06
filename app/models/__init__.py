"""Importa todos los modelos para que Alembic y metadata los registren."""

from app.models.user import User
from app.models.store import Store, StoreMember, Warehouse
from app.models.catalog import Category, Product, ProductCategory, ProductImage, ProductVariant
from app.models.inventory import InventoryMovement, StockLevel
from app.models.order import Address, CheckoutGroup, Order, OrderAdjustment, OrderItem
from app.models.payment import Payment
from app.models.shipping import Shipment
from app.models.cart import Cart, CartItem
from app.models.promotion import Coupon, ExtraCharge, Promotion
from app.models.review import Dispute, Review, ReviewReport
from app.models.platform import PlatformSetting
from app.models.favorite import Favorite
from app.models.payout import PayoutAccount

__all__ = [
    "User",
    "Store",
    "StoreMember",
    "Warehouse",
    "Category",
    "Product",
    "ProductCategory",
    "ProductImage",
    "ProductVariant",
    "StockLevel",
    "InventoryMovement",
    "Address",
    "CheckoutGroup",
    "Order",
    "OrderAdjustment",
    "OrderItem",
    "Payment",
    "Shipment",
    "Cart",
    "CartItem",
    "Promotion",
    "Coupon",
    "ExtraCharge",
    "Review",
    "ReviewReport",
    "Dispute",
    "PlatformSetting",
    "Favorite",
    "PayoutAccount",
]
