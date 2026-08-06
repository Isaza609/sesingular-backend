"""Transiciones de estado de pago y bitácora de transacciones (Épica 10).

Toda escritura del estado de un pago debe pasar por aquí para que:
- el estado vigente (`Payment.status`) y el historial (`PaymentEvent`) queden siempre
  sincronizados (HU-PAG-09), y
- los efectos deterministas de cada estado (confirmar pedido, reponer stock) se apliquen
  en un solo lugar y no se dupliquen entre el webhook de pasarela y la revisión manual.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Payment, PaymentEvent
from app.models.order import OrderStatus
from app.models.payment import PaymentStatus
from app.modules.inventory.service import restock_order


def record_event(
    db: Session,
    payment: Payment,
    to_status: PaymentStatus,
    *,
    actor_role: str,
    actor_user_id: str | None = None,
    note: str | None = None,
    received_amount: int | None = None,
    from_status: PaymentStatus | None = None,
) -> PaymentEvent:
    """Agrega un asiento a la bitácora sin tocar el estado vigente del pago."""
    event = PaymentEvent(
        payment_id=payment.id,
        from_status=from_status.value if isinstance(from_status, PaymentStatus) else from_status,
        to_status=to_status.value if isinstance(to_status, PaymentStatus) else str(to_status),
        actor_role=actor_role,
        actor_user_id=actor_user_id,
        note=note,
        received_amount=received_amount,
    )
    db.add(event)
    return event


def record_creation(db: Session, payment: Payment, *, actor_role: str, actor_user_id: str | None = None) -> PaymentEvent:
    """Registra el nacimiento de la transacción (HU-PAG-09: registro al generarse)."""
    return record_event(
        db,
        payment,
        payment.status,
        actor_role=actor_role,
        actor_user_id=actor_user_id,
        from_status=None,
        note="Transacción creada",
    )


def transition(
    db: Session,
    payment: Payment,
    new_status: PaymentStatus,
    *,
    actor_role: str,
    actor_user_id: str | None = None,
    note: str | None = None,
    received_amount: int | None = None,
) -> Payment:
    """Cambia el estado del pago, registra el evento y aplica los efectos del nuevo estado.

    Efectos deterministas por estado destino:
    - `paid`: si el pedido está pendiente, pasa a confirmado.
    - `rejected` / `refunded`: repone el stock reservado y cancela el pedido (idempotente
      gracias a las guardas de `restock_order`).
    - `pending` / `in_review` / `incomplete`: no tocan el stock; la reserva se mantiene.
    """
    old = payment.status
    record_event(
        db,
        payment,
        new_status,
        actor_role=actor_role,
        actor_user_id=actor_user_id,
        note=note,
        received_amount=received_amount,
        from_status=old,
    )
    payment.status = new_status
    order = payment.order

    if new_status == PaymentStatus.paid:
        if order.status == OrderStatus.pending:
            order.status = OrderStatus.confirmed
        # HU-FAC-01: al confirmarse el pago se emite el comprobante de venta (idempotente).
        from app.modules.invoices.service import issue_invoice  # import diferido: evita ciclo

        issue_invoice(db, order)
    elif new_status in (PaymentStatus.rejected, PaymentStatus.refunded):
        if order.status not in (OrderStatus.cancelled, OrderStatus.delivered, OrderStatus.returned):
            restock_order(db, order, note=f"Reposicion por {new_status.value}")
            order.status = OrderStatus.cancelled
            from app.modules.invoices.service import sync_invoice_status  # import diferido

            sync_invoice_status(db, order)

    return payment
