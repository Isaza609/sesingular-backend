from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PromotionIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    discount_type: str = Field(pattern="^(percent|fixed|volume)$")
    value: int = Field(ge=0)
    min_quantity: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    active: bool = True


class PromotionPatch(PromotionIn):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    discount_type: str | None = Field(default=None, pattern="^(percent|fixed|volume)$")
    value: int | None = Field(default=None, ge=0)


class CouponIn(BaseModel):
    code: str = Field(min_length=1, max_length=60)
    discount_type: str = Field(pattern="^(percent|fixed)$")
    value: int = Field(ge=0)
    max_uses: int | None = Field(default=None, ge=1)
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    active: bool = True


class CouponPatch(CouponIn):
    code: str | None = Field(default=None, min_length=1, max_length=60)
    discount_type: str | None = Field(default=None, pattern="^(percent|fixed)$")
    value: int | None = Field(default=None, ge=0)

