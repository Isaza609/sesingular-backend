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

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    order = relationship("Order", back_populates="payments")
    payout_account = relationship("PayoutAccount")
