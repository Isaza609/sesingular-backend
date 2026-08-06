from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Order, Payment, PlatformSetting
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.models.user import User
from app.modules.common.permissions import require_buyer
from app.modules.payments import service as payment_service
from app.modules.payments.schemas import PaymentIntentOut, WebhookIn, WebhookResultOut

router = APIRouter(prefix="/payments", tags=["payments"])

INTENT_RESPONSES = {
    401: {"description": "Token requerido o invalido."},
    403: {"description": "Requiere rol buyer."},
    404: {"description": "Pedido no encontrado dentro del scope del comprador."},
    409: {"description": "El pedido esta cancelado."},
    422: {"description": "Validacion Pydantic."},
}

WEBHOOK_RESPONSES = {
    400: {"description": "Estado de pago no soportado o falta identificar el pago."},
    401: {"description": "Firma de webhook invalida."},
    404: {"description": "Pago no encontrado."},
    422: {"description": "Validacion Pydantic."},
}


@router.post(
    "/orders/{order_id}/intent",
    response_model=PaymentIntentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear intento de pago por pasarela",
    description=(
        "Rol permitido: buyer. HU-PAG-02. Crea (o reutiliza) el pago pendiente del pedido para "
        "cobrarlo por la pasarela automatizada configurada por la plataforma y registra la "
        "transaccion (HU-PAG-09)."
    ),
    response_description="Intento de pago con proveedor y monto a cobrar.",
    responses=INTENT_RESPONSES,
)
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
        db.flush()
        payment_service.record_creation(db, payment, actor_role="buyer", actor_user_id=user.id)
        db.commit()
        db.refresh(payment)
    gateway = db.get(PlatformSetting, "payment_gateway")
    provider = (gateway.value if gateway else {}).get("provider", "pending")
    if payment.provider == "pending":
        payment.provider = provider
        db.commit()
    return {"payment_id": payment.id, "order_id": order.id, "provider": provider, "status": payment.status.value, "amount": payment.amount, "currency": payment.currency, "checkout_url": None}


@router.post(
    "/webhooks/{provider}",
    response_model=WebhookResultOut,
    status_code=status.HTTP_200_OK,
    summary="Recibir notificacion de la pasarela",
    description=(
        "Endpoint de integracion (pasarela). HU-PAG-02 y HU-PAG-09. Aplica el resultado del pago "
        "notificado por la pasarela: aprobado confirma el pedido; rechazado o reembolsado repone "
        "el stock y cancela el pedido. Valida la firma del webhook contra la configurada por el admin."
    ),
    response_description="Pago afectado con su nuevo estado.",
    responses=WEBHOOK_RESPONSES,
)
def payment_webhook(
    provider: str,
    body: WebhookIn,
    x_webhook_secret: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    gateway = db.get(PlatformSetting, "payment_gateway")
    configured_secret = (gateway.value if gateway else {}).get("webhook_secret", "")
    if configured_secret and x_webhook_secret != configured_secret:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Firma de webhook inválida")
    data = body.data or {}
    provider_payment_id = body.provider_payment_id or data.get("id")
    order_id = body.order_id
    raw_status = str(body.status or data.get("status") or "pending").lower()
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
    payment.raw_payload = body.model_dump()
    payment_service.transition(
        db,
        payment,
        PaymentStatus(new_status),
        actor_role="gateway",
        note=f"Webhook {provider}: {raw_status}",
    )
    db.commit()
    return {"payment_id": payment.id, "order_id": payment.order_id, "status": payment.status.value}
