import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SCHEMA


class ProductStatus(str, enum.Enum):
    draft = "draft"
    active = "active"
    out_of_stock = "out_of_stock"
    discontinued = "discontinued"


class Category(Base):
    """Categoría propia de cada tienda (no global)."""

    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("store_id", "slug", name="uq_categories_store_slug"),
        {"schema": SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.categories.id", ondelete="SET NULL"), index=True
    )
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store = relationship("Store", back_populates="categories")
    parent = relationship("Category", remote_side="Category.id")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("store_id", "slug", name="uq_products_store_slug"),
        {"schema": SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    store_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.stores.id", ondelete="CASCADE"), nullable=False, index=True
    )
    slug: Mapped[str] = mapped_column(String(160), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    short_desc: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    # Material / tipo de accesorio mostrado en el catálogo (ej. "Perlas naturales").
    material: Mapped[str | None] = mapped_column(String(120))
    # Etiqueta destacada en la tarjeta: nuevo | destacado | oferta.
    badge: Mapped[str | None] = mapped_column(String(20))
    # Marca "más vendido" para orden y secciones destacadas.
    bestseller: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, name="product_status", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=ProductStatus.draft,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store = relationship("Store", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product")
    images = relationship("ProductImage", back_populates="product")
    category_links = relationship("ProductCategory", back_populates="product")


class ProductCategory(Base):
    __tablename__ = "product_categories"
    __table_args__ = (
        UniqueConstraint("product_id", "category_id", name="uq_product_categories"),
        {"schema": SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.categories.id", ondelete="CASCADE"), nullable=False, index=True
    )

    product = relationship("Product", back_populates="category_links")
    category = relationship("Category")


class ProductVariant(Base):
    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "sku", name="uq_product_variants_product_sku"),
        {"schema": SCHEMA},
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(80), nullable=False)
    name: Mapped[str | None] = mapped_column(String(200))
    color: Mapped[str | None] = mapped_column(String(80))
    size: Mapped[str | None] = mapped_column(String(80))
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    compare_at: Mapped[int | None] = mapped_column(Integer)
    cost: Mapped[int | None] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product = relationship("Product", back_populates="variants")
    stock_levels = relationship("StockLevel", back_populates="variant")
    movements = relationship("InventoryMovement", back_populates="variant")


class ProductImage(Base):
    __tablename__ = "product_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    product_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    alt: Mapped[str | None] = mapped_column(String(200))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="images")
