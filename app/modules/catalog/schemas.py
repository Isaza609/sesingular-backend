from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class CategoryIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str | None = Field(default=None, max_length=120)
    parent_id: str | None = None
    sort_order: int = Field(default=0, ge=0)
    active: bool = True


class CategoryPatch(CategoryIn):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class VariantIn(BaseModel):
    sku: str = Field(min_length=1, max_length=80)
    name: str | None = Field(default=None, max_length=200)
    color: str | None = Field(default=None, max_length=80)
    size: str | None = Field(default=None, max_length=80)
    price: int = Field(ge=0)
    compare_at: int | None = Field(default=None, ge=0)
    cost: int | None = Field(default=None, ge=0)
    active: bool = True


class VariantPatch(VariantIn):
    sku: str | None = Field(default=None, min_length=1, max_length=80)
    price: int | None = Field(default=None, ge=0)


class ImageIn(BaseModel):
    url: str = Field(min_length=1, max_length=500)
    alt: str | None = Field(default=None, max_length=200)
    sort_order: int = Field(default=0, ge=0)


class ProductIn(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    slug: str | None = Field(default=None, max_length=160)
    short_desc: str | None = Field(default=None, max_length=500)
    description: str | None = None
    status: str = Field(default="draft", pattern="^(draft|active|out_of_stock|discontinued)$")
    category_ids: list[str] = Field(default_factory=list)
    variants: list[VariantIn] = Field(min_length=1)
    images: list[ImageIn] = Field(default_factory=list)


class ProductPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=300)
    slug: str | None = Field(default=None, max_length=160)
    short_desc: str | None = Field(default=None, max_length=500)
    description: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|active|out_of_stock|discontinued)$")
    category_ids: list[str] | None = None


class ProductOut(BaseModel):
    id: str
    store_id: str
    store_name: str
    slug: str
    name: str
    short_desc: str | None
    description: str | None
    status: str
    categories: list[dict]
    variants: list[dict]
    images: list[dict]
    stock: int
    price: int
    compare_at: int | None
    created_at: datetime
    updated_at: datetime


class ProductListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ProductOut]


class StorePublicOut(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    logo_url: str | None


class StoreSettingsIn(BaseModel):
    payment_methods: list[str] = Field(default_factory=lambda: ["card", "pse", "nequi"])
    shipping_flat_cost: int = Field(default=12900, ge=0)
    shipping_free_threshold: int = Field(default=120000, ge=0)
    shipping_zones: list[dict] = Field(default_factory=list)


class StoreListPublicOut(BaseModel):
    items: list[StorePublicOut]


class CategoryOut(BaseModel):
    id: str
    store_id: str
    parent_id: str | None
    slug: str
    name: str
    sort_order: int
    active: bool


class ProductImportRow(BaseModel):
    """Contrato común para una futura carga CSV/XLSX desde el panel vendedor."""

    name: str
    sku: str
    price: int = Field(ge=0)
    cost: int | None = Field(default=None, ge=0)
    stock: int = Field(default=0, ge=0)
    category_slug: str | None = None
