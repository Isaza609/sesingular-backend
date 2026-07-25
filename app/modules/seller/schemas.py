from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


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


class PayoutAccountIn(BaseModel):
    """Cuenta de cobro manual del vendedor: transferencia bancaria o Bre-B."""

    type: str = Field(default="bank", pattern="^(bank|bre_b)$")
    label: str | None = Field(default=None, max_length=120)
    bank_name: str | None = Field(default=None, max_length=120)
    account_type: str | None = Field(default=None, pattern="^(ahorros|corriente)$")
    account_number: str | None = Field(default=None, max_length=60)
    breb_key: str | None = Field(default=None, max_length=120)
    holder_name: str = Field(min_length=1, max_length=200)
    holder_document: str | None = Field(default=None, max_length=40)
    active: bool = True

    @model_validator(mode="after")
    def check_required_by_type(self):
        if self.type == "bank" and not (self.bank_name and self.account_number):
            raise ValueError("Una cuenta bancaria requiere banco y número de cuenta")
        if self.type == "bre_b" and not self.breb_key:
            raise ValueError("Una cuenta Bre-B requiere la llave")
        return self


class PayoutAccountPatch(BaseModel):
    label: str | None = Field(default=None, max_length=120)
    bank_name: str | None = Field(default=None, max_length=120)
    account_type: str | None = Field(default=None, pattern="^(ahorros|corriente)$")
    account_number: str | None = Field(default=None, max_length=60)
    breb_key: str | None = Field(default=None, max_length=120)
    holder_name: str | None = Field(default=None, min_length=1, max_length=200)
    holder_document: str | None = Field(default=None, max_length=40)
    active: bool | None = None


class PaymentConfirmIn(BaseModel):
    """El vendedor registra el monto realmente recibido al confirmar."""

    received_amount: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)


class PaymentRejectIn(BaseModel):
    note: str = Field(min_length=1, max_length=500)

