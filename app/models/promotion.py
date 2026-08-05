import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SCHEMA


class DiscountType(str, enum.Enum):
    percent = "percent"
    fixed = "fixed"
    volume = "volume"


class PromotionScope(str, enum.Enum):
    store = "store"
    products = "products"


class ChargeType(str, enum.Enum):
    fixed = "fixed"
    percent = "percent"


class Promotion(Base):
    __tablename__ = "promotions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type", schema=SCHEMA, native_enum=True), nullable=False
    )
    # percent: puntos porcentuales; fixed: COP; volume: unidades gratis por min_quantity compradas
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    min_quantity: Mapped[int | None] = mapped_column(Integer)
    pay_quantity: Mapped[int | None] = mapped_column(Integer)
    scope: Mapped[PromotionScope] = mapped_column(
        Enum(PromotionScope, name="promotion_scope", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=PromotionScope.store,
    )
    product_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store")


class Coupon(Base):
    __tablename__ = "coupons"
    __table_args__ = (
        UniqueConstraint("store_id", "code", name="uq_coupons_store_code"),
        {"schema": SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    discount_type: Mapped[DiscountType] = mapped_column(
        Enum(DiscountType, name="discount_type", schema=SCHEMA, native_enum=True), nullable=False
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    max_uses: Mapped[int | None] = mapped_column(Integer)
    used_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scope: Mapped[PromotionScope] = mapped_column(
        Enum(PromotionScope, name="promotion_scope", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=PromotionScope.store,
    )
    product_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store")


class ExtraCharge(Base):
    __tablename__ = "extra_charges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    charge_type: Mapped[ChargeType] = mapped_column(
        Enum(ChargeType, name="charge_type", schema=SCHEMA, native_enum=True), nullable=False
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    scope: Mapped[PromotionScope] = mapped_column(
        Enum(PromotionScope, name="promotion_scope", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=PromotionScope.store,
    )
    product_ids: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store = relationship("Store")
