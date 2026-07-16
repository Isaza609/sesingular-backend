from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class WarehouseIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    address_line: str | None = Field(default=None, max_length=300)
    city: str | None = Field(default=None, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    is_default: bool = False
    active: bool = True


class WarehousePatch(WarehouseIn):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class StockPatch(BaseModel):
    warehouse_id: str
    quantity: int = Field(ge=0)
    threshold: int = Field(default=5, ge=0)
    note: str | None = None


class StockOut(BaseModel):
    id: str
    variant_id: str
    sku: str
    product_id: str
    product_name: str
    warehouse_id: str
    warehouse_name: str
    quantity: int
    reserved: int
    available: int
    threshold: int
    updated_at: datetime


class MovementOut(BaseModel):
    id: str
    variant_id: str
    sku: str
    product_name: str
    warehouse_id: str | None
    warehouse_name: str | None
    delta: int
    reason: str
    order_id: str | None
    note: str | None
    created_at: datetime

