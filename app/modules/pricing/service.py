from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Coupon, ExtraCharge, ProductVariant, Promotion
from app.models.promotion import ChargeType, DiscountType, PromotionScope


@dataclass
class PricedItem:
    cart_item: object | None
    variant: ProductVariant
    quantity: int
    unit_price: int
    regular_unit_price: int
    special_price_applied: bool

    @property
    def product_id(self) -> str:
        return self.variant.product_id

    @property
    def subtotal(self) -> int:
        return self.quantity * self.unit_price

    @property
    def regular_subtotal(self) -> int:
        return self.quantity * self.regular_unit_price


def _aware(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def is_active_window(starts_at: datetime | None, ends_at: datetime | None, *, at: datetime | None = None) -> bool:
    current = at or now_utc()
    starts = _aware(starts_at)
    ends = _aware(ends_at)
    return (starts is None or starts <= current) and (ends is None or ends >= current)


def effective_unit_price(variant: ProductVariant, *, at: datetime | None = None) -> dict:
    current = at or now_utc()
    special_active = (
        variant.special_price is not None
        and is_active_window(variant.special_starts_at, variant.special_ends_at, at=current)
    )
    price = variant.special_price if special_active else variant.price
    return {
        "price": price,
        "regular_price": variant.price,
        "special_price": variant.special_price,
        "special_starts_at": variant.special_starts_at,
        "special_ends_at": variant.special_ends_at,
        "special_price_active": special_active,
    }


def validate_special_price(
    *,
    regular_price: int,
    special_price: int | None,
    special_starts_at: datetime | None,
    special_ends_at: datetime | None,
) -> None:
    if special_price is not None and special_price > regular_price:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "El precio especial no puede superar el precio regular")
    starts = _aware(special_starts_at)
    ends = _aware(special_ends_at)
    if starts is not None and ends is not None and starts > ends:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La fecha de inicio no puede ser posterior a la fecha de fin")


def _in_scope(product_id: str, scope: PromotionScope | str, product_ids: list[str] | None) -> bool:
    scope_value = scope.value if isinstance(scope, PromotionScope) else scope
    if scope_value == PromotionScope.store.value:
        return True
    return product_id in set(product_ids or [])


def _applicable_items(items: list[PricedItem], scope: PromotionScope | str, product_ids: list[str] | None) -> list[PricedItem]:
    return [item for item in items if _in_scope(item.product_id, scope, product_ids)]


def _discount_line(
    *,
    source_type: str,
    source_id: str,
    name: str,
    amount: int,
    code: str | None = None,
) -> dict:
    return {
        "kind": "discount",
        "source_type": source_type,
        "source_id": source_id,
        "name": name,
        "amount": amount,
        "code": code,
    }


def _charge_line(charge: ExtraCharge, amount: int) -> dict:
    return {
        "kind": "extra_charge",
        "source_type": "extra_charge",
        "source_id": charge.id,
        "name": charge.name,
        "amount": amount,
        "charge_type": charge.charge_type.value,
    }


def _promotion_discount(promotion: Promotion, items: list[PricedItem]) -> int:
    applicable = _applicable_items(items, promotion.scope, promotion.product_ids)
    if not applicable:
        return 0
    subtotal = sum(item.subtotal for item in applicable)
    if promotion.discount_type == DiscountType.percent:
        return min(subtotal, subtotal * promotion.value // 100)
    if promotion.discount_type == DiscountType.fixed:
        return min(subtotal, promotion.value)
    quantity = sum(item.quantity for item in applicable)
    if not promotion.min_quantity or promotion.min_quantity <= 0:
        return 0
    if promotion.pay_quantity is not None:
        group_size = promotion.min_quantity
        free_per_group = max(0, promotion.min_quantity - promotion.pay_quantity)
    else:
        free_per_group = max(0, promotion.value)
        group_size = promotion.min_quantity + free_per_group
    if group_size <= 0 or free_per_group <= 0 or quantity < group_size:
        return 0
    lowest_price = min(item.unit_price for item in applicable)
    groups = quantity // group_size
    return min(subtotal, groups * free_per_group * lowest_price)


def _coupon_discount(coupon: Coupon, items: list[PricedItem]) -> int:
    applicable = _applicable_items(items, coupon.scope, coupon.product_ids)
    if not applicable:
        return 0
    subtotal = sum(item.subtotal for item in applicable)
    if coupon.discount_type == DiscountType.percent:
        return min(subtotal, subtotal * coupon.value // 100)
    return min(subtotal, coupon.value)


def priced_items_from_cart_items(cart_items: Iterable[object], *, at: datetime | None = None) -> list[PricedItem]:
    rows: list[PricedItem] = []
    for cart_item in cart_items:
        variant = cart_item.variant
        pricing = effective_unit_price(variant, at=at)
        rows.append(
            PricedItem(
                cart_item=cart_item,
                variant=variant,
                quantity=cart_item.quantity,
                unit_price=pricing["price"],
                regular_unit_price=pricing["regular_price"],
                special_price_applied=pricing["special_price_active"],
            )
        )
    return rows


def calculate_store_pricing(
    *,
    store_id: str,
    priced_items: list[PricedItem],
    db: Session,
    coupon_code: str | None = None,
    shipping_cost: int = 0,
    at: datetime | None = None,
) -> dict:
    current = at or now_utc()
    regular_subtotal = sum(item.regular_subtotal for item in priced_items)
    subtotal = sum(item.subtotal for item in priced_items)
    discounts: list[dict] = []

    promotions = db.scalars(
        select(Promotion)
        .where(Promotion.store_id == store_id, Promotion.active.is_(True))
        .order_by(Promotion.created_at)
    ).all()
    for promotion in promotions:
        if not is_active_window(promotion.starts_at, promotion.ends_at, at=current):
            continue
        amount = _promotion_discount(promotion, priced_items)
        if amount > 0:
            discounts.append(
                _discount_line(
                    source_type="promotion",
                    source_id=promotion.id,
                    name=promotion.name,
                    amount=amount,
                )
            )

    coupon: Coupon | None = None
    if coupon_code:
        coupon = db.scalar(
            select(Coupon).where(
                Coupon.store_id == store_id,
                func.upper(Coupon.code) == coupon_code.upper(),
                Coupon.active.is_(True),
            )
        )
        if coupon is None or not is_active_window(coupon.starts_at, coupon.ends_at, at=current):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cupon invalido o expirado")
        if coupon.max_uses is not None and coupon.used_count >= coupon.max_uses:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cupon invalido o expirado")
        amount = _coupon_discount(coupon, priced_items)
        if amount > 0:
            discounts.append(
                _discount_line(
                    source_type="coupon",
                    source_id=coupon.id,
                    name=f"Cupon {coupon.code}",
                    amount=amount,
                    code=coupon.code,
                )
            )

    discount_total = min(subtotal, sum(line["amount"] for line in discounts))
    subtotal_after_discounts = subtotal - discount_total
    charges: list[dict] = []
    extra_charges = db.scalars(
        select(ExtraCharge)
        .where(ExtraCharge.store_id == store_id, ExtraCharge.active.is_(True))
        .order_by(ExtraCharge.created_at)
    ).all()
    for charge in extra_charges:
        applicable = _applicable_items(priced_items, charge.scope, charge.product_ids)
        if not applicable:
            continue
        amount = charge.value if charge.charge_type == ChargeType.fixed else subtotal_after_discounts * charge.value // 100
        if amount > 0:
            charges.append(_charge_line(charge, amount))

    extra_charge_total = sum(line["amount"] for line in charges)
    return {
        "store_id": store_id,
        "items": [
            {
                "cart_item": item.cart_item,
                "variant": item.variant,
                "variant_id": item.variant.id,
                "product_id": item.variant.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "regular_unit_price": item.regular_unit_price,
                "special_price_applied": item.special_price_applied,
                "line_total": item.subtotal,
            }
            for item in priced_items
        ],
        "regular_subtotal": regular_subtotal,
        "subtotal": subtotal,
        "discounts": discounts,
        "discount": discount_total,
        "subtotal_after_discounts": subtotal_after_discounts,
        "extra_charges": charges,
        "extra_charge_total": extra_charge_total,
        "shipping_cost": shipping_cost,
        "total": subtotal_after_discounts + extra_charge_total + shipping_cost,
        "coupon": coupon,
    }
