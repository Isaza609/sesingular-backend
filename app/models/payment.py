import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SCHEMA


class PaymentStatus(str, enum.Enum):
    pending = "pending"          # pendiente_pago: aún sin comprobante
    in_review = "in_review"      # comprobante_subido: esperando revisión del vendedor
    incomplete = "incomplete"    # pago_incompleto: monto recibido de menos, carga reabierta (HU-PAG-07)
    paid = "paid"                # pago_confirmado
    rejected = "rejected"        # pago_rechazado
    refunded = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.orders.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(String(40), nullable=False, default="mercadopago")
    provider_payment_id: Mapped[str | None] = mapped_column(String(120), index=True)
    method: Mapped[str | None] = mapped_column(String(60))
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, name="payment_status", schema=SCHEMA, native_enum=True),
        nullable=False,
        default=PaymentStatus.pending,
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    seller_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)

    # --- Pago manual (transferencia bancaria / Bre-B) ---
    payout_account_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.payout_accounts.id", ondelete="SET NULL"), index=True
    )
    receipt_path: Mapped[str | None] = mapped_column(String(500))
    receipt_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    received_amount: Mapped[int | None] = mapped_column(Integer)
    review_note: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by: Mapped[str | None] = mapped_column(String(36))
    # Constancia del acuerdo cuando el comprador pagó de más (HU-PAG-07). La devolución
    # se acuerda por fuera de la plataforma: aquí solo queda el registro del acuerdo.
    agreement_note: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order = relationship("Order", back_populates="payments")
    payout_account = relationship("PayoutAccount")
    events = relationship(
        "PaymentEvent",
        back_populates="payment",
        cascade="all, delete-orphan",
        order_by="PaymentEvent.created_at",
    )


class PaymentEvent(Base):
    """Historial de estados de una transacción (HU-PAG-09).

    Cada transición de estado inserta un evento y conserva el estado anterior, para
    que el administrador pueda conciliar y auditar. `Payment.status` es el estado
    vigente; esta tabla es la bitácora inmutable de cómo llegó ahí.
    """

    __tablename__ = "payment_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id: Mapped[str] = mapped_column(
        String(36), ForeignKey(f"{SCHEMA}.payments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(20))
    to_status: Mapped[str] = mapped_column(String(20), nullable=False)
    actor_role: Mapped[str | None] = mapped_column(String(20))  # buyer | seller | admin | system | gateway
    actor_user_id: Mapped[str | None] = mapped_column(String(36))
    received_amount: Mapped[int | None] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    payment = relationship("Payment", back_populates="events")
