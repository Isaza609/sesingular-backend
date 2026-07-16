from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class Page(BaseModel):
    total: int
    page: int
    page_size: int


class UserOut(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None
    role: str
    active: bool
    created_at: datetime


class UserListOut(Page):
    items: list[UserOut]


class UserPatch(BaseModel):
    active: bool | None = None
    role: Literal["buyer", "seller", "admin"] | None = None


class UserCreate(BaseModel):
    id: str
    email: str
    name: str
    phone: str | None = None
    role: Literal["buyer", "seller", "admin"] = "buyer"


class StoreOut(BaseModel):
    id: str
    slug: str
    name: str
    description: str | None
    logo_url: str | None
    contact_email: str | None
    contact_phone: str | None
    active: bool
    created_at: datetime


class StoreListOut(Page):
    items: list[StoreOut]


class StoreDetailOut(StoreOut):
    members: int
    warehouses: int
    products: int


class StorePatch(BaseModel):
    active: bool


class StoreCreate(BaseModel):
    slug: str
    name: str
    description: str | None = None
    logo_url: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    owner_user_id: str | None = None


class CommissionIn(BaseModel):
    type: Literal["percent", "fixed"] = "percent"
    value: int = Field(ge=0)


class GatewayIn(BaseModel):
    provider: str = "mercadopago"
    sandbox: bool = True
    public_key: str = ""
    webhook_url: str = ""
    # Si llegan vacíos se conserva el valor guardado (no se borra el secreto)
    access_token: str = ""
    webhook_secret: str = ""


class SettingOut(BaseModel):
    key: str
    value: dict
    updated_at: datetime


class SalesReportOut(BaseModel):
    totals: dict
    by_channel: list[dict]
    by_store: list[dict]
    by_day: list[dict]


class InventoryReportOut(BaseModel):
    stores: list[dict]
    warehouses: list[dict]


class ReportedReviewOut(BaseModel):
    report_id: str
    report_reason: str
    report_status: str
    report_created_at: datetime
    review_id: str
    review_status: str
    rating: int
    comment: str | None
    product_name: str
    store_name: str
    reviewer_name: str | None


class ReviewPatch(BaseModel):
    status: Literal["published", "hidden"]


class ReportPatch(BaseModel):
    status: Literal["resolved", "dismissed"]
    resolution_note: str = ""


class DisputeOut(BaseModel):
    id: str
    order_id: str
    reason: str
    description: str | None
    status: str
    resolution_note: str | None
    store_name: str | None
    opener_name: str | None
    created_at: datetime


class DisputePatch(BaseModel):
    status: Literal["open", "in_review", "resolved", "rejected"]
    resolution_note: str = ""
