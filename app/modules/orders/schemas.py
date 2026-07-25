from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class AddressIn(BaseModel):
    label: str | None = Field(default=None, max_length=80)
    recipient_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, max_length=40)
    address_line: str = Field(min_length=1, max_length=300)
    city: str = Field(min_length=1, max_length=120)
    region: str | None = Field(default=None, max_length=120)
    postal_code: str | None = Field(default=None, max_length=20)
    is_default: bool = False


class AddressPatch(AddressIn):
    recipient_name: str | None = Field(default=None, min_length=1, max_length=200)
    address_line: str | None = Field(default=None, min_length=1, max_length=300)
    city: str | None = Field(default=None, min_length=1, max_length=120)


class CartItemIn(BaseModel):
    variant_id: str | None = None
    product_id: str | None = None
    color: str | None = None
    quantity: int = Field(ge=1, le=100)

    @model_validator(mode="after")
    def variant_or_product(self):
        if not self.variant_id and not self.product_id:
            raise ValueError("Debes indicar variant_id o product_id")
        return self


class CartItemPatch(BaseModel):
    quantity: int = Field(ge=1, le=100)


class CheckoutIn(BaseModel):
    address_id: str | None = None
    address: AddressIn | None = None
    coupon_code: str | None = None
    payment_method: str = Field(default="card", min_length=1, max_length=60)
    # Cuenta de cobro elegida cuando el método es manual (transfer | breb)
    payout_account_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def address_required(self):
        if not self.address_id and not self.address:
            raise ValueError("Debes seleccionar o registrar una dirección")
        return self


class OrderStatusPatch(BaseModel):
    status: str = Field(pattern="^(pending|confirmed|preparing|shipped|delivered|cancelled|returned)$")


class WarehouseAssign(BaseModel):
    warehouse_id: str


class OrderItemOut(BaseModel):
    id: str
    variant_id: str | None
    product_name: str
    sku: str | None
    quantity: int
    unit_price: int
    unit_cost: int | None


class OrderOut(BaseModel):
    id: str
    store_id: str
    store_name: str
    buyer_id: str | None
    buyer_name: str | None = None
    warehouse_id: str | None
    address_id: str | None
    channel: str
    status: str
    subtotal: int
    shipping_cost: int
    tax: int
    total: int
    notes: str | None
    created_at: datetime
    items: list[OrderItemOut]
    payments: list[dict]


class CartOut(BaseModel):
    id: str
    items: list[dict]
    subtotal: int
    shipping_cost: int
    tax: int
    total: int


class PosItemIn(BaseModel):
    variant_id: str
    quantity: int = Field(ge=1, le=1000)


class PosOrderIn(BaseModel):
    items: list[PosItemIn] = Field(min_length=1)
    buyer_id: str | None = None
    payment_method: str = Field(default="cash", min_length=1, max_length=60)
    notes: str | None = None

