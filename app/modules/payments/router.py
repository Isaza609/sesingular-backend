from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Order, Payment, PlatformSetting
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.models.user import User
from app.modules.common.permissions import require_buyer
from app.modules.inventory.service import restock_order
from app.modules.orders.router import _order_out

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/orders/{order_id}/intent")
def create_payment_intent(order_id: str, payment_method: str = "card", user: User = Depends(require_buyer), db: Session = Depends(get_db)):
    order = db.get(Order, order_id)
    if order is None or order.buyer_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pedido no encontrado")
    if order.status == OrderStatus.cancelled:
        raise HTTPException(status.HTTP_409_CONFLICT, "El pedido está cancelado")
    payment = db.scalar(select(Payment).where(Payment.order_id == order.id, Payment.status == PaymentStatus.pending).order_by(Payment.created_at.desc()))
    if payment is None:
        payment = Payment(order_id=order.id, provider="pending", method=payment_method, status=PaymentStatus.pending, amount=order.total, seller_amount=order.total, currency="COP")
        db.add(payment)
        db.commit()
        db.refresh(payment)
    gateway = db.get(PlatformSetting, "payment_gateway")
    provider = (gateway.value if gateway else {}).get("provider", "pending")
    if payment.provider == "pending":
        payment.provider = provider
        db.commit()
    return {"payment_id": payment.id, "order_id": order.id, "provider": provider, "status": payment.status.value, "amount": payment.amount, "currency": payment.currency, "checkout_url": None}


@router.post("/webhooks/{provider}")
def payment_webhook(
    provider: str,
    body: dict,
    x_webhook_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    gateway = db.get(PlatformSetting, "payment_gateway")
    configured_secret = (gateway.value if gateway else {}).get("webhook_secret", "")
    if configured_secret and x_webhook_secret != configured_secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma de webhook inválida")
    provider_payment_id = body.get("provider_payment_id") or body.get("data", {}).get("id")
    order_id = body.get("order_id")
    raw_status = str(body.get("status") or body.get("data", {}).get("status") or "pending").lower()
    status_map = {"approved": PaymentStatus.paid.value, "paid": PaymentStatus.paid.value, "rejected": PaymentStatus.rejected.value, "refunded": PaymentStatus.refunded.value, "pending": PaymentStatus.pending.value}
    new_status = status_map.get(raw_status)
    if new_status is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Estado de pago no soportado")
    stmt = select(Payment).where(Payment.provider.in_([provider, "pending"]))
    if provider_payment_id:
        stmt = stmt.where(Payment.provider_payment_id == str(provider_payment_id))
    elif order_id:
        stmt = stmt.where(Payment.order_id == order_id, Payment.status == PaymentStatus.pending)
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Falta identificar el pago")
    payment = db.scalars(stmt.order_by(Payment.created_at.desc())).first()
    if payment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Pago no encontrado")
    payment.provider_payment_id = str(provider_payment_id) if provider_payment_id else payment.provider_payment_id
    payment.status = PaymentStatus(new_status)
    payment.raw_payload = body
    order = payment.order
    if payment.status == PaymentStatus.paid:
        order.status = OrderStatus.confirmed
    elif payment.status in (PaymentStatus.rejected, PaymentStatus.refunded) and order.status not in (OrderStatus.cancelled, OrderStatus.delivered, OrderStatus.returned):
        restock_order(db, order, note="Reposicion por pago rechazado o reembolsado")
        order.status = OrderStatus.cancelled
    db.commit()
    return {"payment_id": payment.id, "order_id": order.id, "status": payment.status.value}
